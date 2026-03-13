from constants import ErrorCode
from dependencies import AuthException
from services.routes import service_router
from users.routes import auth_router, client_router, professional_router

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError


def create_app():
    app = FastAPI(title='Bloom API', version='1.0.0')

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):
        standardized_details = {}
        for err in exc.errors():
            field_name = err['loc'][-1] if err['loc'] else "__root__"
            standardized_details[field_name] = err['msg']

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'success': False,
                'error': {
                    'code': ErrorCode.VALIDATION_ERROR,
                    'message': "Invalid input provided.",
                    'details': standardized_details
                }
            }
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'success': False,
                'error': {
                    'code': ErrorCode.CONFLICT,
                    'message': 'Resource already exists',
                    'details': {'email': 'Email already exists'}
                }
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if exc.status_code in [401, 403]:
            code = ErrorCode.AUTH_FAILED
        else:
            code = ErrorCode.HTTP_ERROR

        return JSONResponse(
            status_code=exc.status_code,
            content={
                'success': False,
                'error': {
                    'code': code,
                    'message': exc.detail,
                    'details': {}
                }
            }
        )

    @app.exception_handler(AuthException)
    async def auth_exception_handler(request: Request, exc: AuthException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'success': False,
                'error': {
                    'code': ErrorCode.AUTH_FAILED,
                    'message': exc.message,
                    'details': {}
                }
            }
        )

    app.include_router(auth_router, prefix='/api/v1/auth')
    app.include_router(client_router, prefix='/api/v1')
    app.include_router(professional_router, prefix='/api/v1')
    app.include_router(service_router, prefix='/api/v1/services')

    return app


app = create_app()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)