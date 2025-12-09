import os
import django
from django.contrib.auth import get_user_model
from django.core.management import call_command

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

# Obtiene datos del superusuario de las variables de entorno de Render
USERNAME = os.environ.get('DJANGO_SUPERUSER_USERNAME')
EMAIL = os.environ.get('DJANGO_SUPERUSER_EMAIL')
PASSWORD = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not User.objects.filter(username=USERNAME).exists():
    print(f"Creando superusuario {USERNAME}...")
    User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
    print("¡Superusuario creado con éxito!")
else:
    print(f"El superusuario {USERNAME} ya existe. Saltando la creación.")