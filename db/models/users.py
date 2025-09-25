from sqlalchemy.orm import declarative_base

# Import the Base from db_setup to ensure all models use the same Base
from db.db_setup import Base
from db.models.mixins import DataTime

# You can define your models here or in separate files
# For example:
# from .another_model import AnotherModel

# Example model template (uncomment and modify as needed):
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

class ExampleModel(Base):
    __tablename__ = 'example_models'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
"""