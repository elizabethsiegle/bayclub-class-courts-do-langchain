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

def book_any_class(username, password, class_name, date=None, time_of_week="7:00", meridiem="AM", headless=False):
    """Book any class at Bay Club for a specific date and time"""
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
            
            # Book the class using the new general method
            time_str = f"{time_of_week} {meridiem}"
            logging.info(f"Looking for {class_name} class at {time_str}...")
            success = booking.book_class(class_name, target_day, time_str)
            
            if success:
                logging.info(f"Successfully booked {class_name} class!")
                return True
            else:
                logging.error(f"Failed to book {class_name} class")
                return False
                
    except Exception as e:
        logging.error(f"Booking failed: {e}")
        return False

def check_ignite_class(username, password, date=None, headless=False):
    """Check for available classes on a specific date (includes all class types: Ignite, Pilates, Riide, etc.)"""
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
                    'total_classes_found': 0,
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
            
            # Use the new search_all_classes method
            all_classes = booking.search_all_classes(target_day)
            
            if all_classes:
                # Format the results
                available_times = []
                for class_info in all_classes:
                    class_description = f"{class_info['time']} - {class_info['class_name']}"
                    if class_info['instructor'] != "Unknown":
                        class_description += f" with {class_info['instructor']}"
                    class_description += f" ({class_info['availability']})"
                    available_times.append(class_description)
                
                # Get unique class types
                class_types = list(set(cls['class_name'] for cls in all_classes))
                
                logging.info(f"Found {len(all_classes)} classes across {len(class_types)} types: {', '.join(class_types)}")
                return {
                    'date': date or datetime.datetime.now().strftime("%Y-%m-%d"),
                    'available_times': available_times,
                    'total_classes_found': len(all_classes),
                    'time_slots_found': len(available_times),
                    'class_types': class_types,
                    'status': 'success'
                }
            else:
                logging.info("No classes found")
                return {
                    'date': date or datetime.datetime.now().strftime("%Y-%m-%d"),
                    'available_times': [],
                    'total_classes_found': 0,
                    'time_slots_found': 0,
                    'status': 'no_classes'
                }
                
    except Exception as e:
        logging.error(f"Check failed: {e}")
        return {
            'date': date or datetime.datetime.now().strftime("%Y-%m-%d"),
            'available_times': [],
            'total_classes_found': 0,
            'time_slots_found': 0,
            'status': 'error',
            'error': str(e)
        }

def check_tennis_courts(username, password, date=None, club_name="San Francisco", headless=False):
    """Check available tennis courts for a specific date"""
    try:
        with IgniteBooking(headless=headless) as booking:
            # Login
            logging.info("Logging into Bay Club...")
            booking.login(username, password)
            
            # Check tennis courts
            logging.info(f"Checking tennis courts for {club_name}...")
            available_times = booking.check_tennis_courts(date=date, club_name=club_name)
            
            if available_times and isinstance(available_times, list):
                logging.info(f"Successfully retrieved {len(available_times)} tennis court time slots")
                return {
                    'status': 'success',
                    'date': date or datetime.datetime.now().strftime("%Y-%m-%d"),
                    'club': club_name,
                    'available_times': available_times,
                    'total_slots': len(available_times),
                    'message': f'Found {len(available_times)} available time slots'
                }
            else:
                logging.info("No available tennis court time slots found")
                return {
                    'status': 'no_slots',
                    'date': date or datetime.datetime.now().strftime("%Y-%m-%d"),
                    'club': club_name,
                    'available_times': [],
                    'total_slots': 0,
                    'message': 'No available time slots found'
                }
                
    except Exception as e:
        logging.error(f"Tennis court check failed: {e}")
        return {
            'status': 'error',
            'date': date or datetime.datetime.now().strftime("%Y-%m-%d"),
            'club': club_name,
            'available_times': [],
            'total_slots': 0,
            'error': str(e)
        }

def main():
    """Main function to demonstrate booking and checking classes"""
    try:
        # Validate credentials
        Config.validate_credentials()
        
        # Get credentials from config
        USERNAME = Config.BAY_CLUB_USERNAME
        PASSWORD = Config.BAY_CLUB_PASSWORD
        HEADLESS = Config.DEFAULT_HEADLESS
        
        print("🏋️‍♀️ Bay Club Class Manager")
        print("=" * 50)
        
        # Example 1: Check classes for today
        print("\n1. Checking classes for today...")
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        check_result = check_ignite_class(USERNAME, PASSWORD, today, HEADLESS)
        
        if check_result['status'] == 'success':
            class_types = check_result.get('class_types', [])
            print(f"\n✅ Found {check_result['total_classes_found']} classes across {len(class_types)} types")
            print(f"📊 Class types: {', '.join(sorted(class_types))}")
            print(f"\n📅 Classes for {today} (sorted by time):")
            print("=" * 80)
            for i, class_time in enumerate(check_result['available_times'], 1):
                print(f"{i:2}. {class_time}")
        else:
            print(f"❌ {check_result['status']}: {check_result.get('error', 'No classes found')}")
        
        # Example 2: Check classes for tomorrow
        print("\n2. Checking classes for tomorrow...")
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        check_result = check_ignite_class(USERNAME, PASSWORD, tomorrow, HEADLESS)
        
        if check_result['status'] == 'success':
            class_types = check_result.get('class_types', [])
            print(f"\n✅ Found {check_result['total_classes_found']} classes across {len(class_types)} types")
            print(f"📊 Class types: {', '.join(sorted(class_types))}")
            print(f"\n📅 Classes for {tomorrow} (sorted by time):")
            print("=" * 80)
            for i, class_time in enumerate(check_result['available_times'], 1):
                print(f"{i:2}. {class_time}")
        else:
            print(f"❌ {check_result['status']}: {check_result.get('error', 'No classes found')}")
        
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nTo fix this:")
        print("1. Create a .env file with your credentials")
        print("2. Or set environment variables directly")
        print("3. Run: python config.py to create a sample .env file")

if __name__ == "__main__":
    main()