from bookings.routes import bookings_router
from constants import ErrorCode
from dependencies import AuthException
from schedules.routes import schedules_router
from services.routes import service_router
from users.routes import auth_router, client_router, professional_router

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from contextlib import asynccontextmanager
from database import Base, engine


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    print("Tables created!")
    yield

    print("Shutting down...")


def create_app():
    app = FastAPI(title='Bloom API', version='1.0.0', lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['http://localhost:3000'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

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
        """Handle all database constraint violations."""
        orig = exc.orig
        error_msg = str(orig.args[0]) if orig.args else str(orig)

        code = ErrorCode.CONFLICT
        message = 'Resource already exists'
        details = {}

        # Parse constraint type and field
        if 'UNIQUE constraint failed' in error_msg:
            constraint_part = error_msg.split(': ')[1] if ': ' in error_msg else ''
            fields = constraint_part.split(', ')

            for field_path in fields:
                if '.' in field_path:
                    field = field_path.split('.')[-1]
                    details[field] = f'{field.replace("_", " ").title()} already exists'

            if not details:
                details['resource'] = 'Duplicate entry'

        elif 'FOREIGN KEY constraint failed' in error_msg:
            code = ErrorCode.CONFLICT
            message = 'Invalid reference'
            details['resource'] = 'Referenced resource does not exist'

        elif 'CHECK constraint failed' in error_msg:
            # Extract constraint name if available
            constraint_name = ''
            if 'check_' in error_msg.lower():
                constraint_name = error_msg.split('check_')[1].split()[0]

            message = 'Invalid data'
            details['resource'] = f'Constraint violation: {constraint_name}' if constraint_name else 'Data validation failed'

        else:
            # Generic constraint error
            details['resource'] = 'Database constraint violated'

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'success': False,
                'error': {
                    'code': code,
                    'message': message,
                    'details': details if details else {'resource': 'Resource already exists'}
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
    app.include_router(bookings_router, prefix='/api/v1/bookings')
    app.include_router(client_router, prefix='/api/v1')
    app.include_router(professional_router, prefix='/api/v1')
    app.include_router(service_router, prefix='/api/v1/services')
    app.include_router(schedules_router, prefix='/api/v1/schedules')

    add_pagination(app)

    return app


app = create_app()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)