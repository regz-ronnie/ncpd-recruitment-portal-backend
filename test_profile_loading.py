#!/usr/bin/env python
"""
Test script to verify profile data loading mechanism.
This simulates the user experience of logout/login and data persistence.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncpd_portal.settings')
django.setup()

from apps.users.models import User
from apps.users.serializers import UserProfileSerializer

def test_profile_data_persistence():
    """Test that profile data persists across logout/login"""
    
    print("Testing Profile Data Persistence")
    print("=" * 80)
    
    # Find or create a test user
    try:
        user = User.objects.get(email='test.persistence@example.com')
        print(f"[OK] Found existing test user: {user.email}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='test.persistence@example.com',
            email='test.persistence@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )
        print(f"[OK] Created test user: {user.email}")
    
    # Simulate user filling out profile
    print("\n1. Simulating user profile completion...")
    profile_data = {
        'title': 'Mr',
        'first_name': 'Test',
        'last_name': 'User',
        'gender': 'M',
        'nationality': 'Kenyan',
        'national_id': '12345678',
        'phone_number': '+254712345678',
        'email': 'test.persistence@example.com',
        'county': 'Nairobi',
        'date_of_birth': '1990-01-01',
        'academic_qualifications': [
            {
                'institution': 'University of Nairobi',
                'degree': 'Bachelor of Science',
                'course': 'Computer Science',
                'startDate': '2010-01-01',
                'endDate': '2014-12-31',
                'grade': 'Second Class Honors',
                'country': 'Kenya'
            }
        ],
        'professional_qualifications': [
            {
                'qualification': 'AWS Certified Developer',
                'institution': 'Amazon Web Services',
                'startDate': '2018-01-01',
                'endDate': '2021-01-01',
                'certificateNumber': 'AWS-123456',
                'country': 'USA'
            }
        ],
        'work_experiences_json': [
            {
                'employer': 'Tech Company',
                'jobTitle': 'Software Developer',
                'startDate': '2015-01-01',
                'endDate': '2020-12-31',
                'isCurrent': False,
                'jobDescription': 'Developed web applications'
            }
        ],
        'referees': [
            {
                'refereeName': 'Dr. Jane Smith',
                'organization': 'University of Nairobi',
                'position': 'Senior Lecturer',
                'email': 'jane.smith@uon.ac.ke',
                'phoneNumber': '0723456780',
                'relationship': 'Former Supervisor'
            }
        ],
        'attachments': [
            {
                'documentType': 'CV',
                'fileName': 'test_user_cv.pdf',
                'fileUrl': 'https://example.com/files/test_user_cv.pdf'
            }
        ],
        'declaration1': True,
        'declaration2': True,
        'declaration3': True,
        'declaration_date': '2024-01-01',
        'place_of_declaration': 'Nairobi'
    }
    
    # Update user profile
    serializer = UserProfileSerializer(user, data=profile_data, partial=True)
    if serializer.is_valid():
        serializer.save()
        print("[OK] Profile data saved successfully")
    else:
        print(f"[FAIL] Profile save failed: {serializer.errors}")
        return False
    
    # Simulate logout - user data should remain in database
    print("\n2. Simulating logout (user data should persist in database)...")
    # In a real scenario, this would clear tokens/session
    # But the database should still have the data
    print("[OK] User logged out (database intact)")
    
    # Simulate login - reload user from database
    print("\n3. Simulating login (reloading user from database)...")
    user_from_db = User.objects.get(email='test.persistence@example.com')
    print(f"[OK] User reloaded from database: {user_from_db.email}")
    
    # Check if profile data persisted
    print("\n4. Verifying profile data persistence...")
    
    # Check personal details
    checks = [
        ('First Name', user_from_db.first_name, 'Test'),
        ('Last Name', user_from_db.last_name, 'User'),
        ('Gender', user_from_db.gender, 'M'),
        ('Nationality', user_from_db.nationality, 'Kenyan'),
        ('National ID', user_from_db.national_id, '12345678'),
        ('County', user_from_db.county, 'Nairobi'),
        ('Phone Number', str(user_from_db.phone_number), '+254712345678'),
    ]
    
    all_passed = True
    for field_name, actual, expected in checks:
        if str(actual) == str(expected):
            print(f"  [OK] {field_name}: {actual}")
        else:
            print(f"  [FAIL] {field_name}: expected '{expected}', got '{actual}'")
            all_passed = False
    
    # Check complex fields
    if user_from_db.academic_qualifications and len(user_from_db.academic_qualifications) > 0:
        print(f"  [OK] Academic Qualifications: {len(user_from_db.academic_qualifications)} entries")
    else:
        print(f"  [FAIL] Academic Qualifications: missing or empty")
        all_passed = False
    
    if user_from_db.professional_qualifications and len(user_from_db.professional_qualifications) > 0:
        print(f"  [OK] Professional Qualifications: {len(user_from_db.professional_qualifications)} entries")
    else:
        print(f"  [FAIL] Professional Qualifications: missing or empty")
        all_passed = False
    
    if user_from_db.work_experiences_json and len(user_from_db.work_experiences_json) > 0:
        print(f"  [OK] Work Experience: {len(user_from_db.work_experiences_json)} entries")
    else:
        print(f"  [FAIL] Work Experience: missing or empty")
        all_passed = False
    
    if user_from_db.referees and len(user_from_db.referees) > 0:
        print(f"  [OK] Referees: {len(user_from_db.referees)} entries")
    else:
        print(f"  [FAIL] Referees: missing or empty")
        all_passed = False
    
    if user_from_db.attachments and len(user_from_db.attachments) > 0:
        print(f"  [OK] Attachments: {len(user_from_db.attachments)} entries")
    else:
        print(f"  [FAIL] Attachments: missing or empty")
        all_passed = False
    
    # Check declaration
    if user_from_db.declaration1 and user_from_db.declaration2 and user_from_db.declaration3:
        print(f"  [OK] Declaration: All checkboxes checked")
    else:
        print(f"  [FAIL] Declaration: Missing some checkboxes")
        all_passed = False
    
    # Test serializer representation (frontend format)
    print("\n5. Testing serializer representation (frontend format)...")
    serializer = UserProfileSerializer(user_from_db)
    frontend_data = serializer.data
    
    # Check gender conversion to display name
    if frontend_data.get('gender') == 'Male':
        print(f"  [OK] Gender converted to display name: {frontend_data.get('gender')}")
    else:
        print(f"  [FAIL] Gender conversion failed: got '{frontend_data.get('gender')}'")
        all_passed = False
    
    # Check field name mappings
    if 'firstName' in frontend_data and frontend_data['firstName'] == 'Test':
        print(f"  [OK] Field mapping works: firstName")
    else:
        print(f"  [FAIL] Field mapping failed: firstName")
        all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("SUCCESS: Profile data persists correctly across logout/login!")
        print("The frontend will be able to auto-populate fields from the database.")
        return True
    else:
        print("FAILURE: Some profile data was not persisted correctly.")
        return False

if __name__ == '__main__':
    success = test_profile_data_persistence()
    sys.exit(0 if success else 1)