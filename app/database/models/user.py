from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'))
    fullname = Column(String, nullable=False)
    section = Column(String, nullable=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    is_email_verified = Column(Boolean, default=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship("Role", back_populates="users")
    facial_images = relationship("FacialDetectionUserImage", back_populates="user", cascade="all, delete-orphan")
    facials = relationship("FacialDetection", back_populates="user", cascade="all, delete-orphan")
    student_infos = relationship("StudentInfo", back_populates="user", cascade="all, delete-orphan")
    professor_infos = relationship("ProfessorInfo", back_populates="user", cascade="all, delete-orphan")