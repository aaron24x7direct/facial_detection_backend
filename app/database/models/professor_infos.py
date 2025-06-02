from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class ProfessorInfo(Base):
    __tablename__ = 'professor_infos'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    section = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    day = Column(String, nullable=False)
    time = Column(String, nullable=False)

    user = relationship("User", back_populates="professor_infos")