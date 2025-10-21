import streamlit as st
import os
import datetime
import logging
import json
from typing import Dict, List, Any

# Import Gradient LLM
from langchain_gradient import ChatGradient
from config import Config

# Import our booking functions
from main import book_ignite_class, check_ignite_class

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Streamlit App Setup ---
st.set_page_config(page_title="Bay Club Booking Assistant", page_icon="🏋️‍♀️")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_credentials" not in st.session_state:
    # Initialize with values from Config if available
    st.session_state.user_credentials = {
        "username": Config.BAY_CLUB_USERNAME or "", 
        "password": Config.BAY_CLUB_PASSWORD or ""
    }
if "booking_history" not in st.session_state:
    st.session_state.booking_history = []
if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
if "last_mentioned_date" not in st.session_state:
    st.session_state.last_mentioned_date = None

# Initialize Gradient LLM
@st.cache_resource
def get_llm():
    """Initialize and cache the Gradient LLM"""
    if not Config.DIGITALOCEAN_INFERENCE_KEY:
        st.error("Please set DIGITALOCEAN_INFERENCE_KEY in your .env file or environment variables")
        return None
    
    return ChatGradient(
        model="llama3.3-70b-instruct",
        api_key=Config.DIGITALOCEAN_INFERENCE_KEY
    )

def get_system_prompt():
    """Get the system prompt for the AI assistant"""
    return """You are a helpful Bay Club booking assistant. You help users book Ignite classes at Bay Club San Francisco.

You have access to these tools:
1. check_ignite_class(username, password, date, headless=True) - Check available classes for a specific date
2. book_ignite_class(username, password, date, time, meridiem, headless=True) - Book a class for a specific date and time

When users ask about:
- "Check classes for [date]" or "What classes are available on [date]" → Use check_ignite_class()
- "Book a class for [date] at [time]" or "Book me a [time] class on [date]" → Use book_ignite_class()
- "Show me available times" → Use check_ignite_class() for today or ask for a specific date

Date format: YYYY-MM-DD (e.g., "2025-10-22")
Time format: HH:MM (e.g., "7:00", "6:30", "8:00")
Meridiem: "AM" or "PM"

Always be helpful, friendly, and informative. When using tools, explain what you're doing and show the results clearly.

Remember: Bay Club Ignite classes are offered every day for 50 minutes."""

def parse_user_intent(user_input: str) -> dict:
    """Parse user input to determine intent and extract parameters"""
    import re
    
    user_input_lower = user_input.lower()
    
    # Helper function to extract date from input
    def extract_date_from_input(input_text):
        # Extract date
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', input_text)
        if date_match:
            return date_match.group(1)
        
        # Check for relative dates
        if "today" in input_text:
            return datetime.datetime.now().strftime("%Y-%m-%d")
        elif "tomorrow" in input_text:
            return (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        elif "thursday" in input_text:
            # Find next Thursday
            today = datetime.datetime.now()
            days_ahead = 3 - today.weekday()  # Thursday is 3
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "friday" in input_text:
            # Find next Friday
            today = datetime.datetime.now()
            days_ahead = 4 - today.weekday()  # Friday is 4
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "saturday" in input_text:
            # Find next Saturday
            today = datetime.datetime.now()
            days_ahead = 5 - today.weekday()  # Saturday is 5
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "sunday" in input_text:
            # Find next Sunday
            today = datetime.datetime.now()
            days_ahead = 6 - today.weekday()  # Sunday is 6
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "monday" in input_text:
            # Find next Monday
            today = datetime.datetime.now()
            days_ahead = 0 - today.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "tuesday" in input_text:
            # Find next Tuesday
            today = datetime.datetime.now()
            days_ahead = 1 - today.weekday()  # Tuesday is 1
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "wednesday" in input_text:
            # Find next Wednesday
            today = datetime.datetime.now()
            days_ahead = 2 - today.weekday()  # Wednesday is 2
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        else:
            return None
    
    # Check for availability checking intent
    if any(word in user_input_lower for word in ["check", "available", "classes", "times", "schedule"]):
        date = extract_date_from_input(user_input)
        if date:
            # Store the date for future reference
            st.session_state.last_mentioned_date = date
        else:
            # Use last mentioned date if available, otherwise default to today
            date = st.session_state.last_mentioned_date or datetime.datetime.now().strftime("%Y-%m-%d")
        
        return {
            "action": "check_availability",
            "date": date
        }
    
    # Check for booking intent
    elif any(word in user_input_lower for word in ["book", "reserve", "sign up"]):
        # Extract date
        date = extract_date_from_input(user_input)
        if date:
            # Store the date for future reference
            st.session_state.last_mentioned_date = date
        else:
            # Use last mentioned date if available, otherwise default to today
            date = st.session_state.last_mentioned_date or datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Extract time - handle both "6am" and "6:00am" formats
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', user_input_lower)
        if time_match:
            hour = time_match.group(1)
            minutes = time_match.group(2) if time_match.group(2) else "00"
            meridiem = time_match.group(3).upper()
            time = f"{hour}:{minutes}"
        else:
            # Fallback to colon format
            time_match = re.search(r'(\d{1,2}:\d{2})', user_input)
            time = time_match.group(1) if time_match else "7:00"
            meridiem = "PM" if "pm" in user_input_lower else "AM"
        
        return {
            "action": "book_class",
            "date": date,
            "time": time,
            "meridiem": meridiem
        }
    
    # Default to general conversation
    return {
        "action": "conversation"
    }

def process_user_input(user_input: str) -> str:
    """Process user input and generate response using the LLM or tools"""
    
    # First, try to parse intent and use tools if appropriate
    intent = parse_user_intent(user_input)
    
    if intent["action"] == "check_availability":
        return check_availability_for_date(intent["date"])
    elif intent["action"] == "book_class":
        return book_class_for_date_time(intent["date"], intent["time"], intent["meridiem"])
    
    # For general conversation, use the LLM
    llm = get_llm()
    if not llm:
        return "Error: LLM not available. Please check your API key."
    
    # Get conversation context
    conversation_history = []
    for message in st.session_state.messages[-10:]:  # Last 10 messages for context
        conversation_history.append({
            "role": message["role"],
            "content": message["content"]
        })
    
    # Prepare the prompt
    system_prompt = get_system_prompt()
    
    # Add booking system context
    booking_context = f"""
Booking System Status:
- Username: {st.session_state.user_credentials['username'] or 'Not set'}
- Password: {'Set' if st.session_state.user_credentials['password'] else 'Not set'}
- Booking History: {len(st.session_state.booking_history)} bookings
- Current Date: {st.session_state.current_date}
- Last Mentioned Date: {st.session_state.last_mentioned_date or 'None'}

Available Tools:
- check_ignite_class(username, password, date, headless=True)
- book_ignite_class(username, password, date, time, meridiem, headless=True)

You can use these tools by calling them directly in your response. For example:
- "Let me check availability for today" → call check_ignite_class()
- "I'll book that class for you" → call book_ignite_class()

IMPORTANT: If the user mentions a date in one message and then asks to book a class in the next message without specifying a date, use the last mentioned date from the conversation context.
"""
    
    # Create the full prompt
    messages = [
        ("system", system_prompt + "\n\n" + booking_context),
        ("human", f"User: {user_input}")
    ]
    
    # Add conversation history
    for msg in conversation_history:
        if msg["role"] == "user":
            messages.append(("human", msg["content"]))
        else:
            messages.append(("assistant", msg["content"]))
    
    try:
        # Get response from LLM
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"Error processing user input: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

def check_availability_for_date(date: str) -> str:
    """Check availability for a specific date"""
    try:
        if not st.session_state.user_credentials["username"]:
            return "Please set your Bay Club credentials first."
        
        # Use our new function directly
        result = check_ignite_class(
            st.session_state.user_credentials["username"],
            st.session_state.user_credentials["password"],
            date,
            headless=True
        )
        
        if result["status"] == "success":
            if result["available_times"]:
                result_text = f"📅 Available classes on {date}:\n"
                result_text += f"Found {result['ignite_studios_found']} Ignite Studios across {result['time_slots_found']} time slots:\n"
                for time in result["available_times"]:
                    result_text += f"  ✅ {time} - IGNITE (available)\n"
                return result_text
            else:
                return f"📅 No available classes found for {date}"
        elif result["status"] == "no_classes":
            return f"📅 No Ignite classes found for {date}"
        else:
            return f"Error: {result.get('error', 'Unknown error occurred')}"
    except Exception as e:
        return f"Error checking availability: {str(e)}"

def book_class_for_date_time(date: str, time: str, meridiem: str = "AM") -> str:
    """Book a class for a specific date and time"""
    try:
        if not st.session_state.user_credentials["username"]:
            return "Please set your Bay Club credentials first."
        
        # Use our new function directly
        success = book_ignite_class(
            st.session_state.user_credentials["username"],
            st.session_state.user_credentials["password"],
            date,
            time,
            meridiem,
            headless=True
        )
        
        if success:
            # Add to booking history
            booking_record = {
                "date": date,
                "time": time,
                "meridiem": meridiem,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "booked"
            }
            st.session_state.booking_history.append(booking_record)
            return f"✅ Successfully booked class for {date} at {time} {meridiem}!"
        else:
            return f"❌ Failed to book class for {date} at {time} {meridiem}"
    except Exception as e:
        return f"Error booking class: {str(e)}"

def find_next_available() -> str:
    """Find and book the next available class"""
    try:
        if not st.session_state.user_credentials["username"]:
            return "Please set your Bay Club credentials first."
        
        # Use subprocess to avoid Streamlit context issues
        cmd = [
            "python", "booking_runner.py",
            "--action", "find_next_available",
            "--username", st.session_state.user_credentials["username"],
            "--password", st.session_state.user_credentials["password"]
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data["success"]:
                result_data = data["data"]
                if result_data["success"]:
                    # Add to booking history
                    booking_record = {
                        "date": result_data["date"],
                        "time": result_data["time"],
                        "meridiem": "AM",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "status": result_data["status"]
                    }
                    st.session_state.booking_history.append(booking_record)
                    
                    status_emoji = "✅" if result_data["status"] == "booked" else "⏳"
                    return f"{status_emoji} Found and {result_data['status']} class for {result_data['date']} at {result_data['time']}"
                else:
                    return f"❌ {result_data['message']}"
            else:
                return f"Error: {data['error']}"
        else:
            return f"Error running find next available: {result.stderr}"
    except Exception as e:
        return f"Error finding next available: {str(e)}"

def show_weekly_schedule() -> str:
    """Show the weekly schedule"""
    try:
        if not st.session_state.user_credentials["username"]:
            return "Please set your Bay Club credentials first."
        
        # Use subprocess to avoid Streamlit context issues
        cmd = [
            "python", "booking_runner.py",
            "--action", "show_weekly_schedule",
            "--username", st.session_state.user_credentials["username"],
            "--password", st.session_state.user_credentials["password"]
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data["success"]:
                week_schedule = data["data"]
                result_text = "📊 Weekly Schedule:\n"
                for date, day_info in week_schedule["days"].items():
                    result_text += f"\n{date}:\n"
                    if day_info["total_available"] > 0:
                        for class_info in day_info["classes"]:
                            status_emoji = "✅" if class_info["status"] == "available" else "⏳"
                            result_text += f"  {status_emoji} {class_info['time']} - {class_info['class_type']} ({class_info['status']})\n"
                    else:
                        result_text += "  No classes available\n"
                return result_text
            else:
                return f"Error: {data['error']}"
        else:
            return f"Error running weekly schedule: {result.stderr}"
    except Exception as e:
        return f"Error getting weekly schedule: {str(e)}"

# --- Main App Layout ---
st.title("🏋️‍♀️ Bay Club Booking Assistant")
st.markdown("Your AI-powered assistant for booking Ignite classes at Bay Club San Francisco")

# Sidebar for credentials and settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Show config status
    st.subheader("Configuration Status")
    config_status = Config.get_credentials_status()
    for key, value in config_status.items():
        st.write(f"{key.replace('_', ' ').title()}: {value}")
    
    # Credentials section
    st.subheader("Bay Club Credentials")
    st.write("Credentials are loaded from .env file. You can override them here:")
    
    # Use current session state values as defaults
    default_username = st.session_state.user_credentials["username"]
    default_password = st.session_state.user_credentials["password"]
    
    username = st.text_input("Username", value=default_username)
    password = st.text_input("Password", type="password", value=default_password)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Save Credentials"):
            st.session_state.user_credentials = {"username": username, "password": password}
            st.success("Credentials saved!")
    
    with col2:
        if st.button("Reload from .env"):
            st.session_state.user_credentials = {
                "username": Config.BAY_CLUB_USERNAME or "", 
                "password": Config.BAY_CLUB_PASSWORD or ""
            }
            st.success("Credentials reloaded from .env file!")
            st.rerun()
    
    # Booking history
    st.subheader("📚 Booking History")
    if st.session_state.booking_history:
        for i, booking in enumerate(st.session_state.booking_history[-5:]):  # Show last 5
            st.write(f"**{i+1}.** {booking['date']} at {booking['time']} {booking['meridiem']}")
            st.write(f"   Status: {booking['status']}")
    else:
        st.write("No bookings yet")
    
    # Clear history button
    if st.button("Clear History"):
        st.session_state.booking_history = []
        st.success("History cleared!")

# Quick action buttons
st.subheader("🚀 Quick Actions")

col1, col2 = st.columns(2)

with col1:
    if st.button("📅 Check Today's Classes"):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        result = check_availability_for_date(today)
        st.session_state.messages.append({"role": "assistant", "content": result})
        st.rerun()

with col2:
    if st.button("🔍 Find Next Available"):
        result = find_next_available()
        st.session_state.messages.append({"role": "assistant", "content": result})
        st.rerun()

col3, col4 = st.columns(2)

with col3:
    if st.button("📊 Show Weekly Schedule"):
        result = show_weekly_schedule()
        st.session_state.messages.append({"role": "assistant", "content": result})
        st.rerun()

with col4:
    if st.button("🗓️ Check Tomorrow"):
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        result = check_availability_for_date(tomorrow)
        st.session_state.messages.append({"role": "assistant", "content": result})
        st.rerun()

# Manual booking section
st.subheader("🎯 Manual Booking")
col1, col2, col3 = st.columns(3)

with col1:
    booking_date = st.date_input("Select Date", value=datetime.datetime.now().date())

with col2:
    booking_time = st.selectbox("Select Time", ["6:00", "6:30", "7:00", "7:30", "8:00", "8:30"])

with col3:
    booking_meridiem = st.selectbox("AM/PM", ["AM", "PM"])

if st.button("Book Class"):
    date_str = booking_date.strftime("%Y-%m-%d")
    result = book_class_for_date_time(date_str, booking_time, booking_meridiem)
    st.session_state.messages.append({"role": "assistant", "content": result})
    st.rerun()

# Main chat interface
st.subheader("💬 Chat with your booking assistant")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about class availability or book a class..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process the input and get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = process_user_input(prompt)
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.markdown("💡 **Tips:** Use the quick action buttons above for common tasks, or chat with me for more complex requests!")