# db/models/model_student.py
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.db_setup import Base
from db.models.mixins import TimeStamp

class Student(Base, TimeStamp):
    __tablename__ = "students"

    id = Column(Integer, index=True, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    student_id = Column(String, unique=True, nullable=False)  # Student registration number
    active = Column(Boolean, default=True, nullable=False)
    
    # Optional: Link to a class/grade
    class_name = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Student(name='{self.name}', student_id='{self.student_id}')>"