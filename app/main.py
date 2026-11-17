from fastapi import FastAPI

from app.adapters.inbound.http.error_handlers import register_error_handlers
from app.adapters.inbound.http.routes.health import router as health_router
from app.adapters.inbound.http.routes.weather import router as weather_router


def create_app() -> FastAPI:
    app = FastAPI(title="Weather API", version="0.1.0")
    app.include_router(weather_router)
    app.include_router(health_router)
    register_error_handlers(app)
    return app


app = create_app()
