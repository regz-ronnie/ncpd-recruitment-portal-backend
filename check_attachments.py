import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncpd_portal.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Get the user
user = User.objects.get(email='rody@gmail.com')

print(f"User: {user.email}")
print(f"User ID: {user.id}")
print(f"Attachments: {user.attachments}")
print(f"Number of attachments: {len(user.attachments) if user.attachments else 0}")

if user.attachments:
    print("\n--- Attachment Details ---")
    for i, attachment in enumerate(user.attachments, 1):
        print(f"\nAttachment {i}:")
        print(f"  Document Type: {attachment.get('documentType')}")
        print(f"  File Name: {attachment.get('fileName')}")
        print(f"  Date Uploaded: {attachment.get('dateUploaded')}")
        print(f"  File Data: {attachment.get('file')}")
