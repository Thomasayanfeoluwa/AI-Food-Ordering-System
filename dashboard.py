from src import prompt
import streamlit as st
import json
import os
import re
import uuid
import time
import base64
import requests
from pathlib import Path
from src.loader import order_request, messages
from src.notification import NotificationManager
from services.image_service import DishImageService
from services.payment_service import PaystackService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize services
notification_manager = NotificationManager()
image_service = DishImageService()
payment_service = PaystackService()

# Page configuration
st.set_page_config(
    page_title="DishDelivery Nigerian Restaurant",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 1rem;
    }
    .welcome-section {
        background-color: #FFF9F0;
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #FF6B35;
        margin-bottom: 2rem;
    }
    .order-confirmation {
        background-color: #E8F5E8;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
    }
    .payment-section {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2196F3;
        margin: 0.8rem 0;
    }
    .dish-image {
        border-radius: 10px;
        margin: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .customer-info-display {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin-top: 1rem;
    }
    .payment-amount {
        font-size: 1.6rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin: 0.8rem 0;
        padding: 0.8rem;
        background-color: #E8F5E9;
        border-radius: 8px;
        border: 2px solid #4CAF50;
    }
    .payment-instruction {
        font-size: 1.1rem;
        color: #1B5E20;
        font-weight: 600;
        margin: 0.8rem 0;
        padding: 0.6rem;
        background-color: #F1F8E9;
        border-radius: 6px;
        border-left: 4px solid #689F38;
    }
    .contact-info {
        font-size: 1rem;
        color: #0D47A1;
        font-weight: 600;
        margin: 0.8rem 0;
        padding: 0.6rem;
        background-color: #E3F2FD;
        border-radius: 6px;
        border-left: 4px solid #1976D2;
    }
    .delivery-time {
        font-size: 1rem;
        color: #E65100;
        font-weight: 600;
        margin: 0.8rem 0;
        padding: 0.6rem;
        background-color: #FFF3E0;
        border-radius: 6px;
        border-left: 4px solid #FF9800;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to load local images
def load_local_image(image_path):
    """Load local image and convert to base64 for display"""
    try:
        # Define the absolute path to the images folder
        # images_folder = images_folder = Path("images")
        images_folder = Path("images")
        
        # Extract the base filename without extension
        filename_without_ext = Path(image_path).stem
        original_path = Path(image_path)
        
        # If the exact path exists, use it
        if original_path.exists():
            image_path_obj = original_path
        elif (images_folder / original_path.name).exists():
            image_path_obj = images_folder / original_path.name
        else:
            # Try different extensions
            # possible_extensions = ['.jpg', '.jpeg', '.png', '.jpeg']
            possible_extensions = ['.jpg', '.jpeg', '.png']
            image_path_obj = None
            
            for ext in possible_extensions:
                test_path = images_folder / f"{filename_without_ext}{ext}"
                if test_path.exists():
                    image_path_obj = test_path
                    break
            
            if image_path_obj is None:
                st.error(f"Image not found: {filename_without_ext} (tried: {', '.join(possible_extensions)})")
                return None
        
        if image_path_obj.exists():
            with open(image_path_obj, "rb") as f:
                image_bytes = f.read()
            
            # Determine MIME type based on file extension
            if image_path_obj.suffix.lower() == '.png':
                mime_type = "image/png"
            else:
                mime_type = "image/jpeg"
            
            image_base64 = base64.b64encode(image_bytes).decode()
            return f"data:{mime_type};base64,{image_base64}"
        else:
            st.error(f"Image not found: {image_path_obj}")
            return None
    except Exception as e:
        st.error(f"Error loading image {image_path}: {str(e)}")
        return None

# Initialize session state
def initialize_session_state():
    # ---------------------------------------------------------
    # GLOBAL SESSION STATE
    # ---------------------------------------------------------

    if 'user_sessions' not in st.session_state:
        st.session_state.user_sessions = {}

    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = (
            f"user_{uuid.uuid4().hex}"
        )

    if 'conversation' not in st.session_state:
        st.session_state.conversation = messages.copy()

    if 'notification_sent' not in st.session_state:
        st.session_state.notification_sent = False

    if 'payment_initialized' not in st.session_state:
        st.session_state.payment_initialized = False

    if 'payment_verified' not in st.session_state:
        st.session_state.payment_verified = False

    if 'payment_reference' not in st.session_state:
        st.session_state.payment_reference = None

    if 'pending_order' not in st.session_state:
        st.session_state.pending_order = None

    if 'customer_info' not in st.session_state:
        st.session_state.customer_info = {
            'name': '',
            'phone': '',
            'address': '',
            'email': ''
        }

    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False

    if 'customer_info_updated' not in st.session_state:
        st.session_state.customer_info_updated = False

    # ---------------------------------------------------------
    # ENSURE THE CURRENT USER SESSION EXISTS
    # ---------------------------------------------------------

    user_id = st.session_state.current_session_id

    if user_id not in st.session_state.user_sessions:
        st.session_state.user_sessions[user_id] = {
            'name': None,
            'phone': None,
            'address': None,
            'email': None,

            'order_status': 'ORDER_BUILDING',

            'payment_initialized': False,
            'payment_verified': False,

            'payment_reference': None,
            'pending_order': None,

            'notification_sent': False
        }

# More flexible order confirmation detection
def is_final_confirmation(response):
    """
    FLEXIBLE check for FINAL order confirmation
    """
    response_upper = response.upper()
    
    # Must contain ORDER CONFIRMED or similar confirmation
    if not any(phrase in response_upper for phrase in ["ORDER CONFIRMED", "ORDER CONFIRMATION", "CONFIRMED"]):
        return False
    
    # Must NOT contain any phrases asking for more information
    exclusion_phrases = [
        "please provide", "not provided", "is this correct?", 
        "can you provide", "i need", "let me get", "confirm again",
        "would you like", "do you have", "can you please", "let me know"
    ]
    
    response_lower = response.lower()
    for phrase in exclusion_phrases:
        if phrase in response_lower:
            return False
    
    # Must contain customer information indicators
    customer_indicators = ["customer information", "name:", "phone:", "address:"]
    if not any(indicator in response_lower for indicator in customer_indicators):
        return False
    
    # Must contain total amount (flexible matching)
    total_patterns = [r"total.*₦", r"₦.*total", r"amount.*₦", r"₦\s*[\d,]+"]
    for pattern in total_patterns:
        if re.search(pattern, response_lower):
            return True
    
    return False

def extract_customer_info_from_response(response):
    """Extract customer details from LLM response"""
    customer_info = {
        'name': None,
        'phone': None,
        'address': None,
        'email': None
    }
    
    lines = response.split('\n')
    for line in lines:
        line_lower = line.lower()
        
        # Look for name
        if 'name:' in line_lower and 'customer' not in line_lower:
            name_parts = line.split(':')
            if len(name_parts) > 1:
                name = name_parts[1].strip()
                if name and name not in ['(please provide your name)', 'not provided']:
                    customer_info['name'] = name
        
        # Look for phone
        if 'phone:' in line_lower:
            phone_parts = line.split(':')
            if len(phone_parts) > 1:
                phone_str = phone_parts[1].strip()
                # Extract Nigerian phone numbers
                phone_match = re.search(r'(\+?234[789][01]\d{8}|0[789][01]\d{8}|\d{11})', phone_str)
                if phone_match:
                    customer_info['phone'] = phone_match.group()
                elif phone_str and phone_str not in ['(please provide your phone number)', 'not provided']:
                    customer_info['phone'] = phone_str
        
        # Look for address
        if 'address:' in line_lower:
            address_parts = line.split(':')
            if len(address_parts) > 1:
                address = address_parts[1].strip()
                if address and address not in ['(please provide your address)', 'not provided', 'delivery']:
                    customer_info['address'] = address
        
        # Look for email
        if 'email:' in line_lower:
            email_parts = line.split(':')
            if len(email_parts) > 1:
                email = email_parts[1].strip()
                if email and '@' in email:
                    customer_info['email'] = email
    
    return customer_info
# def extract_total_amount(response):
#     """Extract the FINAL ORDER TOTAL amount - PRIORITIZE ORDER TOTAL"""
#     total_amount = 0.0
    
#     # Strategy 1: Look specifically for "ORDER TOTAL" first (highest priority)
#     order_total_patterns = [
#         r'ORDER TOTAL.*₦\s*([\d,]+\.?\d*)',
#         r'💰 ORDER TOTAL.*₦\s*([\d,]+\.?\d*)',
#         r'total.*₦\s*([\d,]+\.?\d*).*order',
#         r'final total.*₦\s*([\d,]+\.?\d*)',
#     ]
    
#     for pattern in order_total_patterns:
#         matches = re.findall(pattern, response, re.IGNORECASE | re.DOTALL)
#         if matches:
#             try:
#                 total_amount = float(matches[0].replace(',', ''))
#                 st.sidebar.success(f"✅ ORDER TOTAL extracted: ₦{total_amount:,.2f}")
#                 return total_amount
#             except ValueError:
#                 continue
    
#     # Strategy 2: Look for amounts in the last lines (where totals usually are)
#     lines = response.split('\n')
#     lines.reverse()  # Start from the bottom where totals usually are
    
#     for line in lines:
#         line_lower = line.lower()
#         if any(keyword in line_lower for keyword in ['order total', 'total', 'final amount', '💰']):
#             amounts = re.findall(r'₦\s*([\d,]+\.?\d*)', line)
#             if amounts:
#                 try:
#                     total_amount = float(amounts[-1].replace(',', ''))  # Take the last amount in the line
#                     st.sidebar.success(f"✅ Bottom-up total extracted: ₦{total_amount:,.2f}")
#                     return total_amount
#                 except ValueError:
#                     continue
    
#     # Strategy 3: Fallback to original pattern matching
#     patterns = [
#         r'₦\s*([\d,]+\.?\d*)',
#         r'total.*₦\s*([\d,]+\.?\d*)',
#     ]
    
#     # Find ALL amounts and take the LARGEST one (most likely the total)
#     all_amounts = []
#     for pattern in patterns:
#         matches = re.findall(pattern, response, re.IGNORECASE | re.DOTALL)
#         for match in matches:
#             try:
#                 amount = float(match.replace(',', ''))
#                 if amount >= 1000:  # Reasonable minimum for food orders
#                     all_amounts.append(amount)
#             except ValueError:
#                 continue
    
#     if all_amounts:
#         total_amount = max(all_amounts)  # Take the largest amount
#         st.sidebar.info(f"ℹ️ Used largest amount: ₦{total_amount:,.2f}")
    
#     if total_amount == 0.0:
#         st.sidebar.error("❌ Could not extract total amount")
#     else:
#         st.sidebar.success(f"🎯 Final amount for Paystack: ₦{total_amount:,.2f}")
    
#     return total_amount

def extract_total_amount(response):
    """
    Extract the final order total only from an explicit
    ORDER TOTAL / FINAL TOTAL field.

    Do not use largest-amount guessing for payments.
    """

    patterns = [
        r'ORDER\s+TOTAL\s*[:\-]?\s*₦\s*([\d,]+(?:\.\d{1,2})?)',
        r'FINAL\s+TOTAL\s*[:\-]?\s*₦\s*([\d,]+(?:\.\d{1,2})?)',
        r'TOTAL\s+AMOUNT\s*[:\-]?\s*₦\s*([\d,]+(?:\.\d{1,2})?)',
    ]

    for pattern in patterns:
        matches = re.findall(
            pattern,
            response,
            re.IGNORECASE
        )

        if matches:
            try:
                amount = float(
                    matches[-1].replace(',', '')
                )

                if amount > 0:
                    return amount

            except (ValueError, TypeError):
                continue

    return 0.0


def extract_with_patterns(text, patterns):
    """Extract amount using given patterns"""
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            try:
                amount = float(match.replace(',', ''))
                if amount > 0:
                    return amount
            except ValueError:
                continue
    return 0.0

def find_largest_amount(text):
    """Find all amounts and return the largest"""
    amounts = []
    # Find all number patterns
    number_patterns = [
        r'₦\s*([\d,]+\.?\d*)',
        r'([\d,]+\.?\d{2})\s*(?:₦|NGN|naira)?',
    ]
    
    for pattern in number_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                amount = float(match.replace(',', ''))
                if 1000 <= amount <= 50000:  # Reasonable range for food orders
                    amounts.append(amount)
            except ValueError:
                continue
    
    return max(amounts) if amounts else 0.0

def manual_amount_extraction(text):
    """Last resort: manual parsing"""
    lines = text.split('\n')
    for line in lines:
        if 'total' in line:
            # Look for numbers in this line
            numbers = re.findall(r'[\d,]+\.?\d*', line)
            for num_str in numbers:
                try:
                    amount = float(num_str.replace(',', ''))
                    if amount > 1000:  # Reasonable minimum
                        return amount
                except ValueError:
                    continue
    return 0.0

def format_customer_info(customer_session):
    """Format customer information for notifications"""
    return {
        'name': customer_session.get('name', 'Not provided'),
        'phone': customer_session.get('phone', 'Not provided'),
        'address': customer_session.get('address', 'Not provided'),
        'email': customer_session.get('email', 'Not provided')
    }

def initiate_paystack_payment_direct(email, amount, reference, metadata=None):
    """Direct Paystack API call with email validation"""
    try:
        # EMAIL VALIDATION AND FALLBACK
        if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            # Generate valid fallback email
            email = f"customer_{int(time.time())}@dishdelivery.ng"
            st.sidebar.info(f"🔄 Using fallback email: {email}")
        
        secret_key = os.environ.get("PAYSTACK_SECRET_KEY")
        if not secret_key:
            return {"status": False, "message": "Paystack secret key not configured"}
        
        url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }
        
        # Convert amount to kobo - ADDED DEBUG LOGGING
        amount_in_kobo = int(amount * 100)
        
        # DEBUG: Log the amount conversion to verify correct amount is sent
        st.sidebar.write(f"💰 Amount Conversion Debug:")
        st.sidebar.write(f"   Original: ₦{amount:,.2f}")
        st.sidebar.write(f"   To Kobo: {amount_in_kobo} kobo")
        st.sidebar.write(f"   Reference: {reference}")
        
        payload = {
            "email": email,
            "amount": amount_in_kobo,
            "reference": reference,
            "currency": "NGN",
            "metadata": metadata or {},
            "channels": ["card", "bank", "ussd", "qr", "mobile_money", "bank_transfer"]
        }
        
        st.sidebar.write(f"🔄 Sending payment request for: {email}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_data = response.json()
        
        st.sidebar.write(f"📡 Paystack API Status: {response.status_code}")
        
        if response.status_code == 200 and response_data.get('status'):
            return {
                "status": True,
                "message": response_data.get('message', 'Payment initialized successfully'),
                "data": response_data.get('data', {})
            }
        else:
            error_msg = response_data.get('message', 'Failed to initialize payment')
            st.sidebar.error(f"❌ Paystack Error: {error_msg}")
            return {
                "status": False,
                "message": error_msg,
                "data": {}
            }
            
    except Exception as e:
        st.sidebar.error(f"💥 Payment Error: {str(e)}")
        return {
            "status": False,
            "message": f"Payment error: {str(e)}",
            "data": {}
        }

# Main application
def main():
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">DishDelivery Nigerian Restaurant 🍽️🇳🇬</h1>', unsafe_allow_html=True)
    
    # Welcome section (only show once)
    if not st.session_state.conversation or len(st.session_state.conversation) <= 2:
        with st.container():
            st.markdown('<div class="welcome-section">', unsafe_allow_html=True)
            
            st.subheader("How you dey! Welcome to DishDelivery")
            st.write("Your number one spot for authentic Nigerian cuisine!")
            
            st.markdown("***")
            
            st.subheader("How to Order")
            
            st.write("1. **Browse our menu** - Tell me what you'd like to eat")
            st.write("2. **Provide delivery details** - Name, phone, address")
            st.write("3. **Get confirmation** - We'll calculate your total")
            st.write("4. **Complete payment** - Secure payment via Paystack")
            st.write("5. **Receive your order** - Delivered to your doorstep!")
            
            st.markdown("*Minimum delivery: ₦1,500*")
            st.markdown("**Ready to order?** Just tell me what you'd like!")
            
            st.subheader("🍛 Popular Dishes:")
            st.write("• Jollof Rice with Chicken")
            st.write("• Pounded Yam with Egusi Soup")
            st.write("• Fried Rice with Beef")
            st.write("• Suya with drinks")
            
            st.markdown('</div>', unsafe_allow_html=True)

    # Display conversation history
    for msg in st.session_state.conversation:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(msg["content"])

    # Sidebar with customer information
    with st.sidebar:
        st.header("Your Order Information")
        
        # Display current customer information
        st.subheader("Current Information")
        if (st.session_state.customer_info['name'] or 
            st.session_state.customer_info['phone'] or 
            st.session_state.customer_info['address']):
            
            st.markdown('<div class="customer-info-display">', unsafe_allow_html=True)
            if st.session_state.customer_info['name']:
                st.write(f"**Name:** {st.session_state.customer_info['name']}")
            if st.session_state.customer_info['phone']:
                st.write(f"**Phone:** {st.session_state.customer_info['phone']}")
            if st.session_state.customer_info['address']:
                st.write(f"**Address:** {st.session_state.customer_info['address']}")
            if st.session_state.customer_info['email']:
                st.write(f"**Email:** {st.session_state.customer_info['email']}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No customer information provided yet.")
        
        # Customer info form - UPDATE SECTION
        st.subheader("Update Your Details")
        
        # Use individual widgets instead of form for better state management
        name = st.text_input("Full Name", value=st.session_state.customer_info['name'], key="name_input")
        phone = st.text_input("Phone Number", value=st.session_state.customer_info['phone'], key="phone_input")
        address = st.text_area("Delivery Address", value=st.session_state.customer_info['address'], key="address_input")
        email = st.text_input("Email (optional)", value=st.session_state.customer_info['email'], key="email_input")
        
        if st.button("Update Information", key="update_button"):
            # Update session state with form values
            st.session_state.customer_info = {
                'name': name.strip() if name else '',
                'phone': phone.strip() if phone else '',
                'address': address.strip() if address else '',
                'email': email.strip() if email else ''
            }
            # Also update user session
            user_id = st.session_state.current_session_id
            if user_id in st.session_state.user_sessions:
                # Convert empty strings to None for consistency
                updated_info = {
                    'name': name.strip() if name else None,
                    'phone': phone.strip() if phone else None,
                    'address': address.strip() if address else None,
                    'email': email.strip() if email else None
                }
                st.session_state.user_sessions[user_id].update(updated_info)
            
            st.session_state.customer_info_updated = True
            st.success("✅ Information updated successfully!")
            st.rerun()

    # Display current order status
    st.subheader("Order Status")

    user_id = st.session_state.current_session_id
    user_session = st.session_state.user_sessions[user_id]

    order_status = user_session.get(
        'order_status',
        'ORDER_BUILDING'
    )

    if order_status == 'ORDER_BUILDING':
        st.info("🔄 Order in progress...")

    elif order_status == 'ORDER_CONFIRMED':
        st.info("✅ Order confirmed — preparing payment.")

    elif order_status == 'PAYMENT_INITIALIZED':
        st.info(
            "💳 Payment link created — awaiting payment verification."
        )

    elif order_status == 'PAYMENT_VERIFIED':
        st.success(
            "✅ Payment verified — order is ready to be sent to the restaurant."
        )

    elif order_status == 'NOTIFICATION_SENT':
        st.success(
            "✅ Payment confirmed — order sent to restaurant."
        )

    elif order_status == 'COMPLETE':
        st.success(
            "✅ Order complete."
        )
        
        # Quick actions
        st.subheader("Quick Actions")

        if st.button("Start New Order", key="start_new_order"):

            # ---------------------------------------------------------
            # CREATE A NEW ORDER SESSION
            # ---------------------------------------------------------

            new_session_id = f"user_{uuid.uuid4().hex}"

            st.session_state.current_session_id = new_session_id

            st.session_state.user_sessions[new_session_id] = {
                'name': None,
                'phone': None,
                'address': None,
                'email': None,

                'order_status': 'ORDER_BUILDING',

                'payment_initialized': False,
                'payment_verified': False,

                'payment_reference': None,
                'pending_order': None,

                'notification_sent': False
            }

            # ---------------------------------------------------------
            # RESET GLOBAL STATE FOR THE NEW ORDER
            # ---------------------------------------------------------

            st.session_state.conversation = messages.copy()

            st.session_state.notification_sent = False
            st.session_state.payment_initialized = False
            st.session_state.payment_verified = False
            st.session_state.payment_reference = None
            st.session_state.pending_order = None

            st.session_state.customer_info = {
                'name': '',
                'phone': '',
                'address': '',
                'email': ''
            }

            st.session_state.form_submitted = False
            st.session_state.customer_info_updated = False

            st.rerun()

    # User input
    if prompt := st.chat_input("Tell me what you'd like to order..."):
        # Add user message to conversation
        st.session_state.conversation.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Process user message and update customer info
        user_id = st.session_state.current_session_id
        user_session = st.session_state.user_sessions[user_id]
        
        # Extract customer info from user message
        phone_match = re.search(r'(\+?234|0)[789][01]\d{8}', prompt)
        if phone_match:
            st.session_state.user_sessions[user_id]['phone'] = phone_match.group()
        
        # Look for address indicators
        if any(keyword in prompt.lower() for keyword in ['address', 'location', 'street', 'house', 'deliver']):
            st.session_state.user_sessions[user_id]['address'] = prompt
        
        # Look for name
        if 'my name is' in prompt.lower():
            name_match = re.search(r'my name is (\w+ \w+)', prompt.lower())
            if name_match:
                st.session_state.user_sessions[user_id]['name'] = name_match.group(1).title()
        
        # Also extract using new method for comprehensive coverage
        user_info = extract_customer_info_from_response(prompt)
        for key in ['name', 'phone', 'address', 'email']:
            if user_info[key] and not st.session_state.user_sessions[user_id][key]:
                st.session_state.user_sessions[user_id][key] = user_info[key]
        
        # Get LLM response
        with st.spinner("Processing your order..."):
            response = order_request(st.session_state.conversation)
            total_amount = extract_total_amount(response)
        # Process dish images exactly once for this assistant response.
        dish_images = []

        if any(
            keyword in response.lower()
            for keyword in [
                'menu',
                'dish',
                'soup',
                'rice',
                'chicken',
                'beef',
                'fish',
                'plantain',
                'drink'
            ]
        ):
            dish_images = image_service.get_images_for_order(response)
        # Add assistant response to conversation
        st.session_state.conversation.append({
            "role": "assistant",
            "content": response
        })

        # Extract customer information
        current_customer_info = extract_customer_info_from_response(response)

        for key in ['name', 'phone', 'address', 'email']:
            if (
                current_customer_info[key]
                and not user_session[key]
            ):
                user_session[key] = current_customer_info[key]

        # Sync customer information to sidebar
        st.session_state.customer_info = {
            'name': user_session.get('name') or '',
            'phone': user_session.get('phone') or '',
            'address': user_session.get('address') or '',
            'email': user_session.get('email') or ''
        }

        # Display assistant response
        with st.chat_message("assistant"):
            st.write(response)

            if dish_images:
                cols = st.columns(len(dish_images))

                for idx, img_url in enumerate(dish_images):
                    with cols[idx]:
                        if img_url.startswith(('http://', 'https://')):
                            dish_name = "Dish"

                            if '/' in img_url:
                                url_parts = img_url.split('/')
                                last_part = url_parts[-1]

                                if '.' in last_part:
                                    dish_name = (
                                        Path(last_part)
                                        .stem
                                        .replace('_', ' ')
                                        .title()
                                    )

                            st.image(
                                img_url,
                                caption=dish_name,
                                width="stretch"
                            )

                        else:
                            local_image_data = load_local_image(img_url)

                            if local_image_data:
                                dish_name = (
                                    Path(img_url)
                                    .stem
                                    .replace('_', ' ')
                                    .title()
                                )

                                st.image(
                                    local_image_data,
                                    caption=dish_name
                                )
                
        # DEBUG: Check if order confirmation is detected
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔧 Debug Info")

        st.sidebar.write(
            f"Final Confirmation: {is_final_confirmation(response)}"
        )

        st.sidebar.write(
            f"Total Amount: ₦{total_amount:,.2f}"
        )

        st.sidebar.write(
            f"Phone Provided: {user_session['phone'] is not None}"
        )

        st.sidebar.write(
            f"Notification Sent: {user_session['notification_sent']}"
        )

        st.sidebar.write(
            f"Payment Initialized: {user_session['payment_initialized']}"
        )

        st.sidebar.write(
            f"Payment Verified: {user_session['payment_verified']}"
        )

        st.sidebar.write(
            f"Order Status: {user_session['order_status']}"
        )


        # Check if this is the FINAL confirmation
        # if (is_final_confirmation(response) and
        #     not st.session_state.user_sessions[user_id]['notification_sent'] and
        #     st.session_state.user_sessions[user_id]['phone'] is not None

            # total_amount = extract_total_amount(response)

        if (
            is_final_confirmation(response)
            and user_session['order_status'] == 'ORDER_BUILDING'
            and not user_session['payment_initialized']
            and user_session['phone'] is not None
        ):

            if total_amount > 0:

                # ---------------------------------------------------------
                # STEP 1 — CONFIRM THE ORDER INTERNALLY
                # ---------------------------------------------------------

                user_session['order_status'] = 'ORDER_CONFIRMED'

                # ---------------------------------------------------------
                # STEP 2 — CREATE ONE REFERENCE FOR THIS ORDER
                # ---------------------------------------------------------

                payment_reference = (
                    user_session.get('payment_reference')
                    or f"DD-{uuid.uuid4().hex}"
                )

                user_session['payment_reference'] = payment_reference
                st.session_state.payment_reference = payment_reference

                # Get order images
                # order_images = image_service.get_images_for_order(response)

                # Convert image references to local paths
                local_image_paths = []

                for img_url in dish_images:
                    if img_url.startswith(('http://', 'https://')):
                        continue

                    img_path = Path(img_url)

                    if img_path.exists():
                        local_image_paths.append(img_path)
                    else:
                        images_folder = Path("images")
                        possible_path = images_folder / Path(img_url).name

                        if possible_path.exists():
                            local_image_paths.append(possible_path)

                # Store the pending order BEFORE creating payment
                # pending_order = {
                #     "customer_info": customer_info.copy(),
                #     "total_amount": total_amount,
                #     "order_summary": response,
                #     "image_paths": [str(path) for path in local_image_paths],
                #     "payment_reference": payment_reference
                # }
                customer_info = {
                    "name": user_session.get("name"),
                    "phone": user_session.get("phone"),
                    "address": user_session.get("address"),
                    "email": user_session.get("email")
                }

                pending_order = {
                    "customer_info": customer_info,
                    "total_amount": total_amount,
                    "order_summary": response,
                    "image_paths": [
                        str(path)
                        for path in local_image_paths
                    ],
                    "payment_reference": payment_reference
                }
                st.session_state.pending_order = pending_order
                st.session_state.payment_reference = payment_reference

                st.session_state.user_sessions[user_id]['pending_order'] = pending_order
                st.session_state.user_sessions[user_id]['payment_reference'] = payment_reference

                # ---------------------------------------------------------
                # INITIALIZE PAYSTACK PAYMENT
                # ---------------------------------------------------------

                st.sidebar.info("🔄 Creating secure Paystack payment...")

            #     payment_response = payment_service.initiate_payment(
            #         email=customer_info.get('email') or 'customer@example.com',
            #         amount=total_amount,
            #         reference=payment_reference,
            #         metadata={
            #             "customer_name": customer_info.get('name'),
            #             "phone": customer_info.get('phone'),
            #             "address": customer_info.get('address'),
            #             "order_reference": payment_reference
            #         }
            #     )

            #     st.sidebar.write(
            #         f"Payment Response Status: {payment_response.get('status')}"
            #     )

            #     if payment_response.get('status'):

            #         payment_url = payment_response['data']['authorization_url']

            #         st.session_state.payment_processed = True
            #         st.session_state.user_sessions[user_id]['payment_processed'] = True

            #         st.sidebar.success("✅ Payment link created.")

            #         st.markdown(f"""
            #         <div class="payment-section">
            #             <h3>💰 Payment Required</h3>

            #             <div class="payment-amount">
            #                 Your Order Total: ₦{total_amount:,.2f}
            #             </div>

            #             <div class="payment-instruction">
            #                 Please complete your payment using the secure Paystack link below.
            #             </div>

            #             <p>
            #                 <a href="{payment_url}"
            #                 target="_blank"
            #                 style="background-color: #4CAF50;
            #                         color: white;
            #                         padding: 12px 24px;
            #                         text-decoration: none;
            #                         border-radius: 6px;
            #                         display: inline-block;
            #                         font-size: 16px;
            #                         font-weight: bold;">
            #                     💳 Pay Now with Paystack
            #                 </a>
            #             </p>

            #             <div class="payment-instruction">
            #                 After completing payment, return here and click
            #                 <strong>Verify Payment</strong>.
            #             </div>

            #             <div class="delivery-time">
            #                 ⏰ Delivery time: 30–45 minutes after payment confirmation
            #             </div>
            #         </div>
            #         """, unsafe_allow_html=True)

            #         st.success(f"Payment link created for ₦{total_amount:,.2f}")

            #     else:

            #         error_msg = payment_response.get(
            #             'message',
            #             'Unknown payment error'
            #         )

            #         st.error(f"Payment system error: {error_msg}")

            # else:
            #     st.error("❌ Could not determine a valid order total.")

                payment_response = payment_service.initiate_payment(
                    email=customer_info.get('email') or f"{payment_reference}@dishdelivery.ng",
                    amount=total_amount,
                    reference=payment_reference,
                    metadata={
                        "customer_name": customer_info.get("name"),
                        "phone": customer_info.get("phone"),
                        "address": customer_info.get("address"),
                        "order_reference": payment_reference
                    }
                )

                if payment_response.get("status"):

                    payment_data = payment_response.get("data", {})
                    payment_url = payment_data.get("authorization_url")

                    if not payment_url:
                        user_session['order_status'] = 'ORDER_BUILDING'

                        st.error(
                            "❌ Payment was initialized but Paystack "
                            "did not return a payment URL. Please try again."
                        )
                    else:
                        user_session['payment_initialized'] = True
                        user_session['payment_verified'] = False
                        user_session['payment_reference'] = payment_reference
                        user_session['order_status'] = 'PAYMENT_INITIALIZED'

                        st.session_state.payment_initialized = True
                        st.session_state.payment_verified = False
                        st.session_state.payment_reference = payment_reference

                        st.sidebar.success(
                            "✅ Payment link created."
                        )

                        st.markdown(
                            f"""
                            <div class="payment-section">
                                <h3>💰 Payment Required</h3>

                                <div class="payment-amount">
                                    Your Order Total: ₦{total_amount:,.2f}
                                </div>

                                <div class="payment-instruction">
                                    Please complete your payment using the
                                    secure Paystack link below.
                                </div>

                                <p>
                                    <a href="{payment_url}"
                                    target="_blank"
                                    style="
                                        background-color: #4CAF50;
                                        color: white;
                                        padding: 12px 24px;
                                        text-decoration: none;
                                        border-radius: 6px;
                                        display: inline-block;
                                        font-size: 16px;
                                        font-weight: bold;
                                    ">
                                        💳 Pay Now with Paystack
                                    </a>
                                </p>

                                <div class="payment-instruction">
                                    After completing payment, return here and
                                    click <strong>Verify Payment</strong>.
                                </div>

                                <div class="delivery-time">
                                    ⏰ Delivery time: 30–45 minutes after
                                    payment confirmation
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                else:
                    user_session['order_status'] = 'ORDER_BUILDING'

                    st.error(
                        f"❌ Payment system error: "
                        f"{payment_response.get('message', 'Unknown error')}"
                    )

    # ---------------------------------------------------------
    # PAYMENT VERIFICATION
    # ---------------------------------------------------------

    pending_order = st.session_state.get("pending_order")
    payment_reference = st.session_state.get("payment_reference")
    user_id = st.session_state.current_session_id
    user_session = st.session_state.user_sessions[user_id]

    if (
        pending_order
        and payment_reference
        and user_session['payment_initialized']
        and not user_session['payment_verified']
    ):

        st.subheader("💳 Payment Verification")

        st.info(
            "After completing payment on Paystack, "
            "return here and verify your payment."
        )

        if st.button("🔍 Verify Payment", type="primary"):

            with st.spinner("Verifying payment with Paystack..."):

                verification = payment_service.verify_payment(
                    payment_reference
                )

    
    # ---------------------------------------------------------
    # RESTAURANT NOTIFICATION
    # ---------------------------------------------------------

    pending_order = st.session_state.get("pending_order")

    if (
        pending_order
        and user_session['payment_verified']
        and not user_session['notification_sent']
    ):

        st.subheader("📨 Restaurant Notification")

        st.info(
            "Payment has been verified. "
            "The order is ready to be sent to the restaurant."
        )

        if st.button(
            "📤 Send Order to Restaurant",
            key="send_order_notification"
        ):

            customer_info = pending_order["customer_info"]
            total_amount = pending_order["total_amount"]
            order_summary = pending_order["order_summary"]

            local_image_paths = [
                Path(path)
                for path in pending_order["image_paths"]
                if Path(path).exists()
            ]

            with st.spinner(
                "Sending order details to the restaurant..."
            ):

                notification_result = (
                    notification_manager
                    .notify_owner_with_whatsapp_images(
                        order_details=order_summary,
                        customer_info=customer_info,
                        total_amount=total_amount,
                        image_references=local_image_paths
                    )
                )

            st.sidebar.write("📊 Notification Results:")

            st.sidebar.write(
                "Pushover: "
                f"{'✅' if notification_result.get('pushover') else '❌'}"
            )

            st.sidebar.write(
                "Email: "
                f"{'✅' if notification_result.get('email') else '❌'}"
            )

            st.sidebar.write(
                "Images Sent: "
                f"{notification_result.get('images_found', 0)}"
            )

            if (
                notification_result.get('pushover')
                or notification_result.get('email')
            ):

                user_session['notification_sent'] = True
                user_session['order_status'] = 'NOTIFICATION_SENT'

                st.session_state.notification_sent = True

                st.success(
                    "✅ Order successfully sent to the restaurant."
                )

            else:

                # Keep payment_verified as True.
                # Do not ask the customer to pay again.
                user_session['payment_verified'] = True
                user_session['order_status'] = 'PAYMENT_VERIFIED'
                st.session_state['payment_verified'] = True
                st.error(
                    "❌ Payment is verified, but the restaurant "
                    "notification failed. You can retry sending it."
                )


            # -------------------------------------------------
            # STEP 1 — API RESPONSE VALIDATION
            # -------------------------------------------------

            if not verification.get("status"):

                st.warning(
                    "⏳ Paystack verification could not confirm "
                    "this transaction yet. "
                    f"{verification.get('message', '')}"
                )

            else:

                transaction_data = (
                    verification.get("data") or {}
                )

                # -------------------------------------------------
                # STEP 2 — TRANSACTION STATUS
                # -------------------------------------------------

                transaction_status = transaction_data.get(
                    "status"
                )

                if transaction_status != "success":

                    st.warning(
                        "⏳ Payment has not been successfully "
                        "completed yet. "
                        f"Paystack status: "
                        f"{transaction_status or 'unknown'}."
                    )

                else:

                    # -------------------------------------------------
                    # STEP 3 — REFERENCE VALIDATION
                    # -------------------------------------------------

                    transaction_reference = (
                        transaction_data.get("reference")
                    )

                    if transaction_reference != payment_reference:

                        st.error(
                            "❌ Payment reference does not "
                            "match this order."
                        )

                    else:

                        # -------------------------------------------------
                        # STEP 4 — AMOUNT VALIDATION
                        # -------------------------------------------------

                        paid_amount_kobo = transaction_data.get(
                            "amount"
                        )

                        if not isinstance(
                            paid_amount_kobo,
                            (int, float)
                        ):

                            st.error(
                                "❌ Paystack returned an invalid "
                                "payment amount."
                            )

                        else:

                            paid_amount = (
                                paid_amount_kobo / 100
                            )

                            expected_amount = float(
                                pending_order["total_amount"]
                            )

                            if (
                                abs(
                                    paid_amount
                                    - expected_amount
                                )
                                > 0.01
                            ):

                                st.error(
                                    f"❌ Payment amount mismatch. "
                                    f"Expected "
                                    f"₦{expected_amount:,.2f}, "
                                    f"received "
                                    f"₦{paid_amount:,.2f}."
                                )

                            else:

                                # -------------------------------------------------
                                # STEP 5 — CURRENCY VALIDATION
                                # -------------------------------------------------

                                transaction_currency = (
                                    transaction_data.get(
                                        "currency"
                                    )
                                )

                                if transaction_currency != "NGN":

                                    st.error(
                                        "❌ Unexpected payment "
                                        f"currency: "
                                        f"{transaction_currency}"
                                    )

                                else:

                                    # -------------------------------------------------
                                    # STEP 6 — PAYMENT IS VERIFIED
                                    # -------------------------------------------------

                                    user_session[
                                        'payment_verified'
                                    ] = True

                                    user_session[
                                        'order_status'
                                    ] = 'PAYMENT_VERIFIED'

                                    st.session_state[
                                        'payment_verified'
                                    ] = True

                                    # # -------------------------------------------------
                                    # # STEP 7 — RESTAURANT NOTIFICATION
                                    # # -------------------------------------------------

                                    # customer_info = (
                                    #     pending_order[
                                    #         "customer_info"
                                    #     ]
                                    # )

                                    # total_amount = (
                                    #     pending_order[
                                    #         "total_amount"
                                    #     ]
                                    # )

                                    # order_summary = (
                                    #     pending_order[
                                    #         "order_summary"
                                    #     ]
                                    # )

                                    # local_image_paths = [
                                    #     Path(path)
                                    #     for path in pending_order[
                                    #         "image_paths"
                                    #     ]
                                    #     if Path(path).exists()
                                    # ]

                                    # st.info(
                                    #     "🔄 Payment verified. "
                                    #     "Sending order to "
                                    #     "the restaurant..."
                                    # )

                                    # notification_result = (
                                    #     notification_manager
                                    #     .notify_owner_with_whatsapp_images(
                                    #         order_details=order_summary,
                                    #         customer_info=customer_info,
                                    #         total_amount=total_amount,
                                    #         image_references=local_image_paths
                                    #     )
                                    # )

                                    # st.sidebar.write(
                                    #     "📊 Notification Results:"
                                    # )

                                    # st.sidebar.write(
                                    #     "Pushover: "
                                    #     f"{'✅' if notification_result.get('pushover') else '❌'}"
                                    # )

                                    # st.sidebar.write(
                                    #     "Email: "
                                    #     f"{'✅' if notification_result.get('email') else '❌'}"
                                    # )

                                    # st.sidebar.write(
                                    #     "Images Sent: "
                                    #     f"{notification_result.get('images_found', 0)}"
                                    # )

                                    # # -------------------------------------------------
                                    # # STEP 8 — NOTIFICATION RESULT
                                    # # -------------------------------------------------

                                    # if (
                                    #     notification_result.get(
                                    #         'pushover'
                                    #     )
                                    #     or
                                    #     notification_result.get(
                                    #         'email'
                                    #     )
                                    # ):

                                    #     user_session[
                                    #         'notification_sent'
                                    #     ] = True

                                    #     user_session[
                                    #         'order_status'
                                    #     ] = 'NOTIFICATION_SENT'

                                    #     st.session_state[
                                    #         'notification_sent'
                                    #     ] = True

                                    #     st.success(
                                    #         "✅ Payment confirmed — "
                                    #         "order sent to restaurant."
                                    #     )

                                    # else:

                                    #     st.error(
                                    #         "❌ Payment was verified, "
                                    #         "but the restaurant "
                                    #         "notification could not "
                                    #         "be sent."
                                    #     )



if __name__ == "__main__":
    main()
