import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncpd_portal.settings')

# Django setup
import django
django.setup()

from django.core.wsgi import get_wsgi_application

# Get the WSGI application
application = get_wsgi_application()

# Vercel serverless handler
def handler(event, context):
    """
    Vercel serverless function handler for Django
    """
    from io import BytesIO
    
    # Parse event
    method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    headers = event.get('headers', {})
    body = event.get('body', '')
    query = event.get('queryStringParameters', {})
    
    # Build Django WSGI environ
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': '&'.join(f"{k}={v}" for k, v in query.items()),
        'CONTENT_TYPE': headers.get('content-type', ''),
        'CONTENT_LENGTH': str(len(body)) if body else '0',
        'SERVER_NAME': 'vercel',
        'SERVER_PORT': '443',
        'wsgi.url_scheme': 'https',
        'wsgi.input': BytesIO(body.encode() if body else b''),
        'wsgi.errors': sys.stderr,
        'wsgi.version': (1, 0),
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Add headers to environ
    for key, value in headers.items():
        environ[f'HTTP_{key.upper().replace("-", "_")}'] = value
    
    # Process request
    response_data = {}
    
    def start_response(status, response_headers):
        response_data['status'] = status
        response_data['headers'] = dict(response_headers)
    
    result = application(environ, start_response)
    body_content = b''.join(result)
    
    return {
        'statusCode': int(response_data['status'].split()[0]),
        'headers': response_data['headers'],
        'body': body_content.decode('utf-8'),
    }
