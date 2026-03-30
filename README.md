# Proyecto Prog II

Plataforma académica desarrollada con Django para el curso de Programación II.

## Estado actual

El proyecto ya incluye:

- autenticación con usuario personalizado
- registro y recuperación de contraseña por pregunta de seguridad
- test diagnóstico con corrección automática
- guardado de respuestas individuales
- decisión académica automática
- seguimiento de fases (`test`, `induction`, `leveling`)
- cierre de ruta con certificado básico
- panel administrativo para cargar usuarios, tests, preguntas, respuestas, resultados, seguimiento y certificados

## Tecnologías

- Python 3.13
- Django 6.0.3
- Bootstrap 5
- `python-decouple` para variables de entorno
- `PyMySQL` para dejar preparada la conexión futura a MySQL

## Estructura principal

- `users/`: autenticación, registro y dashboard
- `tests_academic/`: tests, preguntas, respuestas, resultados y respuestas del estudiante
- `tracking/`: seguimiento académico e inducción
- `leveling/`: nivelación
- `certifications/`: emisión y consulta de certificados

## Primer arranque en VS Code

1. Abrir la carpeta del proyecto en VS Code.
2. Verificar que VS Code use `.\.venv\Scripts\python.exe`.
3. Crear el archivo `.env` a partir de `.env.example`.
4. Ejecutar migraciones:

```powershell
.\.venv\Scripts\python.exe .\manage.py migrate
```

5. Crear un superusuario:

```powershell
.\.venv\Scripts\python.exe .\manage.py createsuperuser
```

6. Iniciar el servidor:

```powershell
.\.venv\Scripts\python.exe .\manage.py runserver
```

## Accesos principales

- Inicio: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- Tests: `http://127.0.0.1:8000/tests/`
- Seguimiento: `http://127.0.0.1:8000/tracking/`
- Nivelación: `http://127.0.0.1:8000/leveling/`

## Carga inicial recomendada desde admin

1. Crear usuarios.
2. Crear un `Test`.
3. Crear `Question` asociadas al test.
4. Crear `Answer` para cada pregunta y marcar la correcta.
5. Iniciar sesión con un estudiante y rendir el test.

## Cambio futuro a MySQL

Cuando MySQL Server ya esté instalado y configurado:

1. Editar `.env` y cambiar:

```env
DB_ENGINE=mysql
DB_NAME=proyecto_prog2
DB_USER=proyecto_user
DB_PASSWORD=tu_clave
DB_HOST=127.0.0.1
DB_PORT=3306
```

2. Ejecutar migraciones sobre MySQL:

```powershell
.\.venv\Scripts\python.exe .\manage.py migrate
```

## Pruebas automáticas

Ejecutar la suite:

```powershell
.\.venv\Scripts\python.exe .\manage.py test
```

## Notas

- El proyecto usa SQLite como respaldo local mientras MySQL no esté disponible.
- La carpeta `app/` quedó como legado y ya no forma parte de `INSTALLED_APPS`.
- El siguiente paso natural es enriquecer el contenido real de inducción y nivelación, y añadir reportes académicos.
