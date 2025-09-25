# services/sms_services/sms_service.py
import os
import requests
import logging
from typing import List, Optional
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

logger = logging.getLogger(__name__)

class AfricasTalkingSMSService:
    """
    Service for sending SMS messages using Africa's Talking API
    """
    
    def __init__(self):
        self.api_key = os.getenv('AFRICAS_TALKING_API_KEY')
        self.username = "sandbox"  # Use "sandbox" for testing, change to your username for production
        self.base_url = "https://api.sandbox.africastalking.com/version1/messaging"  # Sandbox URL
        # For production, use: https://api.africastalking.com/version1/messaging
        
        if not self.api_key:
            raise ValueError("AFRICAS_TALKING_API_KEY not found in environment variables")
        
        self.headers = {
            'apiKey': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
    
    async def send_sms(self, phone_numbers: List[str], message: str) -> dict:
        """
        Send SMS to multiple phone numbers
        
        Args:
            phone_numbers: List of phone numbers (format: +254XXXXXXXXX)
            message: SMS message content
            
        Returns:
            dict: Response from Africa's Talking API
        """
        try:
            # Join phone numbers with commas for bulk SMS
            recipients = ','.join(phone_numbers)
            
            payload = {
                'username': self.username,
                'to': recipients,
                'message': message
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=payload
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"SMS sent successfully: {result}")
                return {
                    'success': True,
                    'data': result,
                    'message': 'SMS sent successfully'
                }
            else:
                logger.error(f"Failed to send SMS: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}",
                    'message': response.text
                }
                
        except Exception as e:
            logger.error(f"Exception in send_sms: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to send SMS due to an internal error'
            }
    
    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number to Africa's Talking format (+254XXXXXXXXX)
        
        Args:
            phone: Phone number in various formats
            
        Returns:
            str: Formatted phone number
        """
        # Remove any spaces, dashes, or other characters
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Handle Kenyan numbers
        if clean_phone.startswith('254'):
            return f"+{clean_phone}"
        elif clean_phone.startswith('07') or clean_phone.startswith('01'):
            return f"+254{clean_phone[1:]}"
        elif len(clean_phone) == 9:
            return f"+254{clean_phone}"
        
        # If already in correct format
        if phone.startswith('+254'):
            return phone
            
        # Default: assume it's a Kenyan number
        return f"+254{clean_phone}"
    
    def generate_class_reminder_message(self, unit: str, start_time: str, 
                                      end_time: str, minutes_before: int) -> str:
        """
        Generate a formatted reminder message for class
        
        Args:
            unit: Subject/unit name
            start_time: Class start time
            end_time: Class end time
            minutes_before: How many minutes before the class
            
        Returns:
            str: Formatted message
        """
        if minutes_before >= 60:
            time_text = f"{minutes_before // 60} hour{'s' if minutes_before > 60 else ''}"
        else:
            time_text = f"{minutes_before} minute{'s' if minutes_before > 1 else ''}"
        
        message = (
            f"📚 Class Reminder!\n\n"
            f"Subject: {unit}\n"
            f"Time: {start_time} - {end_time}\n"
            f"Starts in {time_text}\n\n"
            f"Please be prepared and on time. 👨‍🏫"
        )
        
        return message
    
    def generate_immediate_class_message(self, unit: str, start_time: str, 
                                       end_time: str) -> str:
        """
        Generate message for class starting soon (5-10 minutes)
        
        Args:
            unit: Subject/unit name
            start_time: Class start time
            end_time: Class end time
            
        Returns:
            str: Formatted urgent message
        """
        message = (
            f"🚨 URGENT: Class Starting Soon!\n\n"
            f"Subject: {unit}\n"
            f"Time: {start_time} - {end_time}\n\n"
            f"Please head to class immediately! ⏰"
        )
        
        return message

# Singleton instance
sms_service = AfricasTalkingSMSService()