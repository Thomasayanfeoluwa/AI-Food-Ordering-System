import os
import smtplib
import requests
from pathlib import Path
from email.message import EmailMessage
from mimetypes import guess_type
from dotenv import load_dotenv


load_dotenv()


class NotificationManager:

    def __init__(self):
        # SMTP email configuration
        self.smtp_address = os.environ.get(
            "EMAIL_PROVIDER_SMTP_ADDRESS",
            "smtp.gmail.com"
        )
        self.email = os.environ.get("MANAGER_EMAIL")
        self.email_password = os.environ.get("MANAGER_EMAIL_PASSWORD")

        # Pushover configuration
        self.pushover_user_key = os.environ.get("PUSHOVER_USER_KEY")
        self.pushover_api_token = os.environ.get("PUSHOVER_API_TOKEN")

        self.pushover_url = "https://api.pushover.net/1/messages.json"

        if self.pushover_user_key and self.pushover_api_token:
            print("Pushover credentials loaded successfully")
        else:
            print("Pushover credentials not found. Pushover disabled.")

    def _get_local_image_path(self, image_reference):
        """
        Find an order image inside the project's images folder.
        """

        images_folder = Path("images")

        # Direct path
        if Path(image_reference).exists():
            return Path(image_reference)

        filename = Path(image_reference).name

        possible_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        ]

        for ext in possible_extensions:

            # Original filename
            test_path = images_folder / filename

            if test_path.exists():
                return test_path

            # Filename with detected extension
            name_without_ext = Path(filename).stem
            test_path = images_folder / f"{name_without_ext}{ext}"

            if test_path.exists():
                return test_path

            # Lowercase filename
            test_path = images_folder / f"{name_without_ext.lower()}{ext}"

            if test_path.exists():
                return test_path

        return None

    def send_pushover(self, message_body, image_paths=None):
        """
        Send an order notification through Pushover.

        The first image is attached directly to the notification.
        """

        if not self.pushover_user_key or not self.pushover_api_token:
            print("Pushover failed: credentials not configured")
            return False

        try:
            data = {
                "token": self.pushover_api_token,
                "user": self.pushover_user_key,
                "title": "🚨 NEW CUSTOMER ORDER",
                "message": message_body
            }

            files = None

            # Pushover supports one attachment per notification.
            # Send the first food image with the main notification.
            if image_paths:
                first_image = image_paths[0]

                if first_image.exists():
                    mime_type, _ = guess_type(first_image.name)

                    if not mime_type:
                        mime_type = "image/jpeg"

                    files = {
                        "attachment": (
                            first_image.name,
                            open(first_image, "rb"),
                            mime_type
                        )
                    }

                    data["attachment_type"] = mime_type

            try:
                response = requests.post(
                    self.pushover_url,
                    data=data,
                    files=files,
                    timeout=30
                )
            finally:
                if files:
                    files["attachment"][1].close()

            if response.status_code == 200:
                response_data = response.json()

                if response_data.get("status") == 1:
                    print("Pushover notification sent successfully")

                    # Send additional images as separate notifications.
                    if image_paths and len(image_paths) > 1:
                        for image_path in image_paths[1:]:
                            self._send_pushover_image(
                                image_path,
                                "Additional order image"
                            )

                    return True

            print(
                f"Pushover failed: HTTP {response.status_code} - "
                f"{response.text}"
            )
            return False

        except Exception as e:
            print(f"Pushover failed: {e}")
            return False

    def _send_pushover_image(self, image_path, message):
        """
        Send an additional food image as a separate Pushover notification.
        """

        if not image_path.exists():
            print(f"Pushover image not found: {image_path}")
            return False

        try:
            mime_type, _ = guess_type(image_path.name)

            if not mime_type:
                mime_type = "image/jpeg"

            with open(image_path, "rb") as image_file:

                response = requests.post(
                    self.pushover_url,
                    data={
                        "token": self.pushover_api_token,
                        "user": self.pushover_user_key,
                        "title": "📸 ORDER IMAGE",
                        "message": message,
                        "attachment_type": mime_type
                    },
                    files={
                        "attachment": (
                            image_path.name,
                            image_file,
                            mime_type
                        )
                    },
                    timeout=30
                )

            if response.status_code == 200:
                response_data = response.json()

                if response_data.get("status") == 1:
                    print(
                        f"Pushover image sent successfully: "
                        f"{image_path.name}"
                    )
                    return True

            print(
                f"Pushover image failed: HTTP {response.status_code} - "
                f"{response.text}"
            )
            return False

        except Exception as e:
            print(f"Pushover image failed: {e}")
            return False

    def send_emails(self, email_list, email_body, image_paths=None):
        """
        Send order email with food images attached.
        """

        if not self.email or not self.email_password:
            print("Email failed: Email credentials not configured")
            return False

        try:
            # Remove whitespace and empty values from email addresses.
            email_list = [
                email.strip()
                for email in email_list
                if email.strip()
            ]

            if not email_list:
                print("Email failed: No recipient email addresses configured")
                return False

            with smtplib.SMTP(self.smtp_address, 587) as connection:

                connection.starttls()

                connection.login(
                    self.email,
                    self.email_password
                )

                for recipient in email_list:

                    message = EmailMessage()

                    message["From"] = self.email
                    message["To"] = recipient
                    message["Subject"] = "New Delivery Order!"

                    message.set_content(email_body)

                    # Attach all available food images.
                    if image_paths:

                        for image_path in image_paths:

                            if not image_path.exists():
                                print(
                                    f"Email attachment not found: "
                                    f"{image_path}"
                                )
                                continue

                            mime_type, _ = guess_type(image_path.name)

                            if mime_type:
                                maintype, subtype = mime_type.split(
                                    "/",
                                    1
                                )
                            else:
                                maintype = "image"
                                subtype = "jpeg"

                            with open(image_path, "rb") as image_file:
                                image_data = image_file.read()

                            message.add_attachment(
                                image_data,
                                maintype=maintype,
                                subtype=subtype,
                                filename=image_path.name
                            )

                    connection.send_message(message)

                    print(f"Email sent to: {recipient}")

            return True

        except Exception as e:
            print(f"Email failed: {e}")
            return False

    def notify_owner_with_whatsapp_images(
        self,
        order_details,
        customer_info,
        total_amount,
        image_references
    ):
        """
        Existing application entry point.

        The method name is intentionally preserved so the existing
        Streamlit application does not need to be changed.

        Notifications are now sent through:
        - Pushover
        - SMTP email
        """

        actual_image_paths = []

        for img_ref in image_references:

            img_path = self._get_local_image_path(img_ref)

            if img_path:
                actual_image_paths.append(img_path)
                print(f"✅ Found image: {img_path}")
            else:
                print(f"❌ Image not found: {img_ref}")

        base_message = f"""
🚨 NEW CUSTOMER ORDER 🚨

CUSTOMER DETAILS:
Name: {customer_info.get('name', 'Not provided')}
Phone: {customer_info.get('phone', 'Not provided')}
Address: {customer_info.get('address', 'Not provided')}

ORDER TOTAL: ₦{total_amount:,.2f}

ORDER DETAILS:
{order_details}

ACTION REQUIRED:
Please prepare this order immediately!
"""

        if actual_image_paths:
            base_message += (
                f"\n\nORDER IMAGES: "
                f"{len(actual_image_paths)} image(s) attached."
            )

        # ---------------------------------------------------------
        # Pushover
        # ---------------------------------------------------------

        pushover_sent = self.send_pushover(
            base_message,
            actual_image_paths
        )

        # ---------------------------------------------------------
        # Email
        # ---------------------------------------------------------

        email_sent = False

        owner_emails = os.environ.get(
            "OWNER_EMAILS",
            ""
        ).split(",")

        owner_emails = [
            email.strip()
            for email in owner_emails
            if email.strip()
        ]

        if owner_emails:

            email_body = f"""
NEW ORDER RECEIVED!

CUSTOMER INFORMATION:
Name: {customer_info.get('name', 'Not provided')}
Phone: {customer_info.get('phone', 'Not provided')}
Address: {customer_info.get('address', 'Not provided')}

ORDER TOTAL: ₦{total_amount:,.2f}

ORDER DETAILS:
{order_details}

ORDER CONTAINS:
{len(actual_image_paths)} food image(s) attached.

Please prepare the order immediately!
"""

            email_sent = self.send_emails(
                owner_emails,
                email_body,
                actual_image_paths
            )

        # ---------------------------------------------------------
        # Return notification status
        # ---------------------------------------------------------

        return {
            "pushover": pushover_sent,
            "email": email_sent,
            "images_found": len(actual_image_paths)
        }
