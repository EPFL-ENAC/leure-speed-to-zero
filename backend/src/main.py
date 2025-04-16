from backend.src.api.routes import router
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging
from fastapi.responses import ORJSONResponse
# Set servers in OpenAPI schema
from fastapi.openapi.utils import get_openapi


app = FastAPI(
    openapi_url="/api/v1/docs/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    default_response_class=ORJSONResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="API docs",
        routes=app.routes,
    )
    openapi_schema["servers"] = [{"url": "/api/v1"}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": exc.model.model_dump() if exc.model else None,
        },
    )


# Optional: Serve the main HTML file at the root
@app.get("/")
async def get_index():
    from fastapi.responses import FileResponse
    from pathlib import Path

    index_path = Path(__file__).parent.parent / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Welcome to AddLidar API"}


app.include_router(router)
