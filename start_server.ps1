$ErrorActionPreference = "Stop"

Write-Host "Instalando dependencias..."
python -m pip install -r requirements.txt

Write-Host "Aplicando migraciones..."
python .\manage.py migrate

Write-Host "Iniciando servidor en todas las interfaces de red (0.0.0.0:8000)..."
Write-Host "Desde esta computadora: http://127.0.0.1:8000/"
Write-Host "Desde otro dispositivo en la misma red: http://192.168.1.8:8000/"
python .\manage.py runserver 0.0.0.0:8000
