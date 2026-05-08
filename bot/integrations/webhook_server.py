import logging
from aiohttp import web

logger = logging.getLogger(__name__)


class WebhookServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_get("/health", self._health_handler)
        self.app.router.add_get("/metrics", self._metrics_handler)

    async def _health_handler(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def _metrics_handler(self, request: web.Request) -> web.Response:
        try:
            import psutil
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            return web.json_response({
                "cpu_percent": cpu,
                "memory_percent": mem.percent,
                "memory_used_mb": round(mem.used / 1024 / 1024, 1),
            })
        except ImportError:
            return web.json_response({"error": "psutil not available"}, status=503)

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info("Webhook server started on %s:%s", self.host, self.port)
        return runner
