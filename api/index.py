import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncpd_portal.settings')

# Django setup
import django
django.setup()

from django.core.wsgi import get_wsgi_application

# Vercel serverless handler
from vercel_wsgi import handle_wsgi

application = get_wsgi_application()

def handler(event, context):
    return handle_wsgi(application, event, context)
