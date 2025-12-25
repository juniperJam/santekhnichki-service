"""
Тесты для API заявок
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app, get_db, Base
from app.models import Task


# === FIXTURES ===

# Тестовая база данных в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db():
    """Создание тестовой БД"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async def override_get_db():
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_db):
    """AsyncClient для тестирования"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# === ТЕСТЫ ===

@pytest.mark.asyncio
async def test_create_task(client):
    """Тест: создание новой заявки"""
    tomorrow = date.today() + timedelta(days=1)
    
    response = await client.post(
        "/tasks",
        json={
            "client_name": "Иван Петров",
            "phone": "+79991234567",
            "description": "Нужно отремонтировать кран на кухне",
            "appointment_date": tomorrow.isoformat()
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["client_name"] == "Иван Петров"
    assert data["phone"] == "+79991234567"
    assert data["status"] == "новая"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_get_tasks(client):
    """Тест: получение всех заявок"""
    tomorrow = date.today() + timedelta(days=1)
    
    # Создаем 2 заявки
    for i in range(2):
        await client.post(
            "/tasks",
            json={
                "client_name": f"Клиент {i}",
                "phone": f"+7999123456{i}",
                "description": f"Проблема {i}",
                "appointment_date": tomorrow.isoformat()
            }
        )
    
    response = await client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["client_name"] == "Клиент 0"


@pytest.mark.asyncio
async def test_update_task(client):
    """Тест: обновление заявки"""
    tomorrow = date.today() + timedelta(days=1)
    
    # Создаем заявку
    create_response = await client.post(
        "/tasks",
        json={
            "client_name": "Петр Сидоров",
            "phone": "+79991234567",
            "description": "Течет труба в ванной",
            "appointment_date": tomorrow.isoformat()
        }
    )
    task_id = create_response.json()["id"]
    
    # Обновляем статус
    new_date = date.today() + timedelta(days=5)
    update_response = await client.put(
        f"/tasks/{task_id}",
        json={
            "status": "в_работе",
            "appointment_date": new_date.isoformat()
        }
    )
    
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["status"] == "в_работе"
    assert data["appointment_date"] == new_date.isoformat()


@pytest.mark.asyncio
async def test_delete_task(client):
    """Тест: удаление заявки"""
    tomorrow = date.today() + timedelta(days=1)
    
    # Создаем заявку
    create_response = await client.post(
        "/tasks",
        json={
            "client_name": "Тестовый Клиент",
            "phone": "+79991234567",
            "description": "Тестовая проблема",
            "appointment_date": tomorrow.isoformat()
        }
    )
    task_id = create_response.json()["id"]
    
    # Удаляем
    delete_response = await client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 204
    
    # Проверяем, что удалено
    get_response = await client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_reschedule_task(client):
    """Тест: перенос заявки на другую дату"""
    tomorrow = date.today() + timedelta(days=1)
    
    # Создаем заявку
    create_response = await client.post(
        "/tasks",
        json={
            "client_name": "Клиент",
            "phone": "+79991234567",
            "description": "Проблема",
            "appointment_date": tomorrow.isoformat()
        }
    )
    task_id = create_response.json()["id"]
    
    # Переносим на другую дату
    new_date = date.today() + timedelta(days=10)
    reschedule_response = await client.patch(
        f"/tasks/{task_id}/reschedule",
        params={"new_date": new_date.isoformat()}
    )
    
    assert reschedule_response.status_code == 200
    data = reschedule_response.json()
    assert data["appointment_date"] == new_date.isoformat()


@pytest.mark.asyncio
async def test_invalid_past_date(client):
    """Тест: попытка создать заявку на прошедшую дату"""
    past_date = date.today() - timedelta(days=1)
    
    response = await client.post(
        "/tasks",
        json={
            "client_name": "Клиент",
            "phone": "+79991234567",
            "description": "Проблема",
            "appointment_date": past_date.isoformat()
        }
    )
    
    assert response.status_code == 400
    assert "прошлом" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_statistics(client):
    """Тест: получение статистики"""
    tomorrow = date.today() + timedelta(days=1)
    
    # Создаем несколько заявок
    for i in range(3):
        await client.post(
            "/tasks",
            json={
                "client_name": f"Клиент {i}",
                "phone": f"+7999123456{i}",
                "description": f"Проблема {i}",
                "appointment_date": tomorrow.isoformat()
            }
        )
    
    response = await client.get("/statistics")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["upcoming_count"] == 3
    assert "новая" in data["by_status"]
    assert data["by_status"]["новая"] == 3
