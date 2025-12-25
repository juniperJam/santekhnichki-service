from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel

# ... ServiceItem, ProfessionalBase, ProfessionalResponse остаются прежними ...

class ServiceItem(BaseModel):
    name: str
    price: int

class ProfessionalBase(BaseModel):
    name: str
    specialty: str
    rating: float
    price_start: int
    experience: int
    age: int
    slogan: str
    photo_url: str

class ProfessionalResponse(ProfessionalBase):
    id: int
    services: List[ServiceItem] = []
    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    client_name: str
    phone: str
    description: str
    appointment_date: date
    address: str
    appointment_time: str

class TaskCreate(TaskBase):
    professional_id: Optional[int] = None
    agreed_price: Optional[int] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    professional_id: Optional[int] = None
    agreed_price: Optional[int] = None
    # ДОБАВИЛИ ЭТИ ДВА ПОЛЯ:
    appointment_date: Optional[date] = None
    appointment_time: Optional[str] = None

class TaskResponse(TaskBase):
    id: int
    status: str
    agreed_price: Optional[int] = None
    professional: Optional[ProfessionalResponse] = None
    created_at: datetime
    class Config:
        from_attributes = True
