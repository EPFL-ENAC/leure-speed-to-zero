from backend.src.api.routes import router
from backend.src.config.settings import settings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging
from fastapi.responses import ORJSONResponse

# Set servers in OpenAPI schema
from fastapi.openapi.utils import get_openapi
import os
from fastapi.middleware.gzip import GZipMiddleware


app = FastAPI(root_path=settings.PATH_PREFIX)
app.include_router(router)
app.add_middleware(GZipMiddleware, minimum_size=100000, compresslevel=1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


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
