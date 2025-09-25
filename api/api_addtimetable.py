from fastapi import APIRouter, HTTPException
import fastapi
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import time

from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.types import HTTPExceptionHandler
from api.utils.util_timetables import add_new_timetalbe

from api.utils.dependancies import db_dependancy

from api.utils.dependancies import user_depencancy

# hard_timetable_data = {
#     {'starttime' : time(7,0) , 'end_time' : time(9,0) , 'unit' : 'mathematics' },
#     {'starttime' : time(7,0) , 'end_time' : time(9,0) , 'unit' : 'mathematics' },
#     {'starttime' : time(7,0) , 'end_time' : time(9,0) , 'unit' : 'mathematics' },
#     {'starttime' : time(7,0) , 'end_time' : time(9,0) , 'unit' : 'mathematics' },
# }

router = APIRouter()

@router.post('/add_timetable')
async def add_timetable(db : db_dependancy , User : user_depencancy , timetable_data):
    # here we will add the things iteratively
    for item in timetable_data:
        try:
            new_db_object = add_new_timetalbe(item)
            if not new_db_object:
                raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR , detail = "object returned from database is undefined")
        except Exception as e:
            raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR , detail = "failed to add to the database ")
        
        