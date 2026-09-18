import os
import smtplib
from email.message import EmailMessage
from mimetypes import guess_type
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


load_dotenv()


class NotificationManager:
    """
    Handles owner notifications for customer orders.

    Notification channels:
        - Pushover
        - SMTP email

    The existing method
    notify_owner_with_whatsapp_images()
    is intentionally preserved so the existing
    Streamlit application does not need to change.
    """

    def __init__(self) -> None:
        # ---------------------------------------------------------
        # Determine the project root.
        #
        # This assumes this file is located somewhere inside
        # the project and that the images folder is at the
        # project root.
        # ---------------------------------------------------------

        self.project_root = Path(__file__).resolve().parent

        self.images_folder = self.project_root / "images"

        # ---------------------------------------------------------
        # SMTP configuration
        # ---------------------------------------------------------

        self.smtp_address = os.environ.get(
            "EMAIL_PROVIDER_SMTP_ADDRESS",
            "smtp.gmail.com",
        ).strip()

        self.smtp_port = int(
            os.environ.get(
                "EMAIL_PROVIDER_SMTP_PORT",
                "587",
            )
        )

        self.email = os.environ.get(
            "MANAGER_EMAIL"
        )

        self.email_password = os.environ.get(
            "MANAGER_EMAIL_PASSWORD"
        )

        # ---------------------------------------------------------
        # Pushover configuration
        # ---------------------------------------------------------

        self.pushover_user_key = os.environ.get(
            "PUSHOVER_USER_KEY"
        )

        self.pushover_api_token = os.environ.get(
            "PUSHOVER_API_TOKEN"
        )

        self.pushover_url = (
            "https://api.pushover.net/1/messages.json"
        )

        # ---------------------------------------------------------
        # Configuration messages
        # ---------------------------------------------------------

        if (
            self.pushover_user_key
            and self.pushover_api_token
        ):
            print(
                "Pushover credentials loaded successfully."
            )
        else:
            print(
                "Pushover credentials not found. "
                "Pushover disabled."
            )

        if self.email and self.email_password:
            print(
                "Email credentials loaded successfully."
            )
        else:
            print(
                "Email credentials not found. "
                "Email notifications disabled."
            )

    # =============================================================
    # Helper methods
    # =============================================================

    @staticmethod
    def _safe_response_json(
        response: requests.Response,
    ) -> Optional[Dict[str, Any]]:
        """
        Safely parse a JSON HTTP response.

        Returns:
            Parsed dictionary if valid JSON is returned.
            None otherwise.
        """

        try:
            data = response.json()

            if isinstance(data, dict):
                return data

        except ValueError:
            pass

        return None

    @staticmethod
    def _get_image_mime_type(
        image_path: Path,
    ) -> str:
        """
        Determine the MIME type of an image.

        Falls back to image/jpeg if the extension cannot
        be identified.
        """

        mime_type, _ = guess_type(image_path.name)

        if mime_type and mime_type.startswith("image/"):
            return mime_type

        return "image/jpeg"

    @staticmethod
    def _is_valid_image_path(
        image_path: Path,
    ) -> bool:
        """
        Check that a path exists and is a regular file.
        """

        return (
            image_path.exists()
            and image_path.is_file()
        )

    def _get_local_image_path(
        self,
        image_reference: Any,
    ) -> Optional[Path]:
        """
        Find an order image inside the project's images folder.

        Supports:
            - direct file paths
            - filenames
            - filenames with/without extensions
            - case-insensitive filename matching
        """

        if not image_reference:
            return None

        image_reference = str(image_reference).strip()

        if not image_reference:
            return None

        # ---------------------------------------------------------
        # 1. Direct path
        # ---------------------------------------------------------

        direct_path = Path(image_reference)

        if self._is_valid_image_path(direct_path):
            return direct_path.resolve()

        # ---------------------------------------------------------
        # 2. Search inside the project's images folder
        # ---------------------------------------------------------

        if not self.images_folder.exists():
            return None

        if not self.images_folder.is_dir():
            return None

        filename = Path(image_reference).name

        if not filename:
            return None

        # ---------------------------------------------------------
        # Exact filename match
        # ---------------------------------------------------------

        exact_path = self.images_folder / filename

        if self._is_valid_image_path(exact_path):
            return exact_path.resolve()

        # ---------------------------------------------------------
        # Case-insensitive filename match
        # ---------------------------------------------------------

        filename_lower = filename.lower()

        try:
            for candidate in self.images_folder.iterdir():

                if not candidate.is_file():
                    continue

                if candidate.name.lower() == filename_lower:
                    return candidate.resolve()

        except OSError as exc:
            print(
                f"Could not read images directory: {exc}"
            )
            return None

        # ---------------------------------------------------------
        # Search using the filename stem.
        #
        # Example:
        # burger
        # burger.jpg
        # burger.jpeg
        # burger.png
        # burger.webp
        # ---------------------------------------------------------

        stem = Path(filename).stem.lower()

        supported_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }

        try:
            for candidate in self.images_folder.iterdir():

                if not candidate.is_file():
                    continue

                if candidate.suffix.lower() not in supported_extensions:
                    continue

                if candidate.stem.lower() == stem:
                    return candidate.resolve()

        except OSError as exc:
            print(
                f"Could not search images directory: {exc}"
            )
            return None

        return None

    # =============================================================
    # Pushover
    # =============================================================

    def send_pushover(
        self,
        message_body: str,
        image_paths: Optional[List[Path]] = None,
    ) -> bool:
        """
        Send an order notification through Pushover.

        Pushover supports one attachment per notification.
        Therefore:
            - The first image is attached to the main notification.
            - Additional images are sent as separate notifications.

        Returns:
            True only if the main notification and all additional
            image notifications are successfully sent.
        """

        if (
            not self.pushover_user_key
            or not self.pushover_api_token
        ):
            print(
                "Pushover failed: credentials not configured."
            )
            return False

        image_paths = image_paths or []

        # Only retain valid files.
        valid_image_paths = [
            path
            for path in image_paths
            if self._is_valid_image_path(path)
        ]

        try:
            data = {
                "token": self.pushover_api_token,
                "user": self.pushover_user_key,
                "title": "🚨 NEW CUSTOMER ORDER",
                "message": message_body,
            }

            # -----------------------------------------------------
            # Main notification attachment
            # -----------------------------------------------------

            if valid_image_paths:

                first_image = valid_image_paths[0]

                mime_type = self._get_image_mime_type(
                    first_image
                )

                data["attachment_type"] = mime_type

                with open(
                    first_image,
                    "rb",
                ) as image_file:

                    response = requests.post(
                        self.pushover_url,
                        data=data,
                        files={
                            "attachment": (
                                first_image.name,
                                image_file,
                                mime_type,
                            )
                        },
                        timeout=30,
                    )

            else:

                response = requests.post(
                    self.pushover_url,
                    data=data,
                    timeout=30,
                )

            # -----------------------------------------------------
            # Validate main notification response
            # -----------------------------------------------------

            response_data = self._safe_response_json(
                response
            )

            if (
                response.status_code != 200
                or not response_data
                or response_data.get("status") != 1
            ):
                print(
                    "Pushover failed: "
                    f"HTTP {response.status_code} - "
                    f"{response.text}"
                )
                return False

            print(
                "Pushover notification sent successfully."
            )

            # -----------------------------------------------------
            # Additional images
            # -----------------------------------------------------

            additional_images_sent = True

            for image_path in valid_image_paths[1:]:

                success = self._send_pushover_image(
                    image_path,
                    "Additional order image",
                )

                if not success:
                    additional_images_sent = False

            return additional_images_sent

        except requests.exceptions.Timeout:
            print(
                "Pushover failed: request timed out."
            )
            return False

        except requests.exceptions.ConnectionError:
            print(
                "Pushover failed: could not connect "
                "to Pushover."
            )
            return False

        except requests.exceptions.RequestException as exc:
            print(
                f"Pushover failed: network error: {exc}"
            )
            return False

        except OSError as exc:
            print(
                f"Pushover failed: image/file error: {exc}"
            )
            return False

        except Exception as exc:
            print(
                f"Pushover failed: unexpected error: {exc}"
            )
            return False

    def _send_pushover_image(
        self,
        image_path: Path,
        message: str,
    ) -> bool:
        """
        Send one additional image as a separate Pushover
        notification.
        """

        if not self._is_valid_image_path(image_path):
            print(
                f"Pushover image not found: {image_path}"
            )
            return False

        try:
            mime_type = self._get_image_mime_type(
                image_path
            )

            with open(
                image_path,
                "rb",
            ) as image_file:

                response = requests.post(
                    self.pushover_url,
                    data={
                        "token": self.pushover_api_token,
                        "user": self.pushover_user_key,
                        "title": "📸 ORDER IMAGE",
                        "message": message,
                        "attachment_type": mime_type,
                    },
                    files={
                        "attachment": (
                            image_path.name,
                            image_file,
                            mime_type,
                        )
                    },
                    timeout=30,
                )

            response_data = self._safe_response_json(
                response
            )

            if (
                response.status_code == 200
                and response_data
                and response_data.get("status") == 1
            ):
                print(
                    "Pushover image sent successfully: "
                    f"{image_path.name}"
                )
                return True

            print(
                "Pushover image failed: "
                f"HTTP {response.status_code} - "
                f"{response.text}"
            )
            return False

        except requests.exceptions.Timeout:
            print(
                "Pushover image failed: request timed out."
            )
            return False

        except requests.exceptions.ConnectionError:
            print(
                "Pushover image failed: "
                "could not connect to Pushover."
            )
            return False

        except requests.exceptions.RequestException as exc:
            print(
                f"Pushover image failed: network error: {exc}"
            )
            return False

        except OSError as exc:
            print(
                f"Pushover image failed: file error: {exc}"
            )
            return False

        except Exception as exc:
            print(
                f"Pushover image failed: unexpected error: {exc}"
            )
            return False

    # =============================================================
    # Email
    # =============================================================

    def send_emails(
        self,
        email_list: List[str],
        email_body: str,
        image_paths: Optional[List[Path]] = None,
    ) -> bool:
        """
        Send an order email with food images attached.

        Returns:
            True if the SMTP connection succeeds and every
            recipient receives the message successfully.
        """

        if (
            not self.email
            or not self.email_password
        ):
            print(
                "Email failed: email credentials not configured."
            )
            return False

        if not email_list:
            print(
                "Email failed: no recipient email addresses configured."
            )
            return False

        # ---------------------------------------------------------
        # Clean and validate recipient list
        # ---------------------------------------------------------

        cleaned_emails = []

        for email in email_list:

            if not isinstance(email, str):
                continue

            email = email.strip()

            if email:
                cleaned_emails.append(email)

        if not cleaned_emails:
            print(
                "Email failed: no valid recipient email addresses."
            )
            return False

        image_paths = image_paths or []

        valid_image_paths = [
            path
            for path in image_paths
            if self._is_valid_image_path(path)
        ]

        successful_recipients = 0

        try:

            with smtplib.SMTP(
                self.smtp_address,
                self.smtp_port,
                timeout=30,
            ) as connection:

                connection.ehlo()
                connection.starttls()
                connection.ehlo()

                connection.login(
                    self.email,
                    self.email_password,
                )

                for recipient in cleaned_emails:

                    message = EmailMessage()

                    message["From"] = self.email
                    message["To"] = recipient
                    message["Subject"] = (
                        "New Delivery Order!"
                    )

                    message.set_content(email_body)

                    # -------------------------------------------------
                    # Attach all available food images
                    # -------------------------------------------------

                    for image_path in valid_image_paths:

                        mime_type = self._get_image_mime_type(
                            image_path
                        )

                        maintype, subtype = mime_type.split(
                            "/",
                            1,
                        )

                        try:

                            with open(
                                image_path,
                                "rb",
                            ) as image_file:

                                image_data = (
                                    image_file.read()
                                )

                            message.add_attachment(
                                image_data,
                                maintype=maintype,
                                subtype=subtype,
                                filename=image_path.name,
                            )

                        except OSError as exc:

                            print(
                                "Email attachment skipped: "
                                f"{image_path} - {exc}"
                            )

                    connection.send_message(message)

                    successful_recipients += 1

                    print(
                        f"Email sent to: {recipient}"
                    )

            return (
                successful_recipients
                == len(cleaned_emails)
            )

        except smtplib.SMTPAuthenticationError:
            print(
                "Email failed: SMTP authentication failed. "
                "Check MANAGER_EMAIL and "
                "MANAGER_EMAIL_PASSWORD."
            )
            return False

        except smtplib.SMTPConnectError:
            print(
                "Email failed: could not connect to "
                "the SMTP server."
            )
            return False

        except smtplib.SMTPException as exc:
            print(
                f"Email failed: SMTP error: {exc}"
            )
            return False

        except OSError as exc:
            print(
                f"Email failed: file/system error: {exc}"
            )
            return False

        except Exception as exc:
            print(
                f"Email failed: unexpected error: {exc}"
            )
            return False

    # =============================================================
    # Existing application entry point
    # =============================================================

    def notify_owner_with_whatsapp_images(
        self,
        order_details: str,
        customer_info: Dict[str, Any],
        total_amount: float,
        image_references: List[Any],
    ) -> Dict[str, Any]:
        """
        Existing application entry point.

        The method name is intentionally preserved so the existing
        Streamlit application does not need to be changed.

        Notifications are sent through:
            - Pushover
            - SMTP email

        Returns:
            {
                "pushover": bool,
                "email": bool,
                "images_found": int
            }
        """

        customer_info = (
            customer_info
            if isinstance(customer_info, dict)
            else {}
        )

        image_references = (
            image_references
            if isinstance(image_references, list)
            else []
        )

        # ---------------------------------------------------------
        # Resolve image references
        # ---------------------------------------------------------

        actual_image_paths: List[Path] = []

        for image_reference in image_references:

            image_path = self._get_local_image_path(
                image_reference
            )

            if image_path:

                actual_image_paths.append(
                    image_path
                )

                print(
                    f"✅ Found image: {image_path}"
                )

            else:

                print(
                    f"❌ Image not found: "
                    f"{image_reference}"
                )

        # ---------------------------------------------------------
        # Base notification
        # ---------------------------------------------------------

        customer_name = customer_info.get(
            "name",
            "Not provided",
        )

        customer_phone = customer_info.get(
            "phone",
            "Not provided",
        )

        customer_address = customer_info.get(
            "address",
            "Not provided",
        )

        base_message = f"""
🚨 NEW CUSTOMER ORDER 🚨

CUSTOMER DETAILS:
Name: {customer_name}
Phone: {customer_phone}
Address: {customer_address}

ORDER TOTAL: ₦{total_amount:,.2f}

ORDER DETAILS:
{order_details}

ACTION REQUIRED:
Please prepare this order immediately!
""".strip()

        if actual_image_paths:

            base_message += (
                "\n\nORDER IMAGES: "
                f"{len(actual_image_paths)} "
                "image(s) attached."
            )

        # =========================================================
        # Pushover
        # =========================================================

        pushover_sent = self.send_pushover(
            base_message,
            actual_image_paths,
        )

        # =========================================================
        # Email
        # =========================================================

        owner_emails = os.environ.get(
            "OWNER_EMAILS",
            "",
        ).split(",")

        owner_emails = [
            email.strip()
            for email in owner_emails
            if email.strip()
        ]

        email_sent = False

        if owner_emails:

            email_body = f"""
NEW ORDER RECEIVED!

CUSTOMER INFORMATION:
Name: {customer_name}
Phone: {customer_phone}
Address: {customer_address}

ORDER TOTAL: ₦{total_amount:,.2f}

ORDER DETAILS:
{order_details}

ORDER CONTAINS:
{len(actual_image_paths)} food image(s) attached.

Please prepare the order immediately!
""".strip()

            email_sent = self.send_emails(
                owner_emails,
                email_body,
                actual_image_paths,
            )

        else:

            print(
                "Email notification skipped: "
                "OWNER_EMAILS is not configured."
            )

        # =========================================================
        # Return notification status
        # =========================================================

        return {
            "pushover": pushover_sent,
            "email": email_sent,
            "images_found": len(actual_image_paths),
        }