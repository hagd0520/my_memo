from fastapi import FastAPI, Request
from fastapi.concurrency import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates

import models
from database import Base, engine
from controllers import router

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    
# FastAPi 애플리케이션 초기화
# Swagger UI 와 Redoc 비활성화
app = FastAPI(lifespan=app_lifespan, docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

app.include_router(router)
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})