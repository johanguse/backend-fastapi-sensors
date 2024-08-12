import logging

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.routers import companies, equipment, sensor_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME)

add_pagination(app)

Base.metadata.create_all(bind=engine)

app.include_router(companies.router, prefix=settings.API_V1_STR)
app.include_router(equipment.router, prefix=settings.API_V1_STR)
app.include_router(sensor_data.router, prefix=settings.API_V1_STR)


@app.get('/health')
async def health_check(db: Session = Depends(get_db)):
    try:
        result = db.execute(text('SELECT 1'))
        result.scalar()
        return {'status': 'healthy', 'database': 'connected'}
    except Exception as e:
        return {
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
        }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f'Global exception: {str(exc)}')
    return JSONResponse(
        status_code=500, content={'message': 'An unexpected error occurred.'}
    )
