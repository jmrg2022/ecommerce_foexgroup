## Introducción

El presente proyecto de ecommerce implica la programación en lenguaje Python con Django
y PostgreSQL para la empresa FoexGroup S.R.L. la cual se dedica a la comercialización de 
herramientas para la construcción, plomería, jardinería y soldadura.

Enlace GitHub: https://github.com/jmrg2022/ecommerce_foexgroup.git

Cabe destacar que está en producción el presente proyecto en el dominio: www.foexgroupsrl.com.ar

## Tecnologías

La implementación está usando Python version 3.7 con las siguentes librerías:

 - django
 - pytest
 - coverage

Otros lenguajes y tecnologías usadas:

 - Front-end: Javascript/HTML/CSS
 - Docker

### Estructura

```shell
.
├── ecommerce                                                             # proyecto django
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── main_app                                                              # aplicación principal django
│   ├── templatetags
│   │   └── cart_template_tags.py
│   ├── tests
│   │   ├── factories.py
│   │   ├── test_cart.py
│   │   ├── test_models.py
│   │   ├── test_views.py
│   │   └── tests.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── utils.py
│   └── views.py
├── media_root                                                            # imagenes de los productos 
├── postgres_data                                                         # base de datos
├── static                                                                # archivo estáticos (css/js/...)
├── templates                                                             # front-end (html)
├── conftest.py                                                           # archivo fixture pytest
├── docker-compose.yaml                                                   # docker-compose
├── docker_entrypoint.sh                                                  # docker Entrypoint
├── Dockerfile                                                            # archivo docker build
├── environment.env                                                       # variables de ambiente (environment)
├── manage.py
├── pytest.ini                                                            # pytest setup
├── README.md
└── requirements.txt                                                      # librerías 
```


## Para correr el proyecto

Para correr el proyecto es necesario tener instalado `docker` and `docker-compose` . Siendo necesario acceder al archivo environment.env.


# Comando para crear y ejecutar
$ docker-compose up

# Solo crear:
$ docker-compose build

# Comando para parar:

$ docker-compose down

A partir de haber realizado un docker-compose up, todos los contenedores estarán habilitados, para acceder a la aplicación, 

abrir en cualquier navegador `http://localhost` (tiene modificado el puerto 8000 por el puerto 80)

Para crear un superusuario:

$ docker exec -ti web createsuperuser

Abrir un navegador e ir `localhost/admin`, para loguearse con el usuario antes creado.

# Contacto: 

Mails: ingjesusgonzalez@yahoo.com.ar - ingjesusmrgonzalez@gmail.com
