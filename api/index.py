import base64
import os
import sys
import traceback

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncpd_portal.settings')

# Django setup
try:
    import django
    django.setup()
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    DJANGO_READY = True
except Exception as e:
    print(f"Django setup failed: {e}")
    traceback.print_exc()
    DJANGO_READY = False

def _serialize_vercel_body(body_bytes):
    """Return a Vercel-safe string body and whether it was Base64-encoded."""
    try:
        return body_bytes.decode('utf-8'), False
    except UnicodeDecodeError:
        return base64.b64encode(body_bytes).decode('utf-8'), True


# Vercel serverless handler
def handler(event, context):
    """
    Vercel serverless function handler for Django
    """
    from io import BytesIO

    if not DJANGO_READY:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': '{"error": "Django setup failed"}',
            'isBase64Encoded': False,
        }

    try:
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        headers = event.get('headers', {})
        raw_body = event.get('body', '')
        if isinstance(raw_body, bytes):
            raw_body = raw_body.decode('utf-8', errors='replace')
        body = raw_body if raw_body is not None else ''
        query = event.get('queryStringParameters', {}) or {}

        host = headers.get('host', headers.get('x-forwarded-host', 'localhost'))
        server_name = host.split(':')[0]

        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': path,
            'QUERY_STRING': '&'.join(f"{k}={v}" for k, v in query.items()),
            'CONTENT_TYPE': headers.get('content-type', ''),
            'CONTENT_LENGTH': str(len(body)) if body else '0',
            'SERVER_NAME': server_name,
            'SERVER_PORT': headers.get('x-forwarded-port', '443'),
            'wsgi.url_scheme': headers.get('x-forwarded-proto', 'https'),
            'wsgi.input': BytesIO(body.encode('utf-8') if body else b''),
            'wsgi.errors': sys.stderr,
            'wsgi.version': (1, 0),
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False,
        }

        for key, value in headers.items():
            environ[f'HTTP_{key.upper().replace("-", "_")}'] = value

        response_data = {}

        def start_response(status, response_headers):
            response_data['status'] = status
            response_data['headers'] = dict(response_headers)

        result = application(environ, start_response)
        body_content = b''.join(result)
        response_body, is_base64 = _serialize_vercel_body(body_content)

        return {
            'statusCode': int(response_data['status'].split()[0]),
            'headers': {str(k): str(v) for k, v in response_data['headers'].items()},
            'body': response_body,
            'isBase64Encoded': is_base64,
        }
    except Exception as e:
        print(f"Handler error: {e}")
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': f'{{"error": "{str(e)}"}}',
            'isBase64Encoded': False,
        }


# Vercel looks for an app or handler at module scope.
app = handler
