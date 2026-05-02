$ErrorActionPreference = "Stop"

if (Test-Path ".\.venv\Scripts\python.exe") {
    $pythonCmd = ".\.venv\Scripts\python.exe"
} else {
    $pythonCmd = "python"
}

Write-Host "Instalando dependencias..."
& $pythonCmd -m pip install -r requirements.txt

Write-Host "Aplicando migraciones..."
& $pythonCmd .\manage.py migrate

Write-Host "Iniciando servidor en http://127.0.0.1:8000/"
& $pythonCmd .\manage.py runserver
