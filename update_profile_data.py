import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncpd_portal.settings')
django.setup()

from apps.users.models import User

# Get the user
user = User.objects.get(id=1)

print("Current user data:")
print(f"Academic qualifications: {user.academic_qualifications}")
print(f"Work experiences JSON: {user.work_experiences_json}")
print(f"Referees: {user.referees}")
print(f"Attachments: {user.attachments}")
print(f"Declaration fields: d1={user.declaration1}, d2={user.declaration2}, d3={user.declaration3}, date={user.declaration_date}, place={user.place_of_declaration}")

# Update with sample data if missing
if not user.academic_qualifications:
    user.academic_qualifications = [
        {
            'year': 2020,
            'degree': 'Bachelor of Computer Science',
            'institution': 'University of Nairobi',
            'field_of_study': 'Computer Science'
        }
    ]
    print("Added academic qualifications")

if not user.work_experiences_json:
    user.work_experiences_json = [
        {
            'title': 'Software Developer',
            'company': 'Tech Company',
            'start_date': '2021-01-01',
            'end_date': '2023-12-31',
            'description': 'Developed web applications'
        }
    ]
    print("Added work experiences")

# Always update to ensure complete data
user.referees = [
    {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '123456789',
        'position': 'Manager',
        'organization': 'Previous Company'
    },
    {
        'name': 'Jane Smith',
        'email': 'jane@example.com',
        'phone': '987654321',
        'position': 'Supervisor',
        'organization': 'Previous Company'
    },
    {
        'name': 'Robert Johnson',
        'email': 'robert@example.com',
        'phone': '456789123',
        'position': 'Colleague',
        'organization': 'Previous Company'
    }
]
print("Updated referees to 3 complete entries")

# Always update to ensure complete data
user.attachments = [
    {
        'type': 'CV',
        'filename': 'cv.pdf',
        'upload_date': '2024-01-01'
    },
    {
        'type': 'National ID',
        'filename': 'national_id.pdf',
        'upload_date': '2024-01-01'
    },
    {
        'type': 'Degree Certificate',
        'filename': 'degree_certificate.pdf',
        'upload_date': '2024-01-01'
    }
]
print("Updated attachments to 3 complete entries")

# Update declaration fields
user.declaration1 = True
user.declaration2 = True
user.declaration3 = True
user.declaration_date = '2024-01-01'
user.place_of_declaration = 'Nairobi'
print("Updated declaration fields")

user.save()

print("\nUpdated user data:")
print(f"Academic qualifications: {user.academic_qualifications}")
print(f"Work experiences JSON: {user.work_experiences_json}")
print(f"Referees: {user.referees}")
print(f"Attachments: {user.attachments}")
print(f"Declaration fields: d1={user.declaration1}, d2={user.declaration2}, d3={user.declaration3}, date={user.declaration_date}, place={user.place_of_declaration}")
