# Despliegue EC2

## 1. Paquetes base

```bash
sudo dnf update -y
sudo dnf install -y git nginx python3.11 python3.11-pip
python3.11 -m venv --help
```

## 2. Proyecto

```bash
sudo mkdir -p /var/www
sudo chown ec2-user:ec2-user /var/www
cd /var/www
git clone TU_REPOSITORIO proyecto
cd proyecto
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp deploy/aws/ec2/.env.ec2.example .env
```

## 3. Django

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 4. Gunicorn

```bash
sudo cp deploy/aws/ec2/gunicorn.service /etc/systemd/system/gunicorn-proyecto.service
sudo systemctl daemon-reload
sudo systemctl enable gunicorn-proyecto
sudo systemctl start gunicorn-proyecto
sudo systemctl status gunicorn-proyecto
```

## 5. Nginx

```bash
sudo cp deploy/aws/ec2/nginx-proyecto.conf /etc/nginx/conf.d/proyecto.conf
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

## 6. Firewall en AWS

Abre al menos:

- `22` para SSH
- `80` para HTTP

Si luego activas HTTPS:

- `443` para HTTPS
```
