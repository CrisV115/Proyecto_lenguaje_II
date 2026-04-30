$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    $pythonCmd = $venvPython
    Write-Host "Usando entorno virtual del proyecto: $pythonCmd"
} else {
    $pythonCmd = "python"
    Write-Host "No se encontro .venv. Se usara Python global."
}

Write-Host "Instalando dependencias..."
& $pythonCmd -m pip install -r (Join-Path $projectRoot "requirements.txt")

Write-Host "Aplicando migraciones..."
& $pythonCmd (Join-Path $projectRoot "manage.py") migrate

Write-Host "Iniciando servidor en http://127.0.0.1:8000/"
& $pythonCmd (Join-Path $projectRoot "manage.py") runserver
