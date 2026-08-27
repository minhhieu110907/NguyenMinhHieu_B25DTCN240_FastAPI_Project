from fastapi import FastAPI
from contextlib import asynccontextmanager
import app.models 


from app.database.redis import redis_manager

from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_header import SecurityHeadersMiddleware
from app.middleware.cors import CORSMiddlewareWrapper

from app.routers.auth import router as auth_router
from app.routers.users import router as user_router
from app.routers.project import router as project_router
from app.routers.project_member import router as project_member_router
from app.routers.task import router as task_router

from app.core.exceptions import AppException
from app.core.handlers import app_exception_handler,general_exception_handler
from app.core.config import settings
from app.core.logger import setup_global_logging
setup_global_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_manager.connect()
    yield
    await redis_manager.close()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG,lifespan=lifespan)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CORSMiddlewareWrapper)


app.add_exception_handler(AppException,app_exception_handler)
app.add_exception_handler(Exception,general_exception_handler)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(project_router)
app.include_router(project_member_router)
app.include_router(task_router)

@app.get("/health")
def welcome_to_my_system():
    return {"status": "Eveything is very good"}
