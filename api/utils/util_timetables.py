from locale import currency
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from db.models.model_timetable import TimeTable


async def add_new_timetalbe(db : AsyncSession , timetable_data):
    db_timetable = TimeTable(
        startime = timetable_data.get('start_time'),
        end_time = timetable_data.get('end_time'),
        unit = timetable_data.get('unit'),
    )

    db.add(db_timetable)
    db.refresh()
    db.flush(db_timetable)
    return db_timetable