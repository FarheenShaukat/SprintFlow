import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_application = get_asgi_application()


async def application(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
    elif scope["type"] == "http" and scope["path"].rstrip("/") == "/mcp":
        from apps.integrations.mcp import mcp_application

        scope = {**scope, "path": "/mcp"}
        await mcp_application(scope, receive, send)
    else:
        await django_application(scope, receive, send)
