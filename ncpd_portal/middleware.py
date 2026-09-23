class StripAuthHeaderForAuthEndpointsMiddleware:
    """Middleware to remove Authorization header for public auth endpoints.

    Many authentication backends (e.g., JWT) will raise an authentication
    error if an invalid or expired token is present in the Authorization
    header. For endpoints under /api/auth/ we want the view to run and
    perform its own checks, so strip the header early in the request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = getattr(request, 'path', '') or ''
        if path.startswith('/api/auth/'):
            if 'HTTP_AUTHORIZATION' in request.META:
                del request.META['HTTP_AUTHORIZATION']
        return self.get_response(request)


class XFrameOptionsMiddleware:
    """Middleware to remove X-Frame-Options to allow iframe embedding from frontend."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Remove X-Frame-Options header to allow iframe embedding
        if 'X-Frame-Options' in response:
            del response['X-Frame-Options']
        # Set Content-Security-Policy frame-ancestors to allow framing from frontend
        response['Content-Security-Policy'] = "frame-ancestors 'self' http://192.168.0.84:3000 http://localhost:3000 http://127.0.0.1:3000 http://192.168.0.95:3000"
        return response
