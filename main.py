from fastapi import FastAPI

from app.controllers.base_controller import router
from app.middlewares.exception_handler_middleware import setup_exception_handlers
from app.services.vector_db_service import VectorDBService
from app.services.vector_db_service_interface import VectorDBServiceInterface

app = FastAPI(
    title="Vector DB API",
    description="API para interactuar con Pinecone Vector Database",
    version="1.0.0"
)

app.include_router(router)
app.dependency_overrides[VectorDBServiceInterface] = VectorDBService
setup_exception_handlers(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
