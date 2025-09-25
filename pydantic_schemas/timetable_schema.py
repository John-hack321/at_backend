# pydantic_schemas/timetable_schema.py
from pydantic import BaseModel
from datetime import time
from typing import Optional

class TimetableCreateRequest(BaseModel):
    start_time: time
    end_time: time
    unit: str
    day: str
    
class TimetableResponse(BaseModel):
    id: int
    start_time: time
    end_time: time
    unit: str
    day: str
    
    class Config:
        orm_mode = True