# Bay Club Booking Assistant - Architecture Guide

## 🎯 What Does This App Do?

The Bay Club Booking Assistant is an AI-powered web application that automates class booking at Bay Club San Francisco. It can:

- **Search & Display** all available fitness classes (Ignite, Pilates, Riide, Cardio Hip Hop, Yoga, etc.)
- **Book Classes** by name and time or by number from a list
- **Natural Language Interface** - Users can chat naturally: "Check classes for Friday" or "Book #2"
- **Smart Matching** - Handles variations in class names (e.g., "LiFT" vs "LIFT")

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│                                                               │
│  ┌──────────────────────┐      ┌─────────────────────────┐ │
│  │  Streamlit Web App   │      │   Terminal CLI          │ │
│  │  (streamlit_app.py)  │      │   (main.py)             │ │
│  └──────────┬───────────┘      └──────────┬──────────────┘ │
└─────────────┼──────────────────────────────┼────────────────┘
              │                              │
              ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Main Functions (main.py)                            │   │
│  │  - book_ignite_class()                               │   │
│  │  - book_any_class()                                  │   │
│  │  - check_ignite_class()                              │   │
│  └──────────────────┬───────────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Browser Automation Layer                    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  IgniteBooking Class (bayclub_booking.py)            │   │
│  │  - login()                                           │   │
│  │  - select_location()                                 │   │
│  │  - select_day()                                      │   │
│  │  - search_all_classes()                              │   │
│  │  - book_class()                                      │   │
│  │  - book_ignite()                                     │   │
│  │  - confirm_ignite()                                  │   │
│  └──────────────────┬───────────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Services                           │
│                                                               │
│  ┌──────────────────┐    ┌──────────────────────────────┐   │
│  │  Playwright      │    │  Bay Club Website            │   │
│  │  (Browser        │───▶│  (bayclubconnect.com)        │   │
│  │   Automation)    │    │                              │   │
│  └──────────────────┘    └──────────────────────────────┘   │
│                                                               │
│  ┌──────────────────┐                                        │
│  │  Gradient LLM    │                                        │
│  │  (Natural        │                                        │
│  │   Language)      │                                        │
│  └──────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure & Responsibilities

### Core Files

| File | Purpose | Key Responsibilities |
|------|---------|---------------------|
| `bayclub_booking.py` | Browser automation | Web scraping, class detection, booking automation |
| `main.py` | Business logic | Orchestration, date handling, class filtering |
| `streamlit_app.py` | Web interface | UI, chat interface, session management |
| `config.py` | Configuration | Credentials, environment variables |

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Stores credentials (username, password, API keys) |
| `requirements.txt` | Python dependencies |
| `README.md` | User documentation |

---

## 🔄 How It Works: User Flow

### Flow 1: Checking Available Classes

```
User Input: "Check classes for Friday"
                │
                ▼
    ┌───────────────────────┐
    │ Streamlit parses      │
    │ intent (check_avail)  │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ call check_ignite_    │
    │ class(date="Friday")  │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ IgniteBooking:        │
    │ - login()             │
    │ - select_location()   │
    │ - select_day()        │
    │ - search_all_classes()│
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ Scrape webpage:       │
    │ - Find all classes    │
    │ - Extract times       │
    │ - Get instructor      │
    │ - Check availability  │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ Return sorted list:   │
    │ 1. 6:00 AM - LiFT     │
    │ 2. 7:00 AM - IGNITE   │
    │ 3. 8:00 AM - PILATES  │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ Display to user       │
    │ (formatted, numbered) │
    └───────────────────────┘
```

### Flow 2: Booking a Class

```
User Input: "Book #2"
                │
                ▼
    ┌───────────────────────┐
    │ Parse booking intent  │
    │ Extract: class_number │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ Look up class #2      │
    │ from session state    │
    │ (stored class list)   │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ Extract from list:    │
    │ - Class name: LiFT    │
    │ - Time: 6:30 AM       │
    │ - Date: Friday        │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ call book_any_class() │
    │ (class, date, time)   │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ IgniteBooking:        │
    │ - search_all_classes()│
    │ - Find matching class │
    │ - Click class element │
    │ - book_ignite()       │
    │ - confirm_ignite()    │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ Success! Return true  │
    │ Add to booking history│
    └───────────────────────┘
```

---

## 🔑 Key Technical Components

### 1. Browser Automation (Playwright)

**Why Playwright?**
- Modern, reliable browser automation
- Handles JavaScript-heavy websites
- Built-in waiting mechanisms
- Screenshot capability for debugging

**What it does:**
```python
# Example: Login to Bay Club
self.page.wait_for_selector("#username").fill(username)
self.page.wait_for_selector("#password").fill(password)
self.page.wait_for_selector("button[type='submit']").click()
```

### 2. Web Scraping Strategy

**Challenge:** Find ALL class types, not just one

**Solution:** Target the common HTML pattern
```html
<div class="size-16 text-uppercase">CARDIO HIP HOP</div>
```

**Implementation:**
```python
# Find all class name elements
class_elements = page.query_selector_all("div.size-16.text-uppercase")

# For each element, traverse up to find parent container
# Extract time, instructor, availability
```

### 3. Intelligent Class Matching

**Problem:** Class names have variations
- "LiFT" vs "LIFT"
- "iGNITE" vs "IGNITE"
- "CARDIO HIP HOP" vs "cardio"

**Solution:** Normalize and fuzzy match
```python
# Remove special characters, lowercase
name_norm = re.sub(r'[^a-z0-9\s]', '', class_name.lower())
cls_norm = re.sub(r'[^a-z0-9\s]', '', cls['class_name'].lower())

# Partial matching
if name_norm in cls_norm or cls_norm in name_norm:
    # Match found!
```

### 4. Time Parsing & Sorting

**Challenge:** Extract start time from ranges
- Input: "7:00 - 7:50 AM"
- Need: "7:00 AM"

**Solution:**
```python
# Extract START time from range
match = re.search(r'(\d{1,2}:\d{2})\s*-\s*\d{1,2}:\d{2}\s*(AM|PM)', text)
start_time = f"{match.group(1)} {match.group(2)}"

# Convert to 24-hour for sorting
if meridiem == 'PM' and hour != 12:
    hour += 12
```

### 5. Session State Management

**Streamlit Feature:** Persist data across interactions

```python
# Store last class list for numbered booking
st.session_state.last_class_list = result["available_times"]

# Later when user says "book #2"
class_info = st.session_state.last_class_list[1]  # 0-indexed
```

### 6. Natural Language Processing

**Using Gradient LLM:**
- Parse user intent
- Extract dates, times, class names
- Handle variations in phrasing

**Pattern Matching:**
```python
# Detect booking by number
if re.search(r'book\s*#?(\d+)', user_input):
    class_number = int(match.group(1))
```

---

## 🛠️ How to Build This (Step-by-Step)

### Phase 1: Setup & Authentication

**Goal:** Get logged into Bay Club website

1. **Install Playwright**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Create Browser Context Manager**
   ```python
   class IgniteBooking:
       def __enter__(self):
           self.playwright = sync_playwright().start()
           self.browser = self.playwright.chromium.launch()
           self.page = self.browser.new_page()
           return self
   ```

3. **Implement Login**
   - Find username/password selectors
   - Fill credentials
   - Click login button
   - Wait for page load

**Teaching Tip:** Use `headless=False` during development to see what's happening!

---

### Phase 2: Navigation & Location Selection

**Goal:** Get to the right gym location and day

1. **Select Location**
   - Check if already on correct location
   - Open dropdown
   - Click "San Francisco"

2. **Select Day**
   - Convert Python weekday (0-6) to day codes ("Mo", "Tu", etc.)
   - Find and click day selector

**Teaching Tip:** Take screenshots at each step for debugging

---

### Phase 3: Class Discovery

**Goal:** Find ALL classes, not just one type

1. **Inspect the HTML**
   - Open browser dev tools
   - Find class name pattern
   - Discover: `<div class="size-16 text-uppercase">CLASS NAME</div>`

2. **Scrape All Classes**
   ```python
   # Get all class elements
   elements = page.query_selector_all("div.size-16.text-uppercase")
   
   for element in elements:
       class_name = element.text_content()
       # Traverse to parent to get time, instructor
   ```

3. **Extract Metadata**
   - Time (from parent container)
   - Instructor (regex: "with NAME")
   - Availability ("book" vs "waitlist" vs "full")

**Teaching Tip:** Use regex patterns to extract structured data from unstructured text

---

### Phase 4: Booking Automation

**Goal:** Click the right buttons to book a class

1. **Find Target Class**
   ```python
   # Search all classes
   # Match by name AND time
   # Return the matching element
   ```

2. **Click Sequence**
   ```python
   element.click()           # Open modal
   book_button.click()       # Click "Book"
   confirm_button.click()    # Click "Confirm"
   ```

3. **Handle Failures**
   - Class full? → Try waitlist
   - Button not found? → Take screenshot

**Teaching Tip:** Booking systems are fragile - always have fallback options

---

### Phase 5: User Interface

**Goal:** Make it easy for users to interact

1. **Streamlit Setup**
   ```python
   import streamlit as st
   
   st.title("🏋️‍♀️ Bay Club Booking Assistant")
   
   if prompt := st.chat_input("Ask me about classes..."):
       # Process user input
   ```

2. **Intent Parsing**
   ```python
   if "check" in user_input or "available" in user_input:
       action = "check_availability"
   elif "book" in user_input:
       action = "book_class"
   ```

3. **Session State**
   ```python
   # Store class list for later reference
   st.session_state.last_class_list = classes
   st.session_state.last_mentioned_date = date
   ```

**Teaching Tip:** Session state is key for multi-turn conversations

---

### Phase 6: Smart Features

**Goal:** Handle edge cases and improve UX

1. **Flexible Name Matching**
   - Normalize class names
   - Support partial matches
   - Handle special characters

2. **Time Sorting**
   - Parse time strings
   - Convert to 24-hour format
   - Sort chronologically

3. **Numbered Booking**
   - Display numbered list
   - Parse "book #2"
   - Look up from stored list

**Teaching Tip:** The 80/20 rule - 80% of development time goes into the last 20% of features!

---

## 🎓 Teaching Points

### Key Concepts to Cover

1. **Web Scraping vs Browser Automation**
   - Scraping: Parse HTML directly (fast, fragile)
   - Automation: Drive real browser (slow, reliable)
   - When to use each

2. **Selector Strategies**
   - CSS selectors (`.class`, `#id`)
   - XPath (`//div[text()='Something']`)
   - Text-based (`text=Login`)

3. **State Management**
   - Why state matters in conversational interfaces
   - Session persistence
   - Context tracking

4. **Error Handling**
   - Timeouts (element not found)
   - Fallback strategies
   - User-friendly error messages

5. **Regex for Data Extraction**
   - Extracting structured data from unstructured text
   - Common patterns (time, dates, names)
   - Groups and captures

### Common Pitfalls

1. **Hardcoded Selectors Break**
   - Websites change
   - Use multiple fallback selectors

2. **Race Conditions**
   - Always wait for elements
   - Use Playwright's built-in waiting

3. **Case Sensitivity**
   - Normalize everything
   - Use `.lower()` liberally

4. **Time Zone Issues**
   - Always specify timezone
   - Use UTC internally

---

## 💡 Advanced Topics

### Scaling Considerations

1. **Multiple Users**
   - Each user needs their own browser session
   - Connection pooling
   - Rate limiting

2. **Error Recovery**
   - Retry logic
   - Circuit breakers
   - Health checks

3. **Performance**
   - Headless mode for production
   - Caching frequently accessed data
   - Parallel execution

### Security

1. **Credential Management**
   - Never commit credentials
   - Use environment variables
   - Consider secrets management services

2. **User Privacy**
   - Don't log sensitive data
   - Secure session storage
   - GDPR compliance

---

## 🚀 Deployment

### Local Development
```bash
streamlit run streamlit_app.py
```

### Production Considerations
- Use headless browser
- Set up proper logging
- Configure error monitoring
- SSL/HTTPS for web interface
- Background job scheduler for automated bookings

---

## 📊 Success Metrics

- **Booking Success Rate:** % of bookings that complete successfully
- **Response Time:** Time from user request to class list display
- **User Satisfaction:** Feedback on ease of use
- **Error Rate:** % of failed bookings (should be <5%)

---

## 🎯 Learning Outcomes

After building this project, students will understand:

✅ Browser automation with Playwright  
✅ Web scraping strategies  
✅ Natural language processing basics  
✅ Streamlit for rapid UI development  
✅ State management in conversational interfaces  
✅ Error handling and resilience  
✅ Regex for data extraction  
✅ Time/date handling in Python  

---

## 🔗 Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Regex Tutorial](https://regex101.com/)
- [Python datetime Module](https://docs.python.org/3/library/datetime.html)

---

**Happy Building! 🎉**

