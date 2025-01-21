from fastapi import FastAPI
from starlette.responses import JSONResponse


async def not_implemented_error_handler(request, exc: NotImplementedError):
    error_message = exc.args[0] if exc.args else "El proveedor no está implementado."

    return JSONResponse(
            status_code=400,
            content={"message": error_message}
        )


def setup_exception_handlers(app: FastAPI):
    app.add_exception_handler(NotImplementedError, not_implemented_error_handler)
