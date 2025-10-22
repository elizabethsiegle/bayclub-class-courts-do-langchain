# Bay Club Ignite Class Booking Assistant

A comprehensive Python system for booking Ignite classes at Bay Club San Francisco, featuring an AI-powered Streamlit chat interface.

## Features

### Class Booking/Checking Tools
- **`book_any_class()`**: Books any class type at Bay Club San Francisco (Ignite, Pilates, Riide, etc.)
  - Supports variable date input (YYYY-MM-DD format)
  - Supports variable time input (7:00, 6:30, etc.)
  - Supports variable AM/PM selection
  - Supports any class name (Ignite, Pilates, Riide, Cardio Hip Hop, etc.)
- **`check_all_classes()`**: Checks available classes for a specific date (all types: Ignite, Pilates, Riide, etc.)
  - Returns available times and class information
  - Can check any date (past, present, or future)
  - Returns detailed status information
- Smart day selection (works for any day - Ignite classes run daily)
- Context manager for proper resource cleanup

### LLM Chat Assistant (Streamlit)
- Conversational AI interface using Gradient LLM
- **Direct tool integration**: Chat messages can trigger booking and checking functions
- **Natural language processing**: Understands phrases like "Check classes for today" or "Book a 7:00 AM class tomorrow"
- **Intent parsing**: Automatically detects when users want to check availability or book classes
- Memory and state management for booking history
- Real-time class availability and booking through chat interface
- Interactive weekly schedule viewing
- Credential management and booking history tracking

### Class Availability Checker
- Check class availability for specific dates and times
- Weekly schedule generation
- Real-time availability status (available/waitlist)

## Setup

1. Clone the repository and navigate to the directory:
```bash
cd langchain-gradient-bayclub
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

5. Set up your credentials by creating a `.env` file:
```bash
python config.py  # Creates sample .env file
# Then edit .env with your actual credentials
```

Or set environment variables directly:
```bash
export BAY_CLUB_USERNAME="your-username"
export BAY_CLUB_PASSWORD="your-password"
export DIGITALOCEAN_INFERENCE_KEY="your-api-key"
```

## 🎯 Usage

### Option 1: AI Chat Assistant (Recommended)

Launch the Streamlit chat interface:
```bash
python run_app.py
```

Or directly:
```bash
streamlit run streamlit_app.py
```

Then open your browser to `http://localhost:8501` and chat with the AI assistant!

**Example conversations:**
- "Check classes for today" → Automatically calls `check_all_classes()`
- "What classes are available tomorrow?" → Automatically calls `check_all_classes()`
- "Book me a 7:00 AM Ignite class for Wednesday" → Automatically calls `book_any_class()`
- "Book a Pilates class for 2025-10-22 at 6:30 AM" → Automatically calls `book_any_class()`
- "Show me available times for today" → Automatically calls `check_all_classes()`

**Natural Language Features:**
- Understands relative dates: "today", "tomorrow", "next week"
- Extracts times from text: "7:00", "6:30", "8:00"
- Detects AM/PM: "7:00 AM", "6:30 PM"
- Parses specific dates: "2025-10-22", "October 22nd"

### Option 2: Command Line Tools

**Basic booking and checking (updated functionality):**
```bash
# Run the main demo (checks classes for today and tomorrow)
python main.py

# Run example usage (shows function signatures and examples)
python example_usage.py
```

### Option 3: Programmatic Usage

```python
from main import book_any_class, check_all_classes
from config import Config

# Get credentials
username = Config.BAY_CLUB_USERNAME
password = Config.BAY_CLUB_PASSWORD

# Check classes for a specific date
result = check_all_classes(username, password, "2025-10-22", headless=True)
print(f"Available times: {result['available_times']}")

# Book a class for a specific date and time
success = book_any_class(username, password, "IGNITE", "2025-10-22", "7:00", "AM", headless=True)
if success:
    print("✅ Successfully booked class!")
```

## 📅 Date and Time Logic

The system now supports flexible date and time selection:

### Date Input
- **Format**: YYYY-MM-DD (e.g., "2025-10-22")
- **Default**: If no date provided, uses current day
- **Flexible**: Can book for any date (past, present, or future)

### Time Input
- **Format**: HH:MM (e.g., "7:00", "6:30", "8:00")
- **Default**: "7:00" if not specified
- **Meridiem**: "AM" or "PM" (default: "AM")

### Function Parameters
- `book_any_class(username, password, class_name, date=None, time="7:00", meridiem="AM", headless=False)`
- `check_all_classes(username, password, date=None, headless=False)`

## 🛠️ File Structure

```
langchain-gradient-bayclub/
├── streamlit_app.py          # AI chat interface
├── flexible_booking.py       # Advanced booking system
├── class_checker.py          # Availability checker
├── bayclub_booking.py        # Core booking class
├── main.py                   # Simple booking script
├── run_app.py               # App launcher
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root with:
```env
# Bay Club Credentials
BAY_CLUB_USERNAME=your_username_here
BAY_CLUB_PASSWORD=your_password_here

# Gradient API Key
DIGITALOCEAN_INFERENCE_KEY=your_gradient_api_key_here
```

Or set them as environment variables:
- `BAY_CLUB_USERNAME`: Your Bay Club username
- `BAY_CLUB_PASSWORD`: Your Bay Club password  
- `DIGITALOCEAN_INFERENCE_KEY`: Your Gradient API key (required for chat assistant)

### Quick Setup
Run `python config.py` to create a sample `.env` file, then edit it with your actual credentials.

## 🎨 Streamlit App Features

- **Chat Interface**: Natural language conversation with AI
- **Credential Management**: Secure storage of Bay Club login
- **Booking History**: Track all your bookings
- **Quick Actions**: One-click common tasks
- **Real-time Availability**: Live class availability checking
- **Memory**: Remembers conversation context and preferences

## 🚨 Error Handling

- If a class is full, the system automatically adds you to the waitlist
- Comprehensive logging shows what's happening at each step
- Automatic screenshot capture for debugging
- Graceful error handling with user-friendly messages

## 📋 Requirements

- Python 3.7+
- Playwright
- Streamlit
- LangChain Gradient
- Bay Club account credentials
- Gradient API key

## 📄 License

MIT License - see the header in the source files for details.
