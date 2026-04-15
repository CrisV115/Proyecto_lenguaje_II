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

## Accesos principales

- Inicio: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- Tests: `http://127.0.0.1:8000/tests/`
- Seguimiento: `http://127.0.0.1:8000/tracking/`
- Nivelacion: `http://127.0.0.1:8000/leveling/`
