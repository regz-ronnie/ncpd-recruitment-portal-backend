import os
import sys
import traceback

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncpd_portal.settings')

# Django setup
import django
try:
    django.setup()
    print("Django setup successful")
except Exception as e:
    print(f"Django setup failed: {e}")
    traceback.print_exc()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Wrap application with error logging
def application_with_logging(environ, start_response):
    try:
        return application(environ, start_response)
    except Exception as e:
        print(f"ERROR in application: {e}")
        traceback.print_exc()
        # Return error response
        status = '500 Internal Server Error'
        response_body = f'Internal Server Error: {str(e)}'
        response_headers = [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(len(response_body)))
        ]
        start_response(status, response_headers)
        return [response_body.encode('utf-8')]

# Vercel looks for 'app' or 'application' at module level
app = application_with_logging
