import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncpd_portal.settings')

# Django setup
import django
django.setup()

# Debug email configuration
print(f"VERCEL environment: {os.getenv('VERCEL')}")
print(f"EMAIL_BACKEND: {os.getenv('EMAIL_BACKEND', 'not set')}")
print(f"RESEND_API_KEY set: {bool(os.getenv('RESEND_API_KEY'))}")
print(f"RESEND_FROM_EMAIL: {os.getenv('RESEND_FROM_EMAIL', 'not set')}")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Vercel looks for 'app' or 'application' at module level
app = application
