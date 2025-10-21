#!/usr/bin/python3

import os
import datetime
import logging
from bayclub_booking import IgniteBooking
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def book_ignite_class(username, password, date=None, time_of_week="7:00", meridiem="AM", headless=False):
    """Book an Ignite class at Bay Club for a specific date and time"""
    try:
        # Check if the date is too far in advance (more than 3 days)
        if date:
            target_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            today = datetime.datetime.now().date()
            days_ahead = (target_date.date() - today).days
            
            if days_ahead > 3:
                logging.warning(f"Cannot book classes more than 3 days in advance. Requested date is {days_ahead} days ahead.")
                raise ValueError(f"Cannot book classes more than 3 days in advance. The requested date ({date}) is {days_ahead} days from today. Please choose a date within the next 3 days.")
        
        with IgniteBooking(headless=headless) as booking:
            # Login
            logging.info("Logging into Bay Club...")
            booking.login(username, password)
            
            # Select location
            booking.select_location()
            
            # Determine the day to book
            if date:
                # Parse the date string (format: YYYY-MM-DD)
                target_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                target_day = target_date.weekday()
                logging.info(f"Booking for date: {date} (day of week: {target_day})")
            else:
                # Use current day
                target_day = datetime.datetime.now().weekday()
                logging.info(f"Booking for current day (day of week: {target_day})")
            
            # Select the appropriate day
            booking.select_day(target_day, logging)
            
            # Select Ignite class
            logging.info(f"Looking for Ignite class at {time_of_week} {meridiem}...")
            booking.select_ignite(target_day, time_of_week, meridiem)
            
            # Try to book the class
            try:
                logging.info("Attempting to book class...")
                booking.book_ignite()
                booking.confirm_ignite()
                logging.info("Successfully booked Ignite class!")
                return True
            except Exception as e:
                logging.error(f"Booking failed: {e}")
                # Only try waitlist if we can confirm there's a waitlist option
                try:
                    logging.info("Checking if waitlist is available...")
                    booking.add_to_waitlist_ignite()
                    booking.confirm_ignite()
                    logging.info("Successfully added to waitlist!")
                    return True
                except Exception as waitlist_error:
                    logging.error(f"Waitlist also failed: {waitlist_error}")
                    return False
                
    except Exception as e:
        logging.error(f"Booking failed: {e}")
        return False

def check_ignite_class(username, password, date=None, headless=False):
    """Check for available Ignite classes on a specific date"""
    try:
        # Check if the date is too far in advance (more than 6 days)
        if date:
            target_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            today = datetime.datetime.now().date()
            days_ahead = (target_date.date() - today).days
            
            if days_ahead >= 6:
                logging.warning(f"Cannot check classes more than 6 days in advance. Requested date is {days_ahead} days ahead.")
                return {
                    'date': date,
                    'available_times': [],
                    'ignite_studios_found': 0,
                    'time_slots_found': 0,
                    'status': 'error',
                    'error': f"Cannot check classes more than 6 days in advance. The requested date ({date}) is {days_ahead} days from today. Please choose a date within the next 6 days."
                }
        
        with IgniteBooking(headless=headless) as booking:
            # Login
            logging.info("Logging into Bay Club...")
            booking.login(username, password)
            
            # Select location
            booking.select_location()
            
            # Determine the day to check
            if date:
                # Parse the date string (format: YYYY-MM-DD)
                target_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                target_day = target_date.weekday()
                logging.info(f"Checking classes for date: {date} (day of week: {target_day})")
            else:
                # Use current day
                target_day = datetime.datetime.now().weekday()
                logging.info(f"Checking classes for current day (day of week: {target_day})")
            
            # Select the appropriate day
            booking.select_day(target_day, logging)
            
            # Wait a bit for the page to load after day selection
            import time
            time.sleep(2)
            
            # Look for Ignite classes on this date
            logging.info("Looking for available Ignite classes...")
            
            # First, let's check what day we're actually viewing
            try:
                # Look for day indicators on the page
                day_elements = booking.page.query_selector_all("//*[contains(text(), 'Monday') or contains(text(), 'Tuesday') or contains(text(), 'Wednesday') or contains(text(), 'Thursday') or contains(text(), 'Friday') or contains(text(), 'Saturday') or contains(text(), 'Sunday')]")
                if day_elements:
                    for day_element in day_elements:
                        day_text = day_element.text_content().strip()
                        if any(day in day_text for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
                            logging.info(f"Current day on page: {day_text}")
                            break
            except Exception as e:
                logging.info(f"Could not determine current day: {e}")
            
            # Scroll down to see if there are more classes
            logging.info("Scrolling down to check for more classes...")
            booking.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            booking.page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            
            ignite_elements = booking.page.query_selector_all("//*[contains(text(), 'Ignite Studio')]")
            
            if ignite_elements:
                logging.info(f"Found {len(ignite_elements)} Ignite Studio elements")
                available_times = []
                
                # For each Ignite Studio element, look for associated time elements
                for i, ignite_element in enumerate(ignite_elements):
                    logging.info(f"Processing Ignite Studio element {i+1}")
                    
                    # Look for time elements near this Ignite Studio element
                    # Try to find time elements in the same row or container
                    try:
                        # Get the parent container of the Ignite Studio element
                        parent_handle = ignite_element.evaluate_handle("element => element.parentElement")
                        if parent_handle:
                            # Look for time elements within the parent container
                            time_elements = parent_handle.query_selector_all("//*[contains(text(), ':')]")
                            
                            for time_element in time_elements:
                                text = time_element.text_content().strip()
                                # Look for time patterns like "7:00", "7:30", etc.
                                if ':' in text and any(char.isdigit() for char in text):
                                    import re
                                    time_match = re.search(r'(\d{1,2}:\d{2})', text)
                                    if time_match:
                                        time_str = time_match.group(1)
                                        if time_str not in available_times:
                                            available_times.append(time_str)
                                            logging.info(f"Found time {time_str} for Ignite Studio {i+1}")
                    except Exception as e:
                        logging.info(f"Error processing Ignite Studio element {i+1}: {e}")
                        continue
                
                # If we didn't find times in parent containers, try a broader search
                if not available_times:
                    logging.info("No times found in parent containers, trying broader search...")
                    time_elements = booking.page.query_selector_all("//*[contains(text(), ':')]")
                    
                    for element in time_elements:
                        text = element.text_content().strip()
                        if ':' in text and any(char.isdigit() for char in text):
                            import re
                            # Look for time range patterns like "5:30 - 6:20 PM" or "6:00  - 6:50 AM" (with multiple spaces)
                            time_range_match = re.search(r'(\d{1,2}:\d{2})\s+-\s+(\d{1,2}:\d{2})\s+(AM|PM)', text)
                            if time_range_match:
                                start_time = time_range_match.group(1)
                                end_time = time_range_match.group(2)
                                meridiem = time_range_match.group(3)
                                
                                # Check if this time element is associated with Ignite classes
                                try:
                                    parent = element.evaluate_handle("element => element.parentElement")
                                    if parent:
                                        parent_text = parent.text_content().lower()
                                        if 'ignite' in parent_text:
                                            # Format the time properly
                                            time_str = f"{start_time} {meridiem}"
                                            if time_str not in available_times:
                                                available_times.append(time_str)
                                                logging.info(f"Found Ignite time {time_str} from range: '{text}'")
                                except:
                                    pass
                            else:
                                # Try a more flexible pattern for time ranges with lowercase am/pm
                                time_range_match = re.search(r'(\d{1,2}:\d{2})\s+-\s+(\d{1,2}:\d{2})\s+(am|pm)', text.lower())
                                if time_range_match:
                                    start_time = time_range_match.group(1)
                                    meridiem = time_range_match.group(3).upper()
                                    time_str = f"{start_time} {meridiem}"
                                    # Check if this time element is associated with Ignite classes
                                    try:
                                        parent = element.evaluate_handle("element => element.parentElement")
                                        if parent:
                                            parent_text = parent.text_content().lower()
                                            if 'ignite' in parent_text:
                                                if time_str not in available_times:
                                                    available_times.append(time_str)
                                                    logging.info(f"Found Ignite time {time_str} from range: '{text}'")
                                    except:
                                        pass
                                else:
                                    # Look for simple time patterns like "6:00 AM" or "4:30 PM"
                                    time_meridiem_match = re.search(r'(\d{1,2}:\d{2})\s*(AM|PM)', text)
                                    if time_meridiem_match:
                                        time_str = f"{time_meridiem_match.group(1)} {time_meridiem_match.group(2)}"
                                        # Check if this time element is associated with Ignite classes
                                        try:
                                            parent = element.evaluate_handle("element => element.parentElement")
                                            if parent:
                                                parent_text = parent.text_content().lower()
                                                if 'ignite' in parent_text:
                                                    if time_str not in available_times:
                                                        available_times.append(time_str)
                                                        logging.info(f"Found Ignite time {time_str}: '{text}'")
                                        except:
                                            pass
                
                # Sort times for better presentation
                available_times.sort()
                
                logging.info(f"Found available times: {available_times}")
                return {
                    'date': date or datetime.datetime.now().strftime("%Y-%m-%d"),
                    'available_times': available_times,
                    'ignite_studios_found': len(ignite_elements),
                    'time_slots_found': len(available_times),
                    'status': 'success'
                }
            else:
                logging.info("No Ignite Studio elements found")
                return {
                    'date': date or datetime.datetime.now().strftime("%Y-%m-%d"),
                    'available_times': [],
                    'ignite_studios_found': 0,
                    'time_slots_found': 0,
                    'status': 'no_classes'
                }
                
    except Exception as e:
        logging.error(f"Check failed: {e}")
        return {
            'date': date or datetime.datetime.now().strftime("%Y-%m-%d"),
            'available_times': [],
            'ignite_studios_found': 0,
            'time_slots_found': 0,
            'status': 'error',
            'error': str(e)
        }

def main():
    """Main function to demonstrate booking and checking Ignite classes"""
    try:
        # Validate credentials
        Config.validate_credentials()
        
        # Get credentials from config
        USERNAME = Config.BAY_CLUB_USERNAME
        PASSWORD = Config.BAY_CLUB_PASSWORD
        HEADLESS = Config.DEFAULT_HEADLESS
        
        print("🏋️‍♀️ Bay Club Ignite Class Manager")
        print("=" * 50)
        
        # Example 1: Check classes for today
        print("\n1. Checking classes for today...")
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        check_result = check_ignite_class(USERNAME, PASSWORD, today, HEADLESS)
        
        if check_result['status'] == 'success':
            print(f"✅ Found {check_result['ignite_studios_found']} Ignite Studio(s)")
            print(f"📅 Available times: {check_result['available_times']}")
        else:
            print(f"❌ {check_result['status']}: {check_result.get('error', 'No classes found')}")
        
        # Example 2: Check classes for tomorrow
        print("\n2. Checking classes for tomorrow...")
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        check_result = check_ignite_class(USERNAME, PASSWORD, tomorrow, HEADLESS)
        
        if check_result['status'] == 'success':
            print(f"✅ Found {check_result['ignite_studios_found']} Ignite Studio(s)")
            print(f"📅 Available times: {check_result['available_times']}")
        else:
            print(f"❌ {check_result['status']}: {check_result.get('error', 'No classes found')}")
        
        # Example 3: Book a class (uncomment to use)
        # print("\n3. Booking a class...")
        # success = book_ignite_class(USERNAME, PASSWORD, today, "7:00", "AM", HEADLESS)
        # if success:
        #     print("✅ Successfully booked class!")
        # else:
        #     print("❌ Booking failed")
        
        print("\n🎉 Demo completed!")
        print("\nTo use these functions:")
        print("- check_ignite_class(username, password, date, headless)")
        print("- book_ignite_class(username, password, date, time, meridiem, headless)")
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nTo fix this:")
        print("1. Create a .env file with your credentials")
        print("2. Or set environment variables directly")
        print("3. Run: python config.py to create a sample .env file")

if __name__ == "__main__":
    main()