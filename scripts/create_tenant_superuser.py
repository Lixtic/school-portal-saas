import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.db import connection
from tenants.models import School
from accounts.models import User

def create_tenant_superuser():
    if len(sys.argv) == 5:
        schema_name = sys.argv[1]
        username = sys.argv[2]
        email = sys.argv[3]
        password = sys.argv[4]
    else:
        print("Usage: python scripts/create_tenant_superuser.py <schema_name> <username> <email> <password>")
        print("Falling back to interactive mode...")
        schema_name = input("Enter schema Name (e.g. school1): ")
    
    try:
        tenant = School.objects.get(schema_name=schema_name)
    except School.DoesNotExist:
        print(f"Error: Tenant '{schema_name}' not found.")
        return

    connection.set_tenant(tenant)
    print(f"--- Switched to tenant: {tenant.name} ({schema_name}) ---")
    
    if len(sys.argv) != 5:
        username = input("Enter Username: ")
        email = input("Enter Email: ")
        password = input("Enter Password: ")
    
    if User.objects.filter(username=username).exists():
        print("Error: User already exists.")
        return
        
    user = User.objects.create_superuser(username=username, email=email, password=password)
    # Ensure they are also marked as admin in our custom user_type
    user.user_type = 'admin'
    user.save()
    
    print(f"Success! Superuser '{username}' created for tenant '{schema_name}'.")
    print(f"Login at: http://localhost:8000/{schema_name}/admin/")

if __name__ == '__main__':
    create_tenant_superuser()