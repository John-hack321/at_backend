# services/timetable_alerts/alert_service.py
import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from db.models.model_timetable import TimeTable
from services.sms_services.sms_service import sms_service
from db.db_setup import AsyncSessionLocal

logger = logging.getLogger(__name__)

class TimetableAlertService:
    """
    Service for managing timetable alerts and SMS notifications
    """
    
    def __init__(self):
        self.alert_intervals = [120, 30, 5]  # Alert at 2 hours, 30 minutes, and 5 minutes before
        self.student_contacts = []  # Will be populated from database
        self.running = False
    
    async def get_student_contacts(self, db: AsyncSession) -> List[str]:
        """
        Get all student phone numbers from the database
        You'll need to implement this based on your student model
        
        Args:
            db: Database session
            
        Returns:
            List[str]: List of formatted phone numbers
        """
        try:
            # TODO: Replace with your actual student model query
            # query = select(Student.phone).where(Student.active == True)
            # result = await db.execute(query)
            # phones = [phone[0] for phone in result.fetchall()]
            
            # For now, return demo numbers (replace with actual implementation)
            demo_phones = [
                "+254700000001",
                "+254700000002", 
                "+254700000003"
            ]
            
            # Format all phone numbers
            formatted_phones = [sms_service.format_phone_number(phone) for phone in demo_phones]
            return formatted_phones
            
        except Exception as e:
            logger.error(f"Error fetching student contacts: {str(e)}")
            return []
    
    async def get_todays_timetable(self, db: AsyncSession) -> List[TimeTable]:
        """
        Get today's timetable from the database
        
        Args:
            db: Database session
            
        Returns:
            List[TimeTable]: List of today's classes
        """
        try:
            today = datetime.now().strftime('%A').lower()  # Get current day name
            
            query = select(TimeTable).where(
                TimeTable.day.ilike(f"%{today}%")
            ).order_by(TimeTable.start_time)
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error fetching today's timetable: {str(e)}")
            return []
    
    async def check_and_send_alerts(self):
        """
        Check for upcoming classes and send appropriate alerts
        """
        async with AsyncSessionLocal() as db:
            try:
                current_time = datetime.now()
                today_classes = await self.get_todays_timetable(db)
                student_contacts = await self.get_student_contacts(db)
                
                if not student_contacts:
                    logger.warning("No student contacts found")
                    return
                
                for class_item in today_classes:
                    # Combine today's date with class start time
                    class_datetime = datetime.combine(
                        current_time.date(),
                        class_item.start_time
                    )
                    
                    # Check each alert interval
                    for minutes_before in self.alert_intervals:
                        alert_time = class_datetime - timedelta(minutes=minutes_before)
                        
                        # Check if we should send alert now (within 1 minute window)
                        time_diff = abs((current_time - alert_time).total_seconds())
                        
                        if time_diff <= 60:  # Within 1 minute of alert time
                            await self.send_class_alert(
                                class_item, 
                                student_contacts, 
                                minutes_before
                            )
                
            except Exception as e:
                logger.error(f"Error in check_and_send_alerts: {str(e)}")
    
    async def send_class_alert(self, class_item: TimeTable, 
                             student_contacts: List[str], minutes_before: int):
        """
        Send SMS alert for a specific class
        
        Args:
            class_item: TimeTable object
            student_contacts: List of student phone numbers
            minutes_before: Minutes before class starts
        """
        try:
            start_time_str = class_item.start_time.strftime('%H:%M')
            end_time_str = class_item.end_time.strftime('%H:%M')
            
            # Generate appropriate message based on time before class
            if minutes_before <= 10:
                message = sms_service.generate_immediate_class_message(
                    class_item.unit,
                    start_time_str,
                    end_time_str
                )
            else:
                message = sms_service.generate_class_reminder_message(
                    class_item.unit,
                    start_time_str,
                    end_time_str,
                    minutes_before
                )
            
            # Send SMS to all students
            result = await sms_service.send_sms(student_contacts, message)
            
            if result['success']:
                logger.info(f"Alert sent for {class_item.unit} class ({minutes_before} min before)")
            else:
                logger.error(f"Failed to send alert for {class_item.unit}: {result['message']}")
                
        except Exception as e:
            logger.error(f"Error sending class alert: {str(e)}")
    
    async def send_custom_message(self, message: str, recipients: Optional[List[str]] = None):
        """
        Send custom message to students
        
        Args:
            message: Custom message to send
            recipients: Specific recipients (if None, send to all students)
        """
        async with AsyncSessionLocal() as db:
            try:
                if recipients is None:
                    recipients = await self.get_student_contacts(db)
                
                result = await sms_service.send_sms(recipients, message)
                return result
                
            except Exception as e:
                logger.error(f"Error sending custom message: {str(e)}")
                return {
                    'success': False,
                    'error': str(e),
                    'message': 'Failed to send custom message'
                }
    
    async def start_scheduler(self):
        """
        Start the alert scheduler (runs continuously)
        """
        self.running = True
        logger.info("Timetable alert scheduler started")
        
        while self.running:
            try:
                await self.check_and_send_alerts()
                # Check every minute
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                await asyncio.sleep(60)  # Continue running even if there's an error
    
    def stop_scheduler(self):
        """
        Stop the alert scheduler
        """
        self.running = False
        logger.info("Timetable alert scheduler stopped")

# Singleton instance
alert_service = TimetableAlertService()