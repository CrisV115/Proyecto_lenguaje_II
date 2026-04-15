$ErrorActionPreference = "Stop"

Write-Host "Instalando dependencias..."
python -m pip install -r requirements.txt

Write-Host "Aplicando migraciones..."
python .\manage.py migrate

Write-Host "Iniciando servidor en http://127.0.0.1:8000/"
python .\manage.py runserver
