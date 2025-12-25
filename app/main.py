import os
import random
from contextlib import asynccontextmanager
from datetime import datetime, date
from typing import List, AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.schemas import TaskCreate, TaskUpdate, TaskResponse, ProfessionalResponse, ServiceItem
from app.models import Task, Professional, Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./plumbing.db")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

# --- БАЗА УСЛУГ ---
SERVICES_DB = {
    "Аварийный сантехник": [
        {"name": "Устранение засора (мех. способ)", "price": 2500},
        {"name": "Гидродинамическая промывка", "price": 5000},
        {"name": "Ликвидация протечки трубы", "price": 1500},
        {"name": "Замена гибкой подводки", "price": 800},
        {"name": "Ремонт сливного бачка", "price": 1200}
    ],
    "Инженер-монтажник": [
        {"name": "Разводка труб ХВС/ГВС (точка)", "price": 3000},
        {"name": "Монтаж инсталляции Grohe/Geberit", "price": 4500},
        {"name": "Установка коллекторной группы", "price": 3500},
        {"name": "Штробление стен под трубы", "price": 1000},
        {"name": "Установка редуктора давления", "price": 1500}
    ],
    "Установка санфаянса": [
        {"name": "Установка акриловой ванны", "price": 3500},
        {"name": "Монтаж душевого уголка", "price": 6000},
        {"name": "Установка унитаза (компакт)", "price": 2500},
        {"name": "Монтаж раковины с тумбой", "price": 3000},
        {"name": "Герметизация швов (силикон)", "price": 1500}
    ],
    "Мастер по отоплению": [
        {"name": "Монтаж радиатора (биметалл)", "price": 3500},
        {"name": "Обвязка настенного котла", "price": 8000},
        {"name": "Монтаж водяного теплого пола (м2)", "price": 600},
        {"name": "Замена циркуляционного насоса", "price": 2000},
        {"name": "Опрессовка системы отопления", "price": 2500}
    ]
}

async def seed_data(session: AsyncSession):
    if (await session.execute(select(Professional))).scalars().first(): return

    pros = [
        Professional(name="Дмитрий Кузнецов", specialty="Инженер-монтажник", rating=4.9, price_start=3000, experience=12, age=42, slogan="Делаю разводку труб на века", photo_url="https://randomuser.me/api/portraits/men/32.jpg"),
        Professional(name="Алексей Смирнов", specialty="Аварийный сантехник", rating=5.0, price_start=2000, experience=8, age=31, slogan="Приеду за 30 минут, устраню потоп", photo_url="https://randomuser.me/api/portraits/men/44.jpg"),
        Professional(name="Борис 'Бритва'", specialty="Установка санфаянса", rating=4.7, price_start=2500, experience=15, age=45, slogan="Аккуратный монтаж без сколов", photo_url="https://randomuser.me/api/portraits/men/85.jpg"),
        Professional(name="Михаил Зубенко", specialty="Аварийный сантехник", rating=4.5, price_start=1500, experience=3, age=24, slogan="Быстро прочищу любой засор", photo_url="https://randomuser.me/api/portraits/men/11.jpg"),
        Professional(name="Виктор Петрович", specialty="Мастер по отоплению", rating=4.9, price_start=3500, experience=25, age=55, slogan="Тепло в каждый дом", photo_url="https://randomuser.me/api/portraits/men/65.jpg"),
        Professional(name="Иван Грозный", specialty="Инженер-монтажник", rating=4.2, price_start=2800, experience=20, age=50, slogan="Работаю с Rehau и сшитым полиэтиленом", photo_url="https://randomuser.me/api/portraits/men/55.jpg"),
        Professional(name="Сергей Лазарев", specialty="Установка санфаянса", rating=4.8, price_start=2000, experience=5, age=28, slogan="Подключу стиралку и смеситель", photo_url="https://randomuser.me/api/portraits/men/33.jpg"),
        Professional(name="Павел Дуров", specialty="Мастер по отоплению", rating=4.6, price_start=3000, experience=7, age=30, slogan="Умное отопление и котлы", photo_url="https://randomuser.me/api/portraits/men/22.jpg"),
        Professional(name="Андрей Макаревич", specialty="Аварийный сантехник", rating=4.8, price_start=1800, experience=12, age=40, slogan="Срочный выезд 24/7", photo_url="https://randomuser.me/api/portraits/men/12.jpg"),
        # Имя заменено здесь:
        Professional(name="Алексей Новиков", specialty="Инженер-монтажник", rating=4.9, price_start=3200, experience=9, age=38, slogan="Честные цены на черновую сантехнику", photo_url="https://randomuser.me/api/portraits/men/76.jpg"),
    ]
    session.add_all(pros)
    await session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_maker() as session:
        await seed_data(session)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def read_root(): return FileResponse("app/static/index.html")

@app.get("/professionals", response_model=List[ProfessionalResponse])
async def get_pros(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Professional))
    pros = result.scalars().all()
    out = []
    for p in pros:
        srv = SERVICES_DB.get(p.specialty, SERVICES_DB["Установка санфаянса"])
        p_resp = ProfessionalResponse.model_validate(p)
        p_resp.services = [ServiceItem(name=s["name"], price=s["price"]) for s in srv]
        out.append(p_resp)
    return out

@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(db: AsyncSession = Depends(get_db)):
    query = select(Task).options(selectinload(Task.professional)).order_by(Task.created_at.desc())
    return (await db.execute(query)).scalars().all()

@app.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    status = "в_работе" if task.professional_id else "поиск_мастера"
    db_task = Task(**task.model_dump(), status=status)
    db.add(db_task)
    await db.commit()
    q = select(Task).options(selectinload(Task.professional)).where(Task.id == db_task.id)
    return (await db.execute(q)).scalar_one()

@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, update: TaskUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Task).where(Task.id == task_id))
    task = res.scalar_one_or_none()
    if not task: raise HTTPException(404)
    for k, v in update.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    await db.commit()
    q = select(Task).options(selectinload(Task.professional)).where(Task.id == task_id)
    return (await db.execute(q)).scalar_one()

@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Task).where(Task.id == task_id))
    t = res.scalar_one()
    if t: await db.delete(t); await db.commit()
