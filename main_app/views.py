""" views.py: Responsible to process page requests (get/post) """


from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.views.generic import ListView, DetailView, View
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from main_app.forms import NewAddressForm, CouponForm, RefundForm, PaymentOptionForm, UserInfoForm
from mercadopago_payment.models import Payment
from main_app.templatetags import cart_template_tags
from main_app.models import BillingAddress, Category, Item, OrderItem, Order, Coupon, Refund
from main_app.utils import cookieCart
from django.utils.functional import cached_property
from django.db.models import Q
from babel.numbers import format_currency
from mercadopago_payment import utils
from random import randint


class ProfileView(View):
    def get(self, *args, **kwargs):
        """ Rendering user page """

        if self.request.user.is_authenticated:
            user_profile = self.request.user.userprofile # UserProfile.objects.get(user=self.request.user)
            user_info_form = UserInfoForm(instance=user_profile, initial={'email': self.request.user.email})

            context = {'user_form': user_info_form}
            return render(self.request, "profile-user-data.html", context)
        else:
            return redirect('/accounts/login')

    def post(self, *args, **kwargs):
        """ Updating user data """
        if self.request.user.is_authenticated:
            user_profile = self.request.user.userprofile
            user_info_form = UserInfoForm(self.request.POST or None, instance=user_profile)

            if user_info_form.is_valid():
                form = user_info_form.save(commit=False)
                form.user = self.request.user # Set the user object here - because it is not included in the form

                email_message = ""
                if self.request.user.email != user_info_form.cleaned_data.get('email'):
                    new_email = user_info_form.cleaned_data.get('email')
                    self.request.user.userprofile.add_email_address(self.request, new_email)
                    email_message = "Un e-mail fue enviado para confirmar el cambio de e-mail. Verifique su bandeja de entrada o la bandeja de spam si es necesario."

                #self.request.user.save() # save into allauth model
                form.save() #save into UserProfile model
                messages.info(self.request, "Alteraciones realizadas con éxito" + email_message)

            context = {'user_form': user_info_form}
            return render(self.request, "profile-user-data.html", context)
        else:
            return redirect('/accounts/login')


class AddressView(View):
    """ View to add new addresses """
    http_method_names = ['get', 'post', 'put', 'delete']

    @cached_property
    def user_order(self):
        order_id = self.request.session.get("order_id")
        # order = get_object_or_404(Order, id=order_id)
        try:
            order = Order.objects.get(pk=order_id)
        except ObjectDoesNotExist:
            return None
        return order

    def get(self, *args, **kwargs):
        """ Rendering address page """

        if self.request.user.is_authenticated:
            billing_addresses = BillingAddress.objects.filter(user=self.request.user, is_active=True)
            display_form = 'none' if billing_addresses.count() > 0 else 'block'

            try:
                billing_address_default = billing_addresses.get(default=True)
            except ObjectDoesNotExist:
                billing_address_default = None

            billing_addresses = billing_addresses.filter(default=False)

            context = {'new_address_form': NewAddressForm(),
                        'display_form': display_form,
                        'billing_address_default': billing_address_default,
                        'billing_addresses': billing_addresses}

            return render(self.request, "profile-user-address.html", context)
        else:
            return redirect('/accounts/login')

    def post(self, *args, **kwargs):
        """ Adding new addresses """

        if self.request.user.is_authenticated:
            display_newadress_form = 'none'

            if 'crud' in kwargs and kwargs['crud'] == 'create':
                new_address_form = NewAddressForm(self.request.POST or None)

                billing_addresses = BillingAddress.objects.filter(user=self.request.user, is_active=True)
                if billing_addresses.count() > 4:
                    messages.info(self.request, "Máximo de direcciones excedida. Borrar algunas de las existentes antes de ingresar nuevas.")
                    # display_newadress_form = 'none' # Add button is omitted
                
                elif new_address_form.is_valid():
                    default = new_address_form.cleaned_data.get('default')
                    billing_address, created = BillingAddress.objects.get_or_create(user=self.request.user,
                                                                                    address=new_address_form.cleaned_data.get('address'),
                                                                                    number=new_address_form.cleaned_data.get('number'),
                                                                                    zipcode=new_address_form.cleaned_data.get('zipcode'),
                                                                                    city=new_address_form.cleaned_data.get('city'),
                                                                                    state=new_address_form.cleaned_data.get('state'),)
                                                                                    # district=new_address_form.cleaned_data.get('district'))
                    if created or billing_address.is_active == False:
                        billing_address.is_active = True
                        if default:
                            # all others addresses should be set as default False
                            billing_address_default = billing_addresses.filter(default=True)
                            billing_address_default.update(default=False)
                            for addr in billing_address_default:
                                addr.save()
                            # the new address is the only one with default True -
                            # it should be done after the update
                            billing_address.default = True
                            billing_address.save()
                            if self.user_order:
                                self.user_order.billing_address = billing_address
                                self.user_order.save()
                            messages.success(self.request, "Dirección agregada y configurada \
                                                            como nueva dirección de entrega por defecto!")
                        else:
                            billing_address.default = False
                            billing_address.save()
                            messages.success(self.request, "Dirección agregada pero no fué \
                                                            configurado como de entrega por defecto.")
                        new_address_form = NewAddressForm() # clear the form after a successfull submit (save operation done)
                    else:
                        messages.info(self.request, "Dirección ya estaba ingresada! \
                                                    Haga Click para 'Cambiar Dirección'")
                else:
                    display_newadress_form = 'block' # if form is invalid keep the form visible with errors
            elif 'crud' in kwargs and kwargs['crud'] in ['update', 'delete']:
                new_address_form = NewAddressForm()
                try:
                    billing_address_selected = BillingAddress.objects.get(user=self.request.user,
                                                                            address=kwargs['address'],
                                                                            number=kwargs['number'],
                                                                            zipcode=kwargs['zipcode'])
                except ObjectDoesNotExist as e:
                    messages.info(self.request, "Algún error encontrado, esta dirección no fué encontrada!")
                    # return redirect(self.request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found')) # redirect to the same page

                if kwargs['crud'] == 'delete':
                    # check if the address was already used in an order (payment!=None) - if yes then it turns to inactive otherwise it is deleted
                    orders_address = Order.objects.filter(Q(user=self.request.user) & Q(billing_address=billing_address_selected) & ~Q(payment=None))
                    if orders_address.exists():
                        billing_address_selected.is_active = False
                        billing_address_selected.default = False
                        billing_address_selected.save()
                    else:
                        billing_address_selected.delete()
                    messages.info(self.request, "Dirección borrada exitosamente!")

                elif kwargs['crud'] == 'update':
                    try:
                        billing_address_default = BillingAddress.objects.get(user=self.request.user,
                                                                            default=True, is_active=True)
                        billing_address_default.default = False # changing default address
                        billing_address_default.save()
                    except ObjectDoesNotExist:
                        billing_address_default = None
                        # messages.info(self.request, "Algo errado aconteceu, o endereço padrão não foi encontrado!")
                        # return redirect(self.request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found')) # redirect to the same page

                    billing_address_selected.default = True
                    billing_address_selected.save()
                    if self.user_order:
                        self.user_order.billing_address = billing_address_selected
                        self.user_order.save()
                    messages.info(self.request, "Dirección por defecto cambiada exitosamente!")

            try:
                billing_address_default = BillingAddress.objects.get(user=self.request.user, default=True, is_active=True)
            except ObjectDoesNotExist:
                billing_address_default = None
            
            billing_addresses = BillingAddress.objects.filter(user=self.request.user, default=False, is_active=True)
            
            if 'dest' in kwargs and kwargs['dest'] == 'checkout':
                context = {'new_address_form': new_address_form,
                            'billing_address_default': billing_address_default,
                            'billing_addresses': billing_addresses,
                            'payment_form': PaymentOptionForm(),
                            'coupon_form': CouponForm(),
                            'order': self.user_order,
                            'add_coupon_feature': True}
                page_to_return = "checkout-page.html"
            else:
                context = {'new_address_form': new_address_form,
                            'display_form': display_newadress_form,
                            'billing_address_default': billing_address_default,
                            'billing_addresses': billing_addresses}
                page_to_return = "profile-user-address.html"

            return render(self.request, page_to_return, context)
        else:
            return redirect('/accounts/login')


class OrderView(View):
    def get(self, *args, **kwargs):
        """ Rendering user orders page """

        if self.request.user.is_authenticated:
            user_orders = Order.objects.filter(~Q(ref_code=None) & Q(user=self.request.user))

            context = {'user_orders': user_orders}
            return render(self.request, "profile-user-orders.html", context)
        else:
            return redirect('/accounts/login')


class CheckoutView(View):
    """ Checkout page template view """

    @cached_property
    def user_order(self):
        order_id = self.request.session.get("order_id")
        order = get_object_or_404(Order, id=order_id)
        return order

    def get(self, *args, **kwargs):
        """ Rendering checkout page -
            It shows the order options: address, payment etc """
        new_address_form = NewAddressForm()
        payment_form = PaymentOptionForm()
        coupon_form = CouponForm()
        if self.request.user.is_authenticated:
            # before proceed, check if the item was already sold for other client
            for orderitem in self.user_order.items.all():
                if orderitem.item.quantity == 0 or orderitem.quantity > orderitem.item.quantity:
                    messages.warning(self.request, f"Desculpe! No hay más unidades suficientes del item seleccionado {orderitem.item.title}. Ajuste las cantidades o elija otro producto.")
                    return redirect('mycart')
            
            if not self.user_order.items.all():
                messages.warning(self.request, 'Su carrito está vacío.')
                return redirect('mycart')

            try:
                billing_address_default = BillingAddress.objects.get(user=self.request.user, default=True, is_active=True)
            except ObjectDoesNotExist:
                billing_address_default = None

            billing_addresses = BillingAddress.objects.filter(user=self.request.user, default=False, is_active=True)

            context = {'new_address_form': new_address_form,
                        'billing_address_default': billing_address_default,
                        'billing_addresses': billing_addresses,
                        'payment_form': payment_form,
                        'coupon_form': coupon_form,
                        'order': self.user_order,
                        'add_coupon_feature': True}
            return render(self.request, "checkout-page.html", context)
        else:
            return redirect('/accounts/login')

    def post(self, *args, **kwargs):
        """ Processing payment form options """
        if self.request.user.is_authenticated:
            try:
                try:
                    billing_address_default = BillingAddress.objects.get(user=self.request.user,
                                                                        default=True, is_active=True)
                except ObjectDoesNotExist:
                    billing_address_default = None

                if billing_address_default:
                    self.user_order.billing_address = billing_address_default
                    self.user_order.save()
                else:
                    messages.warning(self.request, 'Seleccione una dirección por defecto antes de continuar.')
                    return redirect('checkout')

                payment = Payment.objects.create(order=self.user_order,
                                                            transaction_amount=float(self.user_order.get_total()),
                                                            installments=1,
                                                            payment_method_id="master",
                                                            card_holder="Lionel Messi",
                                                            email="lionel-messi@jogamuito.com.ar",
                                                            doc_type="cpf",
                                                            doc_number="098.007.758-38",
                                                            mercado_pago_id=randint(1000000000, 9999999999),
                                                            mercado_pago_status_detail="approved",
                                                            mercado_pago_status="accredited")

                self.user_order.payment = payment
                self.user_order.ref_code = utils.create_unique_ref_code()
                self.user_order.paid = True
                order_items = self.user_order.items.all()
                order_items.update(finished=True)
                for orderitem in order_items:
                    orderitem.save()
                    product = Item.objects.get(slug=orderitem.item.slug, pk=orderitem.item.pk)
                    if product.quantity >= orderitem.quantity:
                        product.quantity -= orderitem.quantity
                    else:
                        product.quantity = 0
                    product.save()
                self.user_order.save()
                return redirect('/payments/success')

            except ObjectDoesNotExist:
                messages.error(
                    self.request, 'Ops! Surgió un error. Intente nuevamente más tarde.')
                return redirect('checkout')
        else:
            return redirect('/accounts/login')


class HomeView(ListView):
    """ Homepage View """
    paginate_by = 8
    model = Item
    template_name = "home-page.html"

    def get(self, *args, **kwargs):
        """ Rendering home-page by category (slug) """
        if kwargs:
            self.object_list, query_str = self.get_queryset(slug=kwargs['slug'])
        else:
            self.object_list, query_str = self.get_queryset(slug=None)

        self.context = self.get_context_data()
        self.context['query_str'] = query_str

        delete_cookie = False
        # migrating the products from cookie cart to user cart when logged
        if self.request.user.is_authenticated:
            cookieData = cookieCart(self.request)
            user_order_cookie = cookieData['order']
            if user_order_cookie:
                for orderitem in user_order_cookie['items']['all']:
                    item = orderitem['item']
                    quantity = orderitem['quantity']
                    add_item_to_cart(self.request, item['slug'], item['pk'], 'cart', quantity)
                    delete_cookie = True

        response = render(self.request, 'home-page.html', self.context)
        if delete_cookie: response.delete_cookie("cart")
        return response

    def get_queryset(self, slug, *args, **kwargs):
        """ Querying products by category (slug) or 
        query all products if no slug is passed """
        qs = super().get_queryset(*args, **kwargs)
        query_str = ''

        # search filter for products
        if 'search_query' in self.request.GET and self.request.GET['search_query']:
            query_str = self.request.GET['search_query']
            qs = qs.filter(Q(category__title__icontains=query_str) | 
                           Q(category__description__icontains=query_str) | 
                           Q(title__icontains=query_str) | 
                           Q(description__icontains=query_str) | 
                           Q(slug__icontains=query_str))
        elif slug: # category filter
            qs = qs.filter(category__slug=slug)
        else: # no filter was applied
            qs = qs.all()
        return qs, query_str
    
    def get_context_data(self, *args, **kwargs):
        """ Including categories to context """
        context = super(HomeView, self).get_context_data(**kwargs)
        category_list = Category.objects.all()
        context['category_list'] = category_list

        return context


class CartSummaryView(View):
    """ Cart template page """

    def get(self, *args, **kwargs):
        """ Render cart template """
        try:
            delete_cookie = False
            # creating cookie cart for not logged users
            if self.request.user.is_anonymous:
                cookieData = cookieCart(self.request)
                user_order = cookieData['order']
                context = {'user_order': user_order}
            else:
                created = None
                user_order = Order.objects.filter(user=self.request.user,
                                                  payment__mercado_pago_status__in=[None, "null", "rejected"])
                if user_order.exists():
                    user_order = user_order.first()
                else:
                    user_order, created = Order.objects.get_or_create(user=self.request.user,
                                                                        payment__isnull=True)
                cookieData = cookieCart(self.request)
                user_order_cookie = cookieData['order']
                if user_order_cookie:
                    delete_cookie = True
                    for orderitem in user_order_cookie['items']['all']:
                        item = orderitem['item']
                        quantity = orderitem['quantity']
                        add_item_to_cart(self.request, item['slug'], item['pk'], 'cart', quantity)

                if created:
                    user_order.save()
                self.request.session["order_id"] = user_order.id # it will be used to discard repeated payments if the order is already paid

                context = {'user_order': user_order}
            response = render(self.request, 'cart.html', context)
            if delete_cookie: response.delete_cookie("cart")
            return response
        except ObjectDoesNotExist:
            messages.error(
                self.request, 'Ops! Ocurrió un error. Intente nuevamente más tarde.')
            return redirect('/')


class ItemDetailView(DetailView):
    """ Product template page """
    #model = Item
    #template_name = "product.html"

    def get(self, *args, **kwargs):
        item = get_object_or_404(Item, slug=kwargs['slug'], pk=kwargs['pk'])
        if self.request.user.is_authenticated:
            try:
                order_item = OrderItem.objects.get(item=item,
                                                    order__user=self.request.user,
                                                    finished=False)
            except ObjectDoesNotExist as error:
                order_item = None
        else:
            order_item = None
            cookieData = cookieCart(self.request)
            user_order_cookie = cookieData['order']
            if user_order_cookie:
                for order_item_cookie in user_order_cookie['items']['all']:
                    if order_item_cookie['item']['slug'] == kwargs['slug'] and \
                        order_item_cookie['item']['pk'] == kwargs['pk']:
                        order_item = order_item_cookie

        # querying similar products to show
        if item.category:
            related_items = Item.objects.filter(Q(category__title=item.category.title) & ~Q(pk=item.pk) & ~Q(quantity=0))[:5]
        else:
            related_items = Item.objects.filter(Q(category__title="Destacado") & ~Q(pk=item.pk) & ~Q(quantity=0))[:5]
        context = {'product': item, 'orderitem': order_item, 'related_items': related_items}
        response = render(self.request, 'product.html', context)
        return response


def add_item_to_cart(request, slug, pk, dest, quantity=None):
    """ Adding product to the cart """
    item = get_object_or_404(Item, slug=slug, pk=pk)
    if request.user.is_authenticated:
        # getting/creating the orderitem that will be added to cart
        
        # getting the user cart that was not finished (purchased)
        get_user_order = Order.objects.filter(user=request.user, payment=None)
        if get_user_order.exists():  # the user already has a cart
            # each user can have one order unfinished
            user_order = get_user_order[0]
            request.session["order_id"] = user_order.id

            order_item, _ = OrderItem.objects.get_or_create(item=item,
                                                            user_order=user_order)
            # if the selected item has already units on the cart
            if user_order.items.filter(item__slug=item.slug, item__pk=item.pk).exists():
                if quantity: # quantity is passed only when there is a cookiecart to be converted into a logged usercart
                    if int(item.quantity) >= int(quantity) + int(order_item.quantity):
                        order_item.quantity += quantity
                        order_item.save()
                        messages.info(request, order_item.item.title+': Carrito actualizado con nuevas unidades solicitadas.')
                    elif int(item.quantity) > int(order_item.quantity):
                        order_item.quantity = item.quantity
                        order_item.save()
                        messages.info(request, order_item.item.title+': Producto adicionado al carrito pero no había todas las unidades solicitadas.')
                    else:
                        messages.info(request, order_item.item.title+': El producto esta en carrito con todas las unidades disponibles.')
                elif int(item.quantity) > int(order_item.quantity):
                    order_item.quantity += 1
                    order_item.save()
                    messages.info(request, order_item.item.title+': Carrito actualizado con más una unidad.')
                else:
                    messages.info(request, 'El producto esta en carrito con todas las unidades disponibles.')
            else:  # if it is not on the cart so just add
                if quantity: # quantity is passed only when there is a cookiecart to be converted into a logged usercart
                    if int(item.quantity) >= int(quantity):
                        order_item.quantity = quantity # this case the orderitem was created and it started with default quantity=1
                        order_item.save()
                        messages.info(request, order_item.item.title+': Producto agregado al carrito.')
                    else: # otherwise receive all available units on the stock
                        order_item.quantity = item.quantity
                        order_item.save()
                        messages.info(request, order_item.item.title+': Producto adicionado al carrito pero no había todas las unidades solicitadas.')
                else:
                    # order_item.quantity = 1 # default is already 1 - defined on models
                    order_item.save()
                    messages.info(request, order_item.item.title+': Producto adicionado al carrito.')
                user_order.items.add(order_item)
                
        else:  # the user does not have a order yet - creating a cart and adding item
            start_date = timezone.now()
            user_order = Order.objects.create(
                user=request.user, start_date=start_date)
            order_item, _ = OrderItem.objects.get_or_create(item=item,
                                                        user_order=user_order)
            user_order.items.add(order_item)
            messages.info(request, 'Producto adicionado al carrito.')

    if dest=="product":
        return redirect("product", slug=slug, pk=pk)
    elif dest=="cart":
        return redirect("mycart")
    return redirect("/")


def remove_item_from_cart(request, slug, pk, dest, delete=False):
    """ Remove just an unit of the product from the cart
        It is removed only if it has just 1 unit """
    item = get_object_or_404(Item, slug=slug, pk=pk)
    if request.user.is_authenticated:
        # getting the user cart that was not finished (purchased)
        get_user_order = Order.objects.filter(user=request.user,
                                              payment=None)

        if get_user_order.exists():  # the user already has a cart that was not purchased (finished)
            # each user can have maximum of one active order
            user_order = get_user_order[0]

            # if the selected item is already on the cart just increment its quantity
            if user_order.items.filter(item__slug=item.slug, item__pk=item.pk).exists():
                # orderitem that will be removed from cart
                order_item = OrderItem.objects.filter(item=item,
                                                      user_order=user_order,
                                                      finished=False)[0]

                if order_item.quantity == 1 or delete:
                    order_item.delete()
                    messages.info(request, 'Item removido del carrito.')
                else:
                    order_item.quantity -= 1
                    order_item.save()
                    messages.info(
                        request, 'Removido una de las unidades del carrito.')
                if cart_template_tags.count_cart_items(request) == 0:
                    get_user_order.delete()
            else:  # if it is not on the cart so just add
                messages.info(request, 'Este item no estaba en el carrito!')
        else:  # the user does not have a order yet - creating a cart
            messages.info(request, 'Ud.todavía no tiene carrito!')

    if dest=="product":
        return redirect("product", slug=slug, pk=pk)
    elif dest=="cart":
        return redirect("mycart")
    return redirect("/")


def delete_item_from_cart(request, slug, pk, dest=None):
    """ Remove the entire product from the cart
        even if it has more than 1 unit """
    return remove_item_from_cart(request, slug, pk, dest, delete=True)


def get_coupon(code):
    """ Return the coupon if it exists """
    try:
        coupon = Coupon.objects.get(code=code, is_active=True)
        return coupon
    except ObjectDoesNotExist:
        return None


class AddCouponView(View):
    """ Add coupon to the order """

    def post(self, *args, **kwargs):
        """ Receive the code and check if it is valid """
        if self.request.user.is_authenticated:
            coupon_form = CouponForm(self.request.POST or None)
            if coupon_form.is_valid():
                try:
                    code = coupon_form.cleaned_data.get('code')
                    user_order = Order.objects.get(user=self.request.user, payment=None)
                    user_order.coupon = get_coupon(code)
                    if user_order.coupon:
                        user_order.save()
                        messages.success(self.request, "Cupón agregado!")
                    else:
                        messages.info(self.request, "Cupón inválido.")
                except ObjectDoesNotExist:
                    messages.info(self.request, "Ud.todavía no tiene carrito!")
            return redirect('checkout')
        else:
            return redirect('/accounts/login')


class RemoveCouponView(View):
    """ Removing coupon from the order """

    def post(self, *args, **kwargs):
        """ Clear coupon when X button is clicked """
        if self.request.user.is_authenticated:
            try:
                user_order = Order.objects.get(
                    user=self.request.user, payment=None)
                user_order.coupon = None
                user_order.save()
                messages.success(self.request, "Cupón removido!")
                return redirect(kwargs['dest'])
            except ObjectDoesNotExist:
                messages.info(self.request, "Algún error a ocurrido!")
                return redirect(kwargs['dest'])
        else:
            return redirect('/accounts/login')


class RefundView(View):
    """ Treating refund cases """

    def get(self, *args, **kwargs):
        """ Returning refund page """
        if self.request.user.is_authenticated:
            refund_form = RefundForm()
            if 'cod' in kwargs:
                refund_form.initial['ref_code'] = kwargs['cod']
            refund_form.initial['email'] = self.request.user.email
            context = {'refund_form': refund_form}
            return render(self.request, "refund-page.html", context)
        else:
            return redirect('/accounts/login')

    def post(self, *args, **kwargs):
        """ Receiving refund requests """
        if self.request.user.is_authenticated:
            try:
                refund_form = RefundForm(self.request.POST or None)
                if refund_form.is_valid():
                    ref_code = refund_form.cleaned_data.get('ref_code')
                    reason = refund_form.cleaned_data.get('reason')
                    email = refund_form.cleaned_data.get('email')

                    user_order = Order.objects.get(ref_code=ref_code)
                    user_order.refund_requested = True
                    user_order.save()

                    user_refund = Refund()
                    user_refund.user_order = user_order
                    user_refund.reason = reason
                    user_refund.email = email
                    user_refund.save()
                    messages.success(self.request,
                                    "Requisito de devolución enivado. Aguarde resultado del análisis.")
                else:
                    messages.warning(self.request, "Parámetros incorrectos.")
                return redirect('refund-request')
            except ObjectDoesNotExist:
                messages.info(
                    self.request, "Pedido no encontrado en la devolución solicitada.")
                return redirect('refund-request')
        else:
            return redirect('/accounts/login')
