from datetime import time as time_, datetime
from sqlalchemy import Column, String, Integer, Time
from sqlalchemy.orm import relationship
from db.db_setup import Base
from db.models.mixins import TimeStamp

class TimeTable(Base, TimeStamp):
    __tablename__ = "time_table"  # Changed from "time-table" to use underscore

    id = Column(Integer, index=True, primary_key=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    unit = Column(String, nullable=False)
    day = Column(String, nullable=False)  # Fixed case for 'False'