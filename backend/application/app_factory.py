from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .deals_api import deals_router
from .health_api import health_router
from .market_api import market_router
from .region_api import region_router
from .services_provider import ServicesProvider


class AppFactory:
    @classmethod
    def make_app(cls, lifespan):
        app = FastAPI(
            title="Eve Trade Helper API",
            description="API pour l'application Eve Trade Helper",
            version="1.0.0",
            lifespan=lifespan,
        )

        cls.configure_cors(app)
        cls.register_routers(app)
        return app

    @staticmethod
    def configure_cors(app):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # En production, spécifier les origines autorisées
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @staticmethod
    def register_routers(app):
        app.include_router(region_router)
        app.include_router(health_router)
        app.include_router(deals_router)
        app.include_router(market_router)

    @classmethod
    def set_services(cls, app, services):
        app.state.services = services
        ServicesProvider.set_services(services)
