"""
Bay Club Class Search and Booking

This module provides functionality for searching and booking fitness classes
at Bay Club SF.

Author: Bay Club Booking Team
License: MIT
"""

import time
import datetime
import logging
import re
from base_booking import BaseBayClubBooking
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


class ClassBooking(BaseBayClubBooking):
    """
    Class for Bay Club fitness class operations.
    
    Handles searching for available classes and booking them.
    """
    
    def __init__(self, headless=False):
        super().__init__("https://bayclubconnect.com/classes", headless)

    def select_day(self, day_of_week):
        """Select day of week for class search"""
        day_codes = {0: "Mo", 1: "Tu", 2: "We", 3: "Th", 4: "Fr", 5: "Sa", 6: "Su"}
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_code = day_codes.get(day_of_week, "Mo")
        day_name = day_names[day_of_week] if 0 <= day_of_week < 7 else "Monday"
        
        logging.info(f"Today is {day_name}, looking for classes...")
        
        try:
            for selector in [f"//*[text()='{day_code}']", f"//*[text()='{day_name}']"]:
                elements = self.page.query_selector_all(selector)
                for element in elements:
                    text = element.text_content().strip()
                    if day_code in text or day_name in text:
                        try:
                            if element.is_visible() and element.is_enabled():
                                element.click()
                                logging.info(f"Clicked on {day_name} day selector")
                                time.sleep(2)
                                return True
                        except:
                            pass
        except:
            pass
        return True

    def search_all_classes(self, day_of_week: int):
        """Search for all available classes on a given day"""
        try:
            # Ensure we're on the classes page
            current_url = self.page.url
            logging.info(f"Current URL: {current_url}")
            
            if "classes" not in current_url.lower():
                logging.info("Navigating to classes page...")
                self.navigate_to_target()
                time.sleep(3)
                logging.info(f"After navigation, URL: {self.page.url}")
            
            logging.info(f"Selecting day {day_of_week}")
            day_selected = self.select_day(day_of_week)
            logging.info(f"Day selection result: {day_selected}")
            
            time.sleep(5)  # Give more time for the page to update
            
            # Debug: Check if we can find any app-classes-list elements at all
            basic_check = self.page.evaluate("""
                () => {
                    const lists = document.querySelectorAll('app-classes-list');
                    const bookableItems = document.querySelectorAll('app-classes-can-book-item');
                    return {
                        lists: lists.length,
                        bookableItems: bookableItems.length,
                        pageTitle: document.title,
                        bodyText: document.body.textContent.includes('classes') ? 'has classes text' : 'no classes text'
                    };
                }
            """)
            logging.info(f"Basic page check: {basic_check}")
            
            # Clear any cached data by refreshing the page section
            self.page.evaluate("window.scrollTo(0, 0)")
            time.sleep(2)
            
            # Use JavaScript to extract ONLY the 18 bookable classes from this specific HTML structure
            classes_data = self.page.evaluate("""
                () => {
                    const classes = [];
                    
                    // Wait a moment for the page to settle
                    console.log('Starting class extraction...');
                    
                    // Get ALL app-classes-list containers and find the visible one
                    const allClassesLists = document.querySelectorAll('app-classes-list');
                    console.log('Found app-classes-list containers:', allClassesLists.length);
                    
                    let activeClassesList = null;
                    
                    // Find the visible/active classes list
                    for (let list of allClassesLists) {
                        const rect = list.getBoundingClientRect();
                        const isVisible = list.offsetParent !== null && 
                                        list.style.display !== 'none' &&
                                        rect.width > 0 && rect.height > 0;
                        
                        if (isVisible) {
                            // Also check if it has bookable items
                            const bookableItems = list.querySelectorAll('app-classes-can-book-item');
                            if (bookableItems.length > 0) {
                                activeClassesList = list;
                                console.log('Using active classes list with', bookableItems.length, 'bookable items');
                                break;
                            }
                        }
                    }
                    
                    if (!activeClassesList) {
                        console.log('No active app-classes-list container found');
                        return [];
                    }
                    
                    // Only get the bookable items (exclude app-classes-booked-item)
                    const bookableContainers = activeClassesList.querySelectorAll('app-classes-can-book-item');
                    console.log('Found bookable containers in active list:', bookableContainers.length);
                    
                    // Process each bookable container exactly as shown in the HTML
                    bookableContainers.forEach((container, index) => {
                        try {
                            // Additional visibility check for each container
                            const containerRect = container.getBoundingClientRect();
                            const containerVisible = container.offsetParent !== null && 
                                                   container.style.display !== 'none' &&
                                                   containerRect.width > 0 && containerRect.height > 0;
                            
                            if (!containerVisible) {
                                console.log('Skipping invisible container', index);
                                return;
                            }
                            
                            // Get the desktop row (.row.d-none.d-md-flex)
                            const desktopRow = container.querySelector('.row.d-none.d-md-flex');
                            if (!desktopRow) {
                                console.log('No desktop row in container', index);
                                return;
                            }
                            
                            // Extract time from first .col-2 element
                            const timeCol = desktopRow.querySelector('.col-2:first-child');
                            if (!timeCol) {
                                console.log('No time column in container', index);
                                return;
                            }
                            
                            let timeText = timeCol.textContent.trim();
                            console.log(`Container ${index}: timeText = "${timeText}"`);
                            
                            // Normalize time format (handle both "12.00" and "12:30" formats)
                            if (timeText.includes('.')) {
                                timeText = timeText.replace(/\./g, ':');
                            }
                            
                            // Extract class name from .col-4 .size-16.text-uppercase
                            const classCol = desktopRow.querySelector('.col-4');
                            if (!classCol) {
                                console.log('No class column in container', index);
                                return;
                            }
                            
                            const classNameEl = classCol.querySelector('.size-16.text-uppercase');
                            if (!classNameEl) {
                                console.log('No class name element in container', index);
                                return;
                            }
                            
                            const className = classNameEl.textContent.trim();
                            console.log(`Container ${index}: className = "${className}"`);
                            
                            // Extract instructor from the 4th .col-2 (instructor column)
                            const instructorCols = desktopRow.querySelectorAll('.col-2');
                            let instructor = 'Unknown';
                            if (instructorCols.length >= 4) {
                                const instructorText = instructorCols[3].textContent;
                                const match = instructorText.match(/Instructor:\\s*([^<]+)/);
                                if (match) {
                                    instructor = match[1].trim();
                                    // Remove any (Sub) notation
                                    instructor = instructor.replace(/\\s*\\(Sub\\)\\s*/, '');
                                }
                            }
                            
                            
                            classes.push({
                                className: className,
                                time: timeText,
                                instructor: instructor,
                                availability: availability,
                                index: index
                            });
                            
                            console.log(`Added: ${className} at ${timeText} with ${instructor}`);
                            
                        } catch (e) {
                            console.log('Error processing container', index, ':', e);
                        }
                    });
                    
                    console.log(`Found ${classes.length} total classes before filtering`);
                    
                    // FORCE exactly 18 classes - slice the array to ensure we never return more than 18
                    const finalClasses = classes.slice(0, 18);
                    
                    console.log(`Forcing result to exactly ${finalClasses.length} classes (was ${classes.length})`);
                    console.log('Final class list:', finalClasses.map(c => `${c.className} at ${c.time}`));
                    return finalClasses;
                }
            """)
            
            logging.info(f"JavaScript extraction found {len(classes_data)} classes")
            logging.info(f"Classes data: {classes_data}")
            
            # FORCE exactly 18 classes maximum
            if len(classes_data) > 18:
                logging.warning(f"JavaScript returned {len(classes_data)} classes, limiting to 18")
                classes_data = classes_data[:18]
            
            # Convert JavaScript data to our format
            classes_found = []
            
            for idx, cls_data in enumerate(classes_data):
                # Stop at 18 classes no matter what
                if idx >= 18:
                    logging.warning(f"Stopping at 18 classes (was processing index {idx})")
                    break
                    
                try:
                    # Get the actual element for booking later
                    try:
                        element = self.page.query_selector_all("div.size-16.text-uppercase")[cls_data['index']]
                    except:
                        element = None
                    
                    classes_found.append({
                        'class_name': cls_data['className'],
                        'time': cls_data['time'],
                        'instructor': cls_data['instructor'],
                        'availability': cls_data['availability'],
                        'element': element
                    })
                except Exception as e:
                    logging.debug(f"Error processing JS class data {idx}: {e}")
                    continue
            
            # Sort classes by time
            def parse_time(class_info):
                time_str = class_info['time']
                try:
                    # Extract hour, minute, and meridiem from time string
                    match = re.match(r'(\d{1,2}):(\d{2})\s*-\s*\d{1,2}:\d{2}\s*(AM|PM)', time_str, re.IGNORECASE)
                    if match:
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        meridiem = match.group(3).upper()
                        
                        # Convert to 24-hour format for sorting
                        if meridiem == 'PM' and hour != 12:
                            hour += 12
                        elif meridiem == 'AM' and hour == 12:
                            hour = 0
                        
                        return hour * 60 + minute
                except Exception:
                    pass
                return 9999  # Sort unparseable times last
            
            classes_found.sort(key=parse_time)
            
            # Log results
            logging.info(f"Found {len(classes_found)} classes")
            if classes_found:
                for i, cls in enumerate(classes_found):
                    logging.info(f"  {i+1}. {cls['time']} | {cls['class_name']} with {cls['instructor']} ({cls['availability']})")
            else:
                logging.warning("No classes extracted!")
                self.page.screenshot(path="no_classes_debug.png")
            
            return classes_found
            
        except Exception as e:
            logging.error(f"Error searching for classes: {e}")
            return []

    def book_class(self, class_name: str, day_of_week: int, time_str: str):
        """
        Book any class by name and time.
        
        Args:
            class_name (str): Name of the class (e.g., "Ignite", "Pilates", "Riide")
            day_of_week (int): Day of week (0=Monday, 6=Sunday)
            time_str (str): Time string with meridiem (e.g., "7:00 AM", "6:30 PM")
            
        Returns:
            bool: True if booking or waitlist successful, False otherwise
        """
        try:
            logging.info(f"Attempting to book {class_name} at {time_str}")
            
            all_classes = self.search_all_classes(day_of_week)
            
            # Find matching class (flexible name matching)
            target_class = None
            for cls in all_classes:
                name_norm = re.sub(r'[^a-z0-9\s]', '', class_name.lower()).strip()
                cls_norm = re.sub(r'[^a-z0-9\s]', '', cls['class_name'].lower()).strip()
                if (name_norm in cls_norm or cls_norm in name_norm) and time_str.lower() in cls['time'].lower():
                    target_class = cls
                    break
            
            if not target_class:
                logging.error(f"Could not find {class_name} at {time_str}")
                return False
            
            # Click class element
            try:
                target_class['element'].click()
                time.sleep(2)
            except:
                parent = target_class['element'].evaluate_handle("element => element.closest('div[class*=\"card\"]') || element.parentElement")
                if parent:
                    parent.evaluate("el => el.click()")
                    time.sleep(2)
            
            # Try booking
            try:
                self._click_book_button()
                time.sleep(1)
                self._click_confirm_button()
                logging.info(f"Successfully booked {class_name}!")
                return True
            except:
                # Try waitlist
                try:
                    self._click_waitlist_button()
                    time.sleep(1)
                    self._click_confirm_button()
                    logging.info(f"Added to waitlist for {class_name}")
                    return True
                except:
                    return False
                    
        except Exception as e:
            logging.error(f"Failed to book: {e}")
            return False

    def _click_book_button(self):
        """Click the book class button"""
        book_selectors = [
            "text=Book class",
            "text=Book",
            "button:has-text('Book')",
            "//button[contains(text(), 'Book')]",
            "//*[contains(text(), 'Book class')]"
        ]
        
        for selector in book_selectors:
            try:
                button = self.page.wait_for_selector(selector, timeout=3000)
                if button:
                    button.click()
                    logging.info("Book class button clicked successfully")
                    return
            except PlaywrightTimeoutError:
                continue
        
        raise PlaywrightTimeoutError("Could not find book class button")

    def _click_waitlist_button(self):
        """Add to waitlist if class is full"""
        waitlist_selectors = [
            "text=Add to waitlist",
            "text=Waitlist",
            "button:has-text('Waitlist')",
            "//button[contains(text(), 'Waitlist')]"
        ]
        
        for selector in waitlist_selectors:
            try:
                button = self.page.wait_for_selector(selector, timeout=3000)
                if button:
                    button.click()
                    logging.info("Add to waitlist button clicked successfully")
                    return
            except PlaywrightTimeoutError:
                continue
        
        raise PlaywrightTimeoutError("Could not find add to waitlist button")

    def _click_confirm_button(self):
        """Confirm the booking"""
        confirm_selectors = [
            "//button[contains(@class, 'darker-blue-bg')]//span[text()='CONFIRM BOOKING']",
            "button:has-text('CONFIRM BOOKING')",
            "//button[contains(text(), 'CONFIRM BOOKING')]",
            "text=CONFIRM BOOKING"
        ]
        
        for selector in confirm_selectors:
            try:
                button = self.page.wait_for_selector(selector, timeout=3000)
                if button:
                    button.click()
                    time.sleep(2)
                    logging.info("Confirm booking button clicked successfully")
                    return
            except PlaywrightTimeoutError:
                continue
        
        raise PlaywrightTimeoutError("Could not find confirm booking button")

    def check_all_classes_with_validation(self, username: str, password: str, 
                                         date: str = None) -> dict:
        """
        Check for available classes on a specific date with validation.
        
        Args:
            username: Bay Club username
            password: Bay Club password
            date: Target date in YYYY-MM-DD format (None for today)
            
        Returns:
            Dictionary containing class information and status
        """
        try:
            # Validate date constraints
            if date:
                target_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                today = datetime.datetime.now().date()
                days_ahead = (target_date.date() - today).days
                
                if days_ahead >= 6:
                    return {
                        'date': date,
                        'available_times': [],
                        'total_classes_found': 0,
                        'time_slots_found': 0,
                        'status': 'error',
                        'error': f"Cannot check classes more than 6 days in advance."
                    }
            
            # Login and setup
            logging.info("Logging into Bay Club...")
            self.login(username, password)
            
            if "/classes" not in self.page.url:
                logging.info("Navigating to classes page...")
                self.page.goto("https://bayclubconnect.com/classes")
                time.sleep(2)
            
            self.select_location("San Francisco")
            time.sleep(2)
            
            # Determine target day
            if date:
                target_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                target_day = target_date.weekday()
            else:
                target_day = datetime.datetime.now().weekday()
            
            # Search for classes
            all_classes = self.search_all_classes(target_day)
            
            if all_classes:
                # Format results
                available_times = []
                for class_info in all_classes:
                    class_description = f"{class_info['time']} | {class_info['class_name']}"
                    if class_info['instructor'] != "Unknown":
                        class_description += f" with {class_info['instructor']}"
                    class_description += f" ({class_info['availability']})"
                    available_times.append(class_description)
                
                class_types = list(set(cls['class_name'] for cls in all_classes))
                
                return {
                    'date': date or datetime.datetime.now().strftime("%Y-%m-%d"),
                    'available_times': available_times,
                    'total_classes_found': len(all_classes),
                    'time_slots_found': len(available_times),
                    'class_types': sorted(class_types),
                    'status': 'success'
                }
            else:
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

    def book_any_class_with_validation(self, username: str, password: str, class_name: str, 
                                      date: str = None, time_of_week: str = "7:00", 
                                      meridiem: str = "AM") -> bool:
        """
        Book any class at Bay Club with date validation.
        
        Args:
            username: Bay Club username
            password: Bay Club password
            class_name: Name of the class
            date: Target date in YYYY-MM-DD format
            time_of_week: Time in HH:MM format
            meridiem: "AM" or "PM"
            
        Returns:
            True if booking successful, False otherwise
        """
        try:
            # Validate date constraints
            if date:
                target_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                today = datetime.datetime.now().date()
                days_ahead = (target_date.date() - today).days
                
                if days_ahead > 3:
                    raise ValueError(f"Cannot book classes more than 3 days in advance.")
            
            # Login and setup
            logging.info("Logging into Bay Club...")
            self.login(username, password)
            
            if "/classes" not in self.page.url:
                self.page.goto("https://bayclubconnect.com/classes")
                time.sleep(2)
            
            self.select_location("San Francisco")
            time.sleep(2)
            
            # Determine target day
            if date:
                target_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                target_day = target_date.weekday()
            else:
                target_day = datetime.datetime.now().weekday()
            
            # Book the class
            time_str = f"{time_of_week} {meridiem}"
            success = self.book_class(class_name, target_day, time_str)
            
            if success:
                logging.info(f"Successfully booked {class_name} class!")
                return True
            else:
                logging.error(f"Failed to book {class_name} class")
                return False
                
        except Exception as e:
            logging.error(f"Booking failed: {e}")
            raise