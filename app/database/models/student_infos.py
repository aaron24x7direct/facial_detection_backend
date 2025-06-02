from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class StudentInfo(Base):
    __tablename__ = 'student_infos'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    campus = Column(String, nullable=False)
    academic_term = Column(String, nullable=False)
    academic_year = Column(String, nullable=False)
    student_number = Column(String, nullable=False)
    lrn = Column(String, nullable=False)
    year_status = Column(String, nullable=False)
    fullname = Column(String, nullable=False)
    sex = Column(String, nullable=False)
    course = Column(String, nullable=False)
    contact = Column(String, nullable=False)
    
    user = relationship("User", back_populates="student_infos")
    subjects = relationship("Subject", back_populates="student_info", cascade="all, delete-orphan")

class Subject(Base):
    __tablename__ = 'subjects'

    id = Column(Integer, primary_key=True)
    student_info_id = Column(Integer, ForeignKey('student_infos.id'))
    subject_code = Column(String, nullable=False)
    section = Column(String, nullable=False)
    lec_units = Column(String, nullable=False)
    lab_units = Column(String, nullable=False)
    days = Column(String, nullable=False)
    time = Column(String, nullable=False)
    room = Column(String, nullable=False)

    student_info = relationship("StudentInfo", back_populates="subjects")
    facials = relationship("FacialDetection", back_populates="subject", cascade="all, delete-orphan")