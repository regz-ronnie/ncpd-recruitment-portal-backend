"""
ASGI config for ncpd_portal project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncpd_portal.settings')

application = get_asgi_application()

try:
    from channels.auth import AuthMiddlewareStack
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.security.websocket import AllowedHostsOriginValidator

    try:
        import apps.workflow.routing as workflow_routing
    except ModuleNotFoundError:
        workflow_routing = None

    if workflow_routing is not None and hasattr(workflow_routing, 'websocket_urlpatterns'):
        application = ProtocolTypeRouter({
            "http": application,
            "websocket": AllowedHostsOriginValidator(
                AuthMiddlewareStack(
                    URLRouter(workflow_routing.websocket_urlpatterns)
                )
            ),
        })
    else:
        application = application
except ImportError:
    # Some deployments (such as Vercel serverless builds) do not need WebSockets.
    # Keep ASGI compatible without channels installed.
    application = application
