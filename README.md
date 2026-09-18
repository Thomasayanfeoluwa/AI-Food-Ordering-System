# DishDelivery-OrderBot

An intelligent AI-powered Nigerian restaurant ordering system with real-time notifications and payment integration.

## 🚀 Features

- **AI-Powered Ordering**: Natural language processing for seamless order taking
- **Multi-Channel Notifications**: Real-time push notifications via Pushover and email alerts for new orders
- **Secure Payments**: Paystack integration with automatic payment verification
- **Image Attachments**: Professional dish photos automatically attached to restaurant notifications
- **Real-time Chat**: Interactive ordering via Streamlit web interface
- **Session Management**: Customer data and pending order tracking across conversations
- **Error Handling**: Robust error handling and payment state management

## 🔄 Data Flow

1. User Interaction → Streamlit Interface → Groq LLM Processing
2. Order Confirmation → Payment Link Generation → Paystack
3. Customer completes payment → Payment Verification Step
4. Successful Verification → Push Notifications (Pushover & Email with images) → Restaurant
5. Order Fulfillment → Customer Delivery

## 📁 Complete Project Structure

```
DishDelivery-OrderBot/
├── 📁 src/                          # Core application logic
│   ├── __init__.py
│   ├── notification.py              # Pushover & Email notifications (with image attachments)
│   ├── loader.py                    # Groq LLM integration and API handling
│   └── prompt.py                    # AI system instructions & complete menu
├── 📁 services/                     # External service integrations
│   ├── __init__.py
│   ├── image_service.py             # Dish image management and local file mapping
│   └── payment_service.py           # Paystack payment initialization and verification
├── 📁 images/                       # Local dish images
├── dashboard.py                     # Main Streamlit Web interface
├── app.py                           # Alternative Chainlit application entry point
├── .env                             # Environment variables (create this)
├── .env.example                     # Environment variables template
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🔧 Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| Frontend | Streamlit | Interactive chat interface |
| Backend | Python 3.10+ | Application logic |
| AI/LLM | Groq API (Llama 3) | Natural language order processing |
| Payments | Paystack API | Secure Nigerian payment processing |
| Notifications | Pushover API | Mobile/Desktop push alerts |
| Email | SMTP (Gmail) | Email notifications to owners |

## 🛠️ Installation & Setup

**Prerequisites**
- Python 3.10 or higher
- Groq API account (free tier available)
- Pushover account (for push notifications)
- Paystack account (test mode available)
- Gmail account (for email notifications)

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd DishDelivery-OrderBot

# Create virtual environment
conda create -n Carebot python=3.10 -y

# Activate virtual environment
# On Windows:
conda activate Carebot
# On macOS/Linux:
source activate Carebot

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Environment Configuration

Create a `.env` file in the root directory:

```bash
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Pushover Configuration
PUSHOVER_USER_KEY=your_pushover_user_key
PUSHOVER_API_TOKEN=your_pushover_application_token

# Email Configuration
EMAIL_PROVIDER_SMTP_ADDRESS=smtp.gmail.com
MANAGER_EMAIL=your_email@gmail.com
MANAGER_EMAIL_PASSWORD=your_app_password
OWNER_EMAILS=owner1@example.com,owner2@example.com

# Paystack Configuration
PAYSTACK_SECRET_KEY=sk_test_your_secret_key
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key
```

### Step 3: Obtain API Keys

**Groq API Key**
1. Visit Groq Cloud
2. Sign up for a free account
3. Generate an API key from the dashboard
4. Add to `.env` file

**Pushover Credentials**
1. Sign up at [Pushover](https://pushover.net/)
2. Copy your **User Key** from your dashboard.
3. Scroll down and create an **Application/API Token** to get your API Token.

**Paystack Keys**
1. Register at Paystack
2. Go to Settings → API Keys & Webhooks
3. Copy Test Secret Key and Test Public Key

**Gmail App Password**
1. Enable 2FA on your Gmail account
2. Generate an App Password for "Mail"
3. Use this password in `MANAGER_EMAIL_PASSWORD`

### Step 4: Run the Application

```bash
# Start the application
streamlit run dashboard.py
```

## 📋 Core Components Documentation

**dashboard.py**
Purpose: Orchestrates the entire order processing workflow, chat interface, payment initialization, and verification.

**notification.py**
Purpose: Securely dispatches parsed order details and actual food images to the restaurant owner via Pushover and Email right after the customer's payment is verified.

---

**Issues**: Create a GitHub issue for bugs
**Discussions**: Use GitHub discussions for questions
**Email**: Contact ayanfeoluwadegoke@gmail.com


![WhatsApp Image 2025-11-20 at 12 52 20_8aa6140d](https://github.com/user-attachments/assets/421c66e2-f3f4-4ba1-b62b-8354e045cbee)

![WhatsApp Image 2025-11-20 at 12 52 20_7dbe052c](https://github.com/user-attachments/assets/371384b6-798f-46ea-b2ba-e8ae7d9adad8)

<img width="1142" height="614" alt="Screenshot (122)" src="https://github.com/user-attachments/assets/82e030fe-2893-491b-abdb-2f9611916ea1" />
