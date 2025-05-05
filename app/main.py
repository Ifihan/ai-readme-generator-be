from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyCookie

from app.exceptions import add_exception_handlers
from app.config import settings
from app.api.routes import auth  # add readme in nrxt commit
from app.middlewares import SessionMiddleware
from app.db.mongodb import connect_to_mongodb, close_mongodb_connection

cookie_scheme = APIKeyCookie(name=settings.SESSION_COOKIE_NAME)


def create_application() -> FastAPI:
    """Create the FastAPI application instance."""
    application = FastAPI(
        title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    original_openapi = application.openapi

    def custom_openapi():
        if application.openapi_schema:
            return application.openapi_schema

        openapi_schema = original_openapi()

        # Add security components
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}

        openapi_schema["components"]["securitySchemes"] = {
            "session_cookie": {
                "type": "apiKey",
                "in": "cookie",
                "name": settings.SESSION_COOKIE_NAME,
            },
            "bearer_token": {
                "type": "http",
                "scheme": "bearer",
            },
        }

        openapi_schema["security"] = [{"bearer_token": []}, {"session_cookie": []}]

        application.openapi_schema = openapi_schema
        return application.openapi_schema

    application.openapi = custom_openapi

    # Configure CORS
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    application.add_middleware(SessionMiddleware)

    # Include routers
    application.include_router(
        auth.router, prefix=settings.API_V1_STR, tags=["Authentication"]
    )
    # application.include_router(
    #     readme.router, prefix=settings.API_V1_STR, tags=["README Generation"]
    # )

    add_exception_handlers(application)

    # Add MongoDB connection events
    application.add_event_handler("startup", connect_to_mongodb)
    application.add_event_handler("shutdown", close_mongodb_connection)

    return application


app = create_application()


@app.get("/")
async def root():
    """Root for health check."""
    return {"message": f"Welcome to {settings.PROJECT_NAME} API!"}


@app.get("/test")
def test_endpoint():
    """Endpoint for testing purposes."""
    return {"message": "API is working"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
