import smtplib
import os
from twilio.rest import Client
from pathlib import Path
from urllib.parse import quote

class NotificationManager:

    def __init__(self):
        # Retrieve environment variables
        self.smtp_address = os.environ.get("EMAIL_PROVIDER_SMTP_ADDRESS", "smtp.gmail.com")
        self.email = os.environ.get("MANAGER_EMAIL")
        self.email_password = os.environ.get("MANAGER_EMAIL_PASSWORD")
        self.twilio_virtual_number = os.environ.get("TWILIO_VIRTUAL_NUMBER")
        self.twilio_verified_number = os.environ.get("TWILIO_VERIFIED_NUMBER")
        self.whatsapp_number = os.environ.get("TWILIO_WHATSAPP_NUMBER")

        self.image_base_url = os.environ.get(
        "IMAGE_BASE_URL",
        "https://raw.githubusercontent.com/Thomasayanfeoluwa/AI-Food-Ordering-System/main/images"
        )
        
        # Initialize Twilio Client only if credentials exist
        twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")

        if twilio_sid and twilio_token:
            self.client = Client(twilio_sid, twilio_token)
            print("Twilio client initialized successfully")
        else:
            self.client = None
            print("Twilio credentials not found. SMS/WhatsApp disabled.")

    def _get_local_image_path(self, image_reference):
        """
        Convert image reference to actual local file path
        Handles both direct paths and references from LLM
        """
        images_folder = Path("images")
        
        # If it's already a valid path, use it
        if Path(image_reference).exists():
            return Path(image_reference)
        
        # Extract filename from URL-style references
        filename = Path(image_reference).name
        
        # Try different extensions
        possible_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        for ext in possible_extensions:
            # Try with original filename
            test_path = images_folder / filename
            if test_path.exists():
                return test_path
            
            # Try without extension + new extension
            name_without_ext = Path(filename).stem
            test_path = images_folder / f"{name_without_ext}{ext}"
            if test_path.exists():
                return test_path
            
            # Try with different case
            test_path = images_folder / f"{name_without_ext.lower()}{ext}"
            if test_path.exists():
                return test_path
        
        return None

    def _get_public_image_url(self, image_reference):
        filename = Path(str(image_reference)).name
        return f"{self.image_base_url}/{quote(filename)}"

    def send_sms(self, message_body):
        """Send SMS notification (TEXT ONLY - no images)"""
        if not self.client:
            print("SMS failed: Twilio client not initialized")
            return False
            
        try:
            message = self.client.messages.create(
                from_=self.twilio_virtual_number,
                body=message_body,
                to=self.twilio_verified_number
            )
            print(f"SMS sent. SID: {message.sid}")
            return True
        except Exception as e:
            print(f"SMS failed: {e}")
            return False

    def send_whatsapp_with_media(self, message_body, image_paths=None):
        """Send WhatsApp message WITH ACTUAL IMAGES (ONLY for WhatsApp)"""
        if not self.client:
            print("WhatsApp failed: Twilio client not initialized")
            return False
        
        try:
            if image_paths and len(image_paths) > 0:
                # Send first image with caption
                first_image_path = image_paths[0]
                if first_image_path.exists():
                    message = self.client.messages.create(
                        from_=f'whatsapp:{self.whatsapp_number}',
                        body=message_body,
                        media_url=[self._get_public_image_url(first_image_path)],
                        to=f'whatsapp:{self.twilio_verified_number}'
                    )
                    print(f"WhatsApp with image sent. SID: {message.sid}")
                    
                    # Send remaining images without captions
                    for img_path in image_paths[1:]:
                        if img_path.exists():
                            self.client.messages.create(
                                from_=f'whatsapp:{self.whatsapp_number}',
                                media_url=[self._get_public_image_url(img_path)],
                                to=f'whatsapp:{self.twilio_verified_number}'
                            )
                    return True
            else:
                # Fallback to text-only
                return self.send_whatsapp(message_body)
                
        except Exception as e:
            print(f"WhatsApp with media failed: {e}")
            # Fallback to text-only
            return self.send_whatsapp(message_body)

    def send_whatsapp(self, message_body):
        """Send WhatsApp message (text-only fallback)"""
        if not self.client:
            print("WhatsApp failed: Twilio client not initialized")
            return False
            
        try:
            message = self.client.messages.create(
                from_=f'whatsapp:{self.whatsapp_number}',
                body=message_body,
                to=f'whatsapp:{self.twilio_verified_number}'
            )
            print(f"WhatsApp sent. SID: {message.sid}")
            return True
        except Exception as e:
            print(f"WhatsApp failed: {e}")
            return False

    def send_emails(self, email_list, email_body):
        """Send email notifications (TEXT ONLY - no images)"""
        if not self.email or not self.email_password:
            print("Email failed: Email credentials not configured")
            return False
            
        try:
            with smtplib.SMTP(self.smtp_address, 587) as connection:  
                connection.starttls()
                connection.login(self.email, self.email_password)
                for email in email_list:
                    connection.sendmail( 
                        from_addr=self.email,
                        to_addrs=email,
                        msg=f"Subject:New Delivery Order!\n\n{email_body}".encode('utf-8')
                    )
                    print(f"Email sent to: {email}")
            return True
        except Exception as e:
            print(f"Email failed: {e}")
            return False

    def notify_owner_with_whatsapp_images(self, order_details, customer_info, total_amount, image_references):
        """
        ENHANCED notification with ACTUAL ORDER IMAGES FOR WHATSAPP ONLY
        SMS and Email remain text-only
        """
        # Convert image references to actual file paths
        actual_image_paths = []
        for img_ref in image_references:
            img_path = self._get_local_image_path(img_ref)
            if img_path:
                actual_image_paths.append(img_path)
                print(f"✅ Found image: {img_path}")
            else:
                print(f"❌ Image not found: {img_ref}")

        # Base notification message (for all channels)
        base_message = f"""
🚨 **NEW CUSTOMER ORDER** 🚨

👤 **CUSTOMER DETAILS:**
📛 Name: {customer_info.get('name', 'Not provided')}
📞 Phone: {customer_info.get('phone', 'Not provided')}
📍 Address: {customer_info.get('address', 'Not provided')}

💰 **ORDER TOTAL:** ₦{total_amount:,.2f}

📦 **ORDER DETAILS:**
{order_details}

📍 **ACTION REQUIRED:** Please prepare this order immediately!
"""
        
        # Enhanced WhatsApp message with image info
        whatsapp_message = base_message
        if actual_image_paths:
            whatsapp_message += f"\n\n📸 **ORDER IMAGES ATTACHED:** {len(actual_image_paths)} image(s)"
        
        # Send notifications
        sms_sent = self.send_sms(base_message[:160])  # SMS limited, text-only
        
        # WhatsApp WITH ACTUAL IMAGES (ONLY channel with images)
        whatsapp_sent = self.send_whatsapp_with_media(whatsapp_message, actual_image_paths)
        
        # Email (text-only)
        email_sent = False
        owner_emails = os.environ.get("OWNER_EMAILS", "").split(',')
        if owner_emails and owner_emails[0]:
            email_body = f"""
NEW ORDER RECEIVED!

CUSTOMER INFORMATION:
Name: {customer_info.get('name', 'Not provided')}
Phone: {customer_info.get('phone', 'Not provided')}
Address: {customer_info.get('address', 'Not provided')}

ORDER TOTAL: ₦{total_amount:,.2f}

ORDER DETAILS:
{order_details}

ORDER CONTAINS: {len(actual_image_paths)} IMAGE(S) - Check WhatsApp for images
Please prepare immediately!
            """
            email_sent = self.send_emails(owner_emails, email_body)
        
        return {
            'sms': sms_sent,
            'whatsapp': whatsapp_sent,
            'email': email_sent,
            'images_found': len(actual_image_paths)
        }