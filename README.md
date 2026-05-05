# Proyecto Prog II

Plataforma academica desarrollada con Django para el curso de Programacion II.

## Estado actual

El proyecto incluye:

- autenticacion con usuario personalizado
- registro y recuperacion de contrasena por pregunta de seguridad
- test diagnostico con correccion automatica
- guardado de respuestas individuales
- decision academica automatica
- seguimiento de fases (`test`, `induction`, `leveling`)
- cierre de ruta con certificado basico
- panel administrativo para cargar usuarios, tests, preguntas, respuestas, resultados, seguimiento y certificados

## Tecnologias

- Python 3.11+
- Django 5.2.x
- Bootstrap 5
- `python-decouple` para variables de entorno
- `PyMySQL` para conexion a MySQL
- `cryptography` (opcional, recomendado solo si usas MySQL con `caching_sha2_password`)

## Configuracion rapida (SQLite, recomendado para desarrollo local)

1. Crear `.env` desde `.env.example`.
2. Instalar dependencias de Python:

```powershell
python -m pip install -r requirements.txt
```
3. Ejecutar migraciones:

```powershell
python .\manage.py migrate
```

4. Crear superusuario:

```powershell
python .\manage.py createsuperuser
```

5. Iniciar servidor:

```powershell
python .\manage.py runserver
```

Comando unico (instala, migra y arranca):

```powershell
powershell -ExecutionPolicy Bypass -File .\start_server.ps1
```

## Configuracion MySQL (opcional)

1. Cambiar en `.env`:

```env
DB_ENGINE=mysql
```

2. Crear base y usuario:

```powershell
cmd /c """C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"" -u root -p < mysql_setup.sql"
```

3. Ejecutar migraciones:

```powershell
python .\manage.py migrate
```

Si tu usuario MySQL usa `caching_sha2_password`, instala tambien:

```powershell
python -m pip install cryptography
```

## Variables de entorno

```env
DB_ENGINE=mysql
DB_NAME=proyecto_prog2
DB_USER=proyecto_user
DB_PASSWORD=proyecto123
DB_HOST=127.0.0.1
DB_PORT=3306
DB_CONN_MAX_AGE=60
```

## Pruebas automaticas

```powershell
python .\manage.py test
```

## Despliegue basico en AWS

El proyecto ya queda preparado para un despliegue simple con `gunicorn` en AWS Elastic Beanstalk.

Archivos relevantes:

- `Procfile`: arranque de la app con `gunicorn`
- `requirements.txt`: ahora incluye `gunicorn`
- `proyecto/settings.py`: incluye `STATIC_ROOT`, `CSRF_TRUSTED_ORIGINS` y soporte para proxy HTTPS
- `.ebextensions/01_django.config`: define `WSGIPath`, `collectstatic` y `migrate`

Flujo recomendado en AWS Elastic Beanstalk:

1. Crear un entorno Python para Django.
2. Elegir ambiente `Single instance` para gastar lo minimo.
3. Configurar variables de entorno:

```env
DEBUG=False
SECRET_KEY=tu-clave-segura
ALLOWED_HOSTS=tu-dominio.us-east-1.elasticbeanstalk.com,tu-dominio.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.us-east-1.elasticbeanstalk.com,https://tu-dominio.com
DB_ENGINE=mysql
DB_NAME=nombre_bd
DB_USER=usuario_bd
DB_PASSWORD=clave_bd
DB_HOST=endpoint-rds
DB_PORT=3306
DB_CONN_MAX_AGE=60
```

4. Si vas solo a demo o pruebas pequenas, puedes empezar con SQLite para no pagar RDS.

```env
DEBUG=False
SECRET_KEY=tu-clave-segura
ALLOWED_HOSTS=tu-dominio.us-east-1.elasticbeanstalk.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.us-east-1.elasticbeanstalk.com
DB_ENGINE=sqlite
SQLITE_NAME=dev.sqlite3
```

5. Si usas RDS o una base ya creada, Elastic Beanstalk ejecutara migraciones automaticamente al desplegar.

6. Si despliegas con EB CLI:

```powershell
pip install awsebcli
eb init -p python-3.11 proyecto-lenguaje-ii
eb create proyecto-lenguaje-ii-prod --single
eb deploy
```

7. Abre la aplicacion:

```powershell
eb open
```

8. Cuando termines de probar, elimina el entorno para no seguir consumiendo creditos o cobros:

```powershell
eb terminate proyecto-lenguaje-ii-prod
```

Nota:

- Para produccion real no conviene usar SQLite en AWS si la app tendra varios accesos o reinicios del servidor.
- Elastic Beanstalk no cobra extra por el servicio; cobran los recursos que uses como EC2, RDS, disco y transferencia.
- Si tu cuenta AWS fue creada el 15 de julio de 2025 o despues, el plan gratis nuevo funciona con creditos y vence a los 6 meses o cuando se acaben esos creditos.

## Despliegue recomendado para demo gratis: EC2

Si quieres dejarlo funcional hoy mismo con el menor costo posible, la mejor ruta practica es:

- `EC2`
- `1 sola instancia`
- `t3.micro`
- `Amazon Linux`
- `SQLite`
- `nginx + gunicorn`

Archivos listos para eso:

- [deploy/aws/ec2/gunicorn.service](C:/Users/Joseph/Desktop/edadpromedio/Proyecto_lenguaje_II/deploy/aws/ec2/gunicorn.service)
- [deploy/aws/ec2/nginx-proyecto.conf](C:/Users/Joseph/Desktop/edadpromedio/Proyecto_lenguaje_II/deploy/aws/ec2/nginx-proyecto.conf)
- [deploy/aws/ec2/.env.ec2.example](C:/Users/Joseph/Desktop/edadpromedio/Proyecto_lenguaje_II/deploy/aws/ec2/.env.ec2.example)
- [deploy/aws/ec2/deploy_commands.md](C:/Users/Joseph/Desktop/edadpromedio/Proyecto_lenguaje_II/deploy/aws/ec2/deploy_commands.md)

## Importacion desde archivos planos

Los archivos planos del proyecto ahora viven en la raiz del repositorio:

- [estudiantes.csv](C:/Users/herna/Documents/GitHub/Proyecto_lenguaje_II/estudiantes.csv)
- [profesores.csv](C:/Users/herna/Documents/GitHub/Proyecto_lenguaje_II/profesores.csv)

Pueden estar vacios al inicio. Lo importante es que conserven sus encabezados y el separador `;`.

Encabezados esperados:

- `estudiantes.csv`: `Cedula;Nombre;Apellido;Correo;Carrera`
- `profesores.csv`: `Cedula;Nombre;Apellido;Carrera;Correo`

Despues de ejecutar las migraciones, puedes importar asi:

```powershell
python .\manage.py importar_usuarios_csv
```

Si quieres otra clave temporal para los usuarios cargados:

Comportamiento de la importacion:

- usa la `cedula` como `username` para facilitar el inicio de sesion
- usa la misma `cedula` como clave temporal inicial
- obliga a cambiar la clave en el primer ingreso
- clasifica cada registro como `estudiante` o `profesor`
- actualiza usuarios existentes si ya encuentra la misma `cedula`
- acepta archivos vacios mientras tengan encabezados validos

## Accesos principales

- Inicio: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- Tests: `http://127.0.0.1:8000/tests/`
- Seguimiento: `http://127.0.0.1:8000/tracking/`
- Nivelacion: `http://127.0.0.1:8000/leveling/`
