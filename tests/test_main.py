from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Тест 1: Проверка, что главная страница (фронтенд) отдается
def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    # Проверяем, что в ответе есть часть вашего HTML
    assert "Сантехнички" in response.text

# Тест 2: Проверка, что список профессионалов загружается и их 10
def test_get_professionals():
    response = client.get("/professionals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 10  # Мы добавляли 10 мастеров
    # Проверяем структуру одного мастера
    assert "name" in data[0]
    assert "services" in data[0]

# Тест 3: Создание заявки (сценарий "Поиск мастера")
def test_create_task_search():
    payload = {
        "client_name": "Тестовый Клиент",
        "phone": "+7 (999) 000-00-00",
        "description": "Тестовая проблема",
        "appointment_date": "2025-12-30"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["client_name"] == payload["client_name"]
    assert data["status"] == "поиск_мастера"
    assert "id" in data
