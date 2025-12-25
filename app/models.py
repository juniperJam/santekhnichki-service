from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class Professional(Base):
    __tablename__ = "professionals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False)
    rating = Column(Float, default=5.0)
    price_start = Column(Integer, nullable=False)
    experience = Column(Integer, default=1)
    age = Column(Integer, default=30)
    slogan = Column(String(255), default="Качество гарантирую")
    photo_url = Column(String(255))
    
    tasks = relationship("Task", back_populates="professional")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    
    # НОВЫЕ ПОЛЯ
    address = Column(String(255), nullable=False)      # Адрес
    appointment_time = Column(String(50), nullable=False) # Время (строкой, например "14:30")
    
    status = Column(String(50), default="поиск_мастера", nullable=False)
    appointment_date = Column(Date, nullable=False, index=True)
    
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=True)
    agreed_price = Column(Integer, nullable=True)
    
    professional = relationship("Professional", back_populates="tasks")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
