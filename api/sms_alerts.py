# api/api_sms_alerts.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK, HTTP_201_CREATED
import logging

from api.utils.dependancies import db_dependancy, user_depencancy
from services.sms_services.sms_service import sms_service
from services.timetable_alerts.alert_service import alert_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/sms',
    tags=['SMS Alerts']
)

class CustomMessageRequest(BaseModel):
    message: str
    recipients: Optional[List[str]] = None  # If None, send to all students

class TestSMSRequest(BaseModel):
    phone_number: str
    message: str

class AlertConfigRequest(BaseModel):
    alert_intervals: List[int]  # Minutes before class to send alerts
    enabled: bool = True

@router.post('/send-custom-message', status_code=HTTP_201_CREATED)
async def send_custom_message(
    db: db_dependancy,
    user: user_depencancy,
    message_request: CustomMessageRequest
):
    """
    Send custom message to students
    Only teachers/admins can send custom messages
    """
    try:
        # Format phone numbers if recipients are provided
        if message_request.recipients:
            formatted_recipients = [
                sms_service.format_phone_number(phone) 
                for phone in message_request.recipients
            ]
            result = await alert_service.send_custom_message(
                message_request.message, 
                formatted_recipients
            )
        else:
            result = await alert_service.send_custom_message(message_request.message)
        
        if result['success']:
            return {
                'success': True,
                'message': 'Custom message sent successfully',
                'data': result['data']
            }
        else:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send message: {result['message']}"
            )
            
    except Exception as e:
        logger.error(f"Error in send_custom_message: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send custom message"
        )

@router.post('/test-sms', status_code=HTTP_201_CREATED)
async def test_sms(
    db: db_dependancy,
    user: user_depencancy,
    test_request: TestSMSRequest
):
    """
    Test SMS functionality by sending a message to a single number
    """
    try:
        formatted_phone = sms_service.format_phone_number(test_request.phone_number)
        
        result = await sms_service.send_sms([formatted_phone], test_request.message)
        
        if result['success']:
            return {
                'success': True,
                'message': 'Test SMS sent successfully',
                'data': result['data']
            }
        else:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send test SMS: {result['message']}"
            )
            
    except Exception as e:
        logger.error(f"Error in test_sms: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test SMS"
        )

@router.post('/start-scheduler', status_code=HTTP_200_OK)
async def start_alert_scheduler(
    background_tasks: BackgroundTasks,
    db: db_dependancy,
    user: user_depencancy
):
    """
    Start the automatic timetable alert scheduler
    """
    try:
        if not alert_service.running:
            background_tasks.add_task(alert_service.start_scheduler)
            return {
                'success': True,
                'message': 'Alert scheduler started successfully'
            }
        else:
            return {
                'success': True,
                'message': 'Alert scheduler is already running'
            }
            
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start alert scheduler"
        )

@router.post('/stop-scheduler', status_code=HTTP_200_OK)
async def stop_alert_scheduler(
    db: db_dependancy,
    user: user_depencancy
):
    """
    Stop the automatic timetable alert scheduler
    """
    try:
        alert_service.stop_scheduler()
        return {
            'success': True,
            'message': 'Alert scheduler stopped successfully'
        }
            
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop alert scheduler"
        )

@router.get('/scheduler-status', status_code=HTTP_200_OK)
async def get_scheduler_status(
    db: db_dependancy,
    user: user_depencancy
):
    """
    Get the current status of the alert scheduler
    """
    try:
        return {
            'success': True,
            'running': alert_service.running,
            'alert_intervals': alert_service.alert_intervals
        }
            
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scheduler status"
        )

@router.post('/send-immediate-alert/{class_id}', status_code=HTTP_201_CREATED)
async def send_immediate_class_alert(
    class_id: int,
    db: db_dependancy,
    user: user_depencancy
):
    """
    Send immediate alert for a specific class
    """
    try:
        # Get the class details
        from db.models.model_timetable import TimeTable
        from sqlalchemy.future import select
        
        query = select(TimeTable).where(TimeTable.id == class_id)
        result = await db.execute(query)
        class_item = result.scalars().first()
        
        if not class_item:
            raise HTTPException(
                status_code=404,
                detail="Class not found"
            )
        
        # Get student contacts
        student_contacts = await alert_service.get_student_contacts(db)
        
        if not student_contacts:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No student contacts found"
            )
        
        # Send immediate alert
        await alert_service.send_class_alert(class_item, student_contacts, 0)
        
        return {
            'success': True,
            'message': f'Immediate alert sent for {class_item.unit} class'
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending immediate alert: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send immediate alert"
        )

@router.get('/todays-schedule', status_code=HTTP_200_OK)
async def get_todays_schedule_with_alerts(
    db: db_dependancy,
    user: user_depencancy
):
    """
    Get today's class schedule with alert information
    """
    try:
        from datetime import datetime, timedelta
        
        today_classes = await alert_service.get_todays_timetable(db)
        current_time = datetime.now()
        
        schedule_with_alerts = []
        for class_item in today_classes:
            class_datetime = datetime.combine(current_time.date(), class_item.start_time)
            
            # Calculate next alert times
            next_alerts = []
            for minutes_before in alert_service.alert_intervals:
                alert_time = class_datetime - timedelta(minutes=minutes_before)
                if alert_time > current_time:
                    next_alerts.append({
                        'minutes_before': minutes_before,
                        'alert_time': alert_time.strftime('%H:%M')
                    })
            
            schedule_with_alerts.append({
                'id': class_item.id,
                'unit': class_item.unit,
                'start_time': class_item.start_time.strftime('%H:%M'),
                'end_time': class_item.end_time.strftime('%H:%M'),
                'day': class_item.day,
                'next_alerts': next_alerts
            })
        
        return {
            'success': True,
            'data': schedule_with_alerts
        }
            
    except Exception as e:
        logger.error(f"Error getting today's schedule: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get today's schedule"
        )