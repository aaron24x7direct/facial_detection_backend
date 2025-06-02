from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base
from zoneinfo import ZoneInfo

class FacialDetection(Base):
    __tablename__ = 'facial_detections'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow().replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Manila")))

    user = relationship("User", back_populates="facials")
    subject = relationship("Subject", back_populates="facials")

class FacialDetectionUserImage(Base):
    __tablename__ = 'facial_detection_user_images'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    image_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow().replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Manila")))
    
    user = relationship("User", back_populates="facial_images")
    