"""
Simple user management script for NCPD recruitment portal
Run with: python manage_users.py
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncpd_portal.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def list_users():
    """List all users in the system"""
    print("\n=== All Users ===")
    print(f"{'Username':<20} {'Email':<30} {'Type':<15} {'Active':<8} {'Staff':<8}")
    print("-" * 80)
    for user in User.objects.all():
        print(f"{user.username:<20} {user.email:<30} {user.user_type:<15} {str(user.is_active):<8} {str(user.is_staff):<8}")
    print(f"\nTotal users: {User.objects.count()}")

def create_user():
    """Create a new user"""
    print("\n=== Create New User ===")
    username = input("Username: ")
    email = input("Email: ")
    password = input("Password: ")
    first_name = input("First Name: ")
    last_name = input("Last Name: ")
    user_type = input("User Type (applicant/hr/admin/manager/panel_member): ")
    
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        user_type=user_type
    )
    
    if user_type == 'admin':
        user.is_staff = True
        user.is_superuser = True
    elif user_type == 'hr':
        user.is_staff = True
    
    user.save()
    print(f"✓ User '{username}' created successfully!")

def update_user():
    """Update an existing user"""
    print("\n=== Update User ===")
    username = input("Enter username to update: ")
    try:
        user = User.objects.get(username=username)
        print(f"Current user: {user.username} ({user.email}) - {user.user_type}")
        
        print("\nUpdate options:")
        print("1. Change password")
        print("2. Update user type")
        print("3. Activate/Deactivate")
        print("4. Make staff/admin")
        print("5. Delete user")
        
        choice = input("Select option (1-5): ")
        
        if choice == '1':
            password = input("New password: ")
            user.set_password(password)
            user.save()
            print("✓ Password updated successfully!")
        elif choice == '2':
            user_type = input("New user type (applicant/hr/admin/manager/panel_member): ")
            user.user_type = user_type
            user.save()
            print("✓ User type updated successfully!")
        elif choice == '3':
            user.is_active = not user.is_active
            user.save()
            print(f"✓ User {'activated' if user.is_active else 'deactivated'} successfully!")
        elif choice == '4':
            is_staff = input("Make staff? (y/n): ").lower() == 'y'
            is_superuser = input("Make superuser? (y/n): ").lower() == 'y'
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()
            print("✓ Permissions updated successfully!")
        elif choice == '5':
            confirm = input(f"Are you sure you want to delete {user.username}? (yes/no): ")
            if confirm.lower() == 'yes':
                user.delete()
                print("✓ User deleted successfully!")
            else:
                print("Deletion cancelled.")
        
    except User.DoesNotExist:
        print("✗ User not found!")

def main():
    while True:
        print("\n=== NCPD User Management ===")
        print("1. List all users")
        print("2. Create new user")
        print("3. Update existing user")
        print("4. Exit")
        
        choice = input("Select option (1-4): ")
        
        if choice == '1':
            list_users()
        elif choice == '2':
            create_user()
        elif choice == '3':
            update_user()
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == '__main__':
    main()