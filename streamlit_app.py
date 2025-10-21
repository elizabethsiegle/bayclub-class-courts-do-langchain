import streamlit as st
import os
import datetime
import logging
import json
import subprocess
from typing import Dict, List, Any

# Import Gradient LLM
from langchain_gradient import ChatGradient
from config import Config

# Import our booking functions
from main import book_ignite_class, book_any_class, check_ignite_class

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Streamlit App Setup ---
st.set_page_config(
    page_title="Bay Club SF Class Booking Assistant", 
    page_icon="🏋️‍♀️",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Custom CSS to hide settings and add sticky footer
st.markdown("""
<style>
    /* Hide the settings menu */
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    .stApp > header {visibility: hidden;}
    
    /* Hide the hamburger menu */
    #MainMenu {visibility: hidden;}
    
    /* Custom sticky footer */
    .main .block-container {
        padding-bottom: 5rem;
    }
    
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0e1117;
        color: white;
        text-align: center;
        padding: 10px 0;
        border-top: 1px solid #262730;
        z-index: 1000;
        font-size: 14px;
    }
    
    .footer a {
        color: #ff6b6b;
        text-decoration: none;
        font-weight: 500;
    }
    
    .footer a:hover {
        color: #ff5252;
        text-decoration: underline;
    }
    
    /* Ensure content doesn't get hidden behind footer */
    .stApp {
        margin-bottom: 60px;
    }
</style>
""", unsafe_allow_html=True)

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
if "last_class_list" not in st.session_state:
    st.session_state.last_class_list = []

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
    return """You are a helpful Bay Club booking assistant. You help users book classes at Bay Club San Francisco.

You have access to these tools:
1. check_ignite_class(username, password, date, headless=True) - Check available classes for a specific date (includes ALL class types: Ignite, Pilates, Riide, Cardio Hip Hop, Yoga, and more)
2. book_any_class(username, password, class_name, date, time, meridiem, headless=True) - Book ANY class type for a specific date and time

When users ask about:
- "Check classes for [date]" or "What classes are available on [date]" → Use check_ignite_class()
- "Book a [class name] class for [date] at [time]" → Use book_any_class() with the specific class name
- "Book me a [time] class on [date]" → Use book_any_class() (defaults to Ignite if no class type specified)
- "Show me available times" → Use check_ignite_class() for today or ask for a specific date
- "What Pilates/Riide/Cardio Hip Hop classes are available?" → Use check_ignite_class()

Supported class types: Ignite, Pilates, Riide, Cardio Hip Hop, Yoga, Spin, Barre, and more

Date format: YYYY-MM-DD (e.g., "2025-10-22")
Time format: HH:MM (e.g., "7:00", "6:30", "8:00")
Meridiem: "AM" or "PM"

Always be helpful, friendly, and informative. When using tools, explain what you're doing and show the results clearly.

Remember: Bay Club offers many different class types. Classes are typically 50 minutes long. You can book any class type, not just Ignite!"""

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
        # Check if booking by number (e.g., "book #2" or "book 2")
        number_match = re.search(r'(?:book|reserve)\s*#?(\d+)', user_input_lower)
        if number_match:
            class_number = int(number_match.group(1))
            return {
                "action": "book_by_number",
                "class_number": class_number
            }
        
        # Extract date
        date = extract_date_from_input(user_input)
        if date:
            # Store the date for future reference
            st.session_state.last_mentioned_date = date
        else:
            # Use last mentioned date if available, otherwise default to today
            date = st.session_state.last_mentioned_date or datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Extract class name - expanded list to include all Bay Club classes
        class_name = None
        class_types = [
            "pilates mat", "pilates", "riide", "riise", "cardio hip hop", "cardio", 
            "yoga", "vinyasa", "therapeutic yoga", "alignment", "spin", "barre", 
            "ignite", "lift", "fiight", "zumba", "bodypump", "aqua", "choreodance",
            "powerlifting", "gunz bunz", "trx", "rooftop", "roll release restore",
            "forever fit", "align", "stretch"
        ]
        for cls_type in class_types:
            if cls_type in user_input_lower:
                class_name = cls_type.upper()
                break
        
        # If no class name found, try to extract it from the context
        if not class_name:
            # Look for capitalized words that might be class names
            words = user_input.split()
            for word in words:
                if word.isupper() and len(word) > 2:
                    class_name = word
                    break
        
        # Default to None if still not found (will need to ask user)
        if not class_name:
            class_name = None
        
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
            "meridiem": meridiem,
            "class_name": class_name
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
    elif intent["action"] == "book_by_number":
        return book_class_by_number(intent["class_number"])
    elif intent["action"] == "book_class":
        class_name = intent.get("class_name")
        if not class_name:
            return "❓ I couldn't identify which class you want to book. Please specify the class name (e.g., 'book Pilates at 7am' or 'book #2')"
        return book_class_for_date_time(intent["date"], intent["time"], intent["meridiem"], class_name)
    
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
                # Store the class list in session state for numbered booking
                st.session_state.last_class_list = result["available_times"]
                st.session_state.last_mentioned_date = date
                
                class_types = result.get('class_types', [])
                result_text = f"### 📅 Classes for {date}\n\n"
                result_text += f"**Found {result['total_classes_found']} classes** across **{len(class_types)} types**\n\n"
                result_text += f"**Class Types:** {', '.join(sorted(class_types))}\n\n"
                result_text += "---\n\n"
                result_text += "**Schedule (sorted by time):**\n\n"
                
                for i, class_info in enumerate(result["available_times"], 1):
                    # Parse availability status to show appropriate emoji
                    if "(Available)" in class_info:
                        emoji = "✅"
                    elif "(Waitlist)" in class_info:
                        emoji = "⏳"
                    else:
                        emoji = "ℹ️"
                    result_text += f"{i}. {emoji} {class_info}\n"
                
                result_text += f"\n💡 *Tip: You can book by number! Just say \"book #2\" or \"book 5\"*"
                return result_text
            else:
                st.session_state.last_class_list = []
                return f"📅 No available classes found for {date}"
        elif result["status"] == "no_classes":
            st.session_state.last_class_list = []
            return f"📅 No classes found for {date}"
        else:
            return f"Error: {result.get('error', 'Unknown error occurred')}"
    except Exception as e:
        return f"Error checking availability: {str(e)}"

def book_class_by_number(class_number: int) -> str:
    """Book a class by its number from the last displayed list"""
    try:
        if not st.session_state.user_credentials["username"]:
            return "Please set your Bay Club credentials first."
        
        if not st.session_state.last_class_list:
            return "❓ Please check available classes first before booking by number."
        
        if class_number < 1 or class_number > len(st.session_state.last_class_list):
            return f"❌ Invalid class number. Please choose a number between 1 and {len(st.session_state.last_class_list)}."
        
        # Get the class info from the list (1-indexed)
        class_info = st.session_state.last_class_list[class_number - 1]
        
        # Parse the class info string: "7:00 AM - LiFT with Unknown (Available)"
        import re
        match = re.match(r'(\d{1,2}:\d{2})\s*(AM|PM)\s*-\s*([^(]+?)(?:\s+with\s+[^(]+)?\s*\(', class_info)
        
        if not match:
            return f"❌ Error parsing class information: {class_info}"
        
        time_str = match.group(1)
        meridiem = match.group(2)
        class_name = match.group(3).strip()
        date = st.session_state.last_mentioned_date or datetime.datetime.now().strftime("%Y-%m-%d")
        
        logging.info(f"Booking class #{class_number}: {class_name} at {time_str} {meridiem} on {date}")
        
        # Book the class
        return book_class_for_date_time(date, time_str, meridiem, class_name)
        
    except Exception as e:
        return f"Error booking class by number: {str(e)}"

def book_class_for_date_time(date: str, time: str, meridiem: str = "AM", class_name: str = "IGNITE") -> str:
    """Book a class for a specific date and time"""
    try:
        if not st.session_state.user_credentials["username"]:
            return "Please set your Bay Club credentials first."
        
        # Use the new general booking function
        success = book_any_class(
            st.session_state.user_credentials["username"],
            st.session_state.user_credentials["password"],
            class_name,
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
                "class_name": class_name,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "booked"
            }
            st.session_state.booking_history.append(booking_record)
            return f"✅ Successfully booked **{class_name}** class for {date} at {time} {meridiem}!"
        else:
            return f"❌ Failed to book {class_name} class for {date} at {time} {meridiem}"
    except Exception as e:
        return f"Error booking class: {str(e)}"

# --- Main App Layout ---
st.title("🏋️‍♀️ Bay Club Booking Assistant")
st.markdown("Your AI-powered assistant for booking classes at Bay Club San Francisco (Ignite, Pilates, Riide, Cardio Hip Hop, and more)")

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
            class_name = booking.get('class_name', 'Class')
            st.write(f"**{i+1}.** {class_name} - {booking['date']} at {booking['time']} {booking['meridiem']}")
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
    if st.button("🗓️ Check Tomorrow"):
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        result = check_availability_for_date(tomorrow)
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

# Custom sticky footer
st.markdown("""
<div class="footer">
    made with <3 in sf | <a href="https://github.com/elizabethsiegle/bayclub-ignite-agent-do-langchain/tree/main" target="_blank">View on GitHub</a>
</div>
""", unsafe_allow_html=True)