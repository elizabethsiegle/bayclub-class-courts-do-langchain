from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import datetime
import logging


class IgniteBooking:
    '''Functions to book Ignite class at Bayclub using Playwright'''
    
    def __init__(self, url="https://bayclubconnect.com/classes", headless=False):
        self.url = url
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None
        
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = self.context.new_page()
        self.page.goto(self.url)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def login(self, user_name='user_name', user_password='password'):
        """Login to Bay Club"""
        try:
            self.page.wait_for_selector("#username", timeout=15000).fill(user_name)
            self.page.wait_for_selector("#password", timeout=15000).fill(user_password)
            
            login_selectors = [
                "xpath=/html/body/app-root/div/app-login/div/app-login-connect/div[1]/div/div/div/form/button",
                "button[type='submit']",
                "button:has-text('Login')"
            ]
            
            for selector in login_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    break
                except PlaywrightTimeoutError:
                    continue
            
            try:
                self.page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeoutError:
                self.page.wait_for_selector("text=Classes", timeout=10000)
            
            time.sleep(2)
            self.select_location("San Francisco")
            
        except PlaywrightTimeoutError as e:
            logging.error(f"Login failed: {e}")
            self.page.screenshot(path="login_error.png")
            raise

    def select_location(self, location_name="San Francisco"):
        """Select Bay Club San Francisco location"""
        try:
            # Check if already on San Francisco
            elements = self.page.query_selector_all("//*[contains(text(), 'Bay Club San Francisco')]")
            if any("Bay Club" in el.text_content() and "San Francisco" in el.text_content() for el in elements):
                return
            
            # Open dropdown
            for selector in ["[dropdown]", ".btn-group .select-border"]:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    time.sleep(1)
                    break
                except:
                    continue
            
            # Click San Francisco span
            for selector in ["//span[text()='San Francisco']", "text=San Francisco"]:
                try:
                    elements = self.page.query_selector_all(selector)
                    for el in elements:
                        if el.text_content().strip() == 'San Francisco':
                            el.click()
                            time.sleep(1)
                            break
                    break
                except:
                    continue
            
            # Click San Francisco option
            elements = self.page.query_selector_all("//div[text()='San Francisco']")
            for el in elements:
                if el.text_content().strip() == 'San Francisco':
                    try:
                        el.click()
                    except:
                        self.page.evaluate("element => element.click()", el)
                    time.sleep(2)
                    break
        except Exception as e:
            logging.warning(f"Location selection failed: {e}")

    def select_day(self, day_of_week, logging):
        """Select day of week"""
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

    def select_ignite(self, day_of_week: int, time_of_week: str = "7:00", meridiem: str = "AM"):
        """
        Selects the IGNITE class for the given day of the week and time.
        
        Args:
            day_of_week (int): Python weekday (0=Monday, 6=Sunday).
            time_of_week (str): The time string to look for, e.g. "7:00" or "6:30".
            meridiem (str): AM or PM
        """
        try:
            logging.info(f"Looking for Ignite class at {time_of_week} {meridiem}...")
            
            # Look for time elements that contain the specific time and are associated with Ignite
            time_elements = self.page.query_selector_all("//*[contains(text(), ':')]")
            
            target_time_str = f"{time_of_week} {meridiem}"
            logging.info(f"Looking for time: {target_time_str}")
            
            for element in time_elements:
                text = element.text_content().strip()
                if ':' in text and any(char.isdigit() for char in text):
                    # Check if this time element contains our target time
                    if time_of_week in text and meridiem.upper() in text.upper():
                        # Check if this element is associated with Ignite classes
                        try:
                            parent = element.evaluate_handle("element => element.parentElement")
                            if parent:
                                parent_text = parent.text_content().lower()
                                if 'ignite' in parent_text:
                                    logging.info(f"Found Ignite time element: '{text}'")
                                    
                                    # Look for the BOOK button near this time element
                                    book_selectors = [
                                        "//button[contains(text(), 'BOOK')]",
                                        "//*[contains(text(), 'BOOK')]",
                                        "//button[contains(@class, 'book')]"
                                    ]
                                    
                                    # Try to find BOOK button in the same container
                                    try:
                                        grandparent = parent.evaluate_handle("element => element.parentElement")
                                        if grandparent:
                                            book_elements = grandparent.query_selector_all("//button[contains(text(), 'BOOK')]")
                                            if book_elements:
                                                book_button = book_elements[0]
                                                logging.info("Found BOOK button, clicking it...")
                                                book_button.click()
                                                return True
                                    except Exception as e:
                                        logging.info(f"Error finding BOOK button: {e}")
                                    
                                    # If no BOOK button found, try clicking the time element itself
                                    try:
                                        element.click()
                                        logging.info("Clicked on time element")
                                        return True
                                    except Exception as e:
                                        logging.info(f"Failed to click time element: {e}")
                        except Exception as e:
                            logging.info(f"Error checking parent context: {e}")
                            continue
            
            logging.error(f"Could not find Ignite class at {time_of_week} {meridiem}")
            return False
            
        except Exception as e:
            logging.error(f"Failed to find Ignite class: {e}")
            return False

    def book_ignite(self):
        """Click the book class button"""
        try:
            logging.info("Looking for book class button...")
            
            # Try multiple selectors for book button
            book_selectors = [
                "text=Book class",
                "text=Book",
                "button:has-text('Book')",
                "//button[contains(text(), 'Book')]",
                "//*[contains(text(), 'Book class')]",
                "//*[contains(text(), 'Book') and contains(@class, 'btn')]",
                "[class*='book']",
                "button[class*='book']"
            ]
            
            book_button = None
            for selector in book_selectors:
                try:
                    logging.info(f"Trying book button selector: {selector}")
                    book_button = self.page.wait_for_selector(selector, timeout=3000)
                    if book_button:
                        logging.info("Found book class button")
                        break
                except PlaywrightTimeoutError:
                    continue
            
            if not book_button:
                logging.warning("Could not find book class button")
                self.page.screenshot(path="book_button_debug.png")
                raise PlaywrightTimeoutError("Could not find book class button")
            
            logging.info("Clicking book class button...")
            book_button.click()
            logging.info("Book class button clicked successfully")
            
        except PlaywrightTimeoutError as e:
            logging.error(f"Failed to click book class button: {e}")
            raise

    def add_to_waitlist_ignite(self):
        """Add to waitlist if class is full"""
        try:
            logging.info("Looking for add to waitlist button...")
            
            # Try multiple selectors for waitlist button
            waitlist_selectors = [
                "text=Add to waitlist",
                "text=Waitlist",
                "button:has-text('Waitlist')",
                "button:has-text('Add to waitlist')",
                "//button[contains(text(), 'Waitlist')]",
                "//button[contains(text(), 'Add to waitlist')]",
                "//*[contains(text(), 'waitlist')]",
                "//*[contains(text(), 'Waitlist')]",
                "[class*='waitlist']",
                "button[class*='waitlist']"
            ]
            
            waitlist_button = None
            for selector in waitlist_selectors:
                try:
                    logging.info(f"Trying waitlist button selector: {selector}")
                    waitlist_button = self.page.wait_for_selector(selector, timeout=3000)
                    if waitlist_button:
                        logging.info("Found add to waitlist button")
                        break
                except PlaywrightTimeoutError:
                    continue
            
            if not waitlist_button:
                logging.warning("Could not find add to waitlist button")
                self.page.screenshot(path="waitlist_button_debug.png")
                raise PlaywrightTimeoutError("Could not find add to waitlist button")
            
            logging.info("Clicking add to waitlist button...")
            waitlist_button.click()
            logging.info("Add to waitlist button clicked successfully")
            
        except PlaywrightTimeoutError as e:
            logging.error(f"Failed to click add to waitlist button: {e}")
            raise

    def confirm_ignite(self):
        """Confirm the booking"""
        try:
            logging.info("Looking for confirm booking button...")
            
            # Try multiple selectors for the confirm button
            confirm_selectors = [
                "//button[@class='btn darker-blue-bg font-weight-bold mx-2 py-2 text-uppercase white']//span[text()='CONFIRM BOOKING']",
                "//button[contains(@class, 'darker-blue-bg')]//span[text()='CONFIRM BOOKING']",
                "//button[contains(@class, 'btn') and contains(@class, 'darker-blue-bg')]//span[text()='CONFIRM BOOKING']",
                "//span[text()='CONFIRM BOOKING']",
                "button:has-text('CONFIRM BOOKING')",
                "//button[contains(text(), 'CONFIRM BOOKING')]",
                "text=CONFIRM BOOKING",
                "//button[contains(@class, 'btn') and contains(text(), 'CONFIRM')]",
                "//button[contains(@class, 'darker-blue-bg')]",
                "//button[contains(@class, 'btn') and contains(@class, 'darker-blue-bg')]"
            ]
            
            confirm_button = None
            for selector in confirm_selectors:
                try:
                    logging.info(f"Trying confirm button selector: {selector}")
                    confirm_button = self.page.wait_for_selector(selector, timeout=3000)
                    if confirm_button:
                        logging.info("Found confirm booking button")
                        break
                except PlaywrightTimeoutError:
                    continue
            
            if not confirm_button:
                logging.warning("Could not find confirm booking button")
                self.page.screenshot(path="confirm_button_debug.png")
                raise PlaywrightTimeoutError("Could not find confirm booking button")
            
            logging.info("Clicking confirm booking button...")
            confirm_button.click()
            time.sleep(2)  # Wait for confirmation to process
            logging.info("Confirm booking button clicked successfully")
            
        except PlaywrightTimeoutError as e:
            logging.error(f"Failed to confirm booking: {e}")
            self.page.screenshot(path="confirm_button_error.png")
            raise

    def search_all_classes(self, day_of_week: int):
        """Search for all available classes on a given day"""
        try:
            self.select_day(day_of_week, logging)
            time.sleep(3)
            
            # Find class elements
            class_elements = self.page.query_selector_all("div.size-16.text-uppercase")
            if not class_elements:
                return []
            
            logging.info(f"Processing {len(class_elements)} classes...")
            
            classes_found = []
            seen_classes = set()
            import re
            
            for element in class_elements:
                try:
                    class_name = element.text_content().strip()
                    if not class_name or len(class_name) > 100 or not any(c.isupper() for c in class_name):
                        continue
                    
                    parent = element.evaluate_handle("""element => {
                        let current = element;
                        for (let i = 0; i < 10; i++) {
                            if (!current) break;
                            const classes = current.className || '';
                            if (classes.includes('class') || classes.includes('card')) return current;
                            current = current.parentElement;
                        }
                        return element.parentElement.parentElement.parentElement || element.parentElement;
                    }""")
                    
                    if not parent:
                        continue
                        
                    parent_text = parent.evaluate("el => el.textContent")
                    
                    # Extract time (start time from range)
                    time_range_match = re.search(r'(\d{1,2}:\d{2})\s*-\s*\d{1,2}:\d{2}\s*(AM|PM)', parent_text, re.IGNORECASE)
                    if time_range_match:
                        class_time = f"{time_range_match.group(1)} {time_range_match.group(2).upper()}"
                    else:
                        time_match = re.search(r'(\d{1,2}:\d{2})\s*(AM|PM)', parent_text, re.IGNORECASE)
                        class_time = f"{time_match.group(1)} {time_match.group(2).upper()}" if time_match else "Time not found"
                    
                    # Avoid duplicates
                    unique_key = f"{class_name}_{class_time}"
                    if unique_key in seen_classes:
                        continue
                    seen_classes.add(unique_key)
                    
                    # Extract instructor
                    instructor_match = re.search(r'with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', parent_text)
                    instructor = instructor_match.group(1) if instructor_match else "Unknown"
                    
                    # Determine availability
                    lower_text = parent_text.lower()
                    if 'waitlist' in lower_text:
                        availability = "Waitlist"
                    elif 'book' in lower_text:
                        availability = "Available"
                    else:
                        availability = "Full"
                    
                    classes_found.append({
                        'class_name': class_name,
                        'time': class_time,
                        'instructor': instructor,
                        'availability': availability,
                        'element': element
                    })
                    
                except Exception as e:
                    continue
            
            # Sort by time
            def parse_time(class_info):
                time_str = class_info['time']
                if time_str == "Time not found":
                    return 9999
                try:
                    match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_str, re.IGNORECASE)
                    if match:
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        if match.group(3).upper() == 'PM' and hour != 12:
                            hour += 12
                        elif match.group(3).upper() == 'AM' and hour == 12:
                            hour = 0
                        return hour * 60 + minute
                except:
                    pass
                return 9999
            
            classes_found.sort(key=parse_time)
            logging.info(f"Found {len(classes_found)} classes")
            return classes_found
            
        except Exception as e:
            logging.error(f"Failed to search classes: {e}")
            return []

    def book_class(self, class_name: str, day_of_week: int, time_str: str):
        """Book any class by name and time"""
        try:
            logging.info(f"Attempting to book {class_name} at {time_str}")
            
            all_classes = self.search_all_classes(day_of_week)
            
            # Find matching class (flexible name matching)
            import re
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
                self.book_ignite()
                time.sleep(1)
                self.confirm_ignite()
                logging.info(f"Successfully booked {class_name}!")
                return True
            except:
                # Try waitlist
                try:
                    self.add_to_waitlist_ignite()
                    time.sleep(1)
                    self.confirm_ignite()
                    logging.info(f"Added to waitlist for {class_name}")
                    return True
                except:
                    return False
                    
        except Exception as e:
            logging.error(f"Failed to book: {e}")
            return False

    def _click_hour_view(self):
        """Helper function to click HOUR VIEW button using JavaScript"""
        logging.info("Waiting for HOUR VIEW button to appear...")
        
        # Wait for the button to appear (retry up to 5 times)
        hour_view_clicked = False
        for attempt in range(5):
            time.sleep(2)
            logging.info(f"HOUR VIEW attempt {attempt + 1}/5...")
            
            try:
                hour_view_clicked = self.page.evaluate("""
                    () => {
                        const buttons = Array.from(document.querySelectorAll('div.btn'));
                        for (const btn of buttons) {
                            if (btn.textContent.includes('HOUR VIEW')) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                
                if hour_view_clicked:
                    logging.info(f"✓ Clicked HOUR VIEW on attempt {attempt + 1}")
                    time.sleep(3)  # Wait for view change
                    return True
                else:
                    logging.warning(f"HOUR VIEW button not found on attempt {attempt + 1}")
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed: {e}")
        
        # All attempts failed
        logging.error("Could not find HOUR VIEW button after 5 attempts!")
        self.page.screenshot(path="hour_view_error.png")
        return False

    def check_tennis_courts(self, date=None, club_name="San Francisco"):
        """Check available tennis courts for a given date"""
        try:
            # Navigate to plan-visit page
            self.page.goto("https://bayclubconnect.com/plan-visit")
            self.page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(2)
            
            # Open club dropdown and select club
            for selector in ["app-input-select input.form-control", "input#input_select", ".form-control.clickable"]:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    time.sleep(1)
                    break
                except:
                    continue
            
            # Click club name
            for selector in [f"//span[text()='{club_name}']", f"text={club_name}"]:
                try:
                    elements = self.page.query_selector_all(selector)
                    for el in elements:
                        if el.text_content().strip() == club_name:
                            el.click()
                            time.sleep(1)
                            break
                    break
                except:
                    continue
            
            # Select Gateway - try multiple approaches for radio button
            gateway_clicked = False
            logging.info("Looking for Gateway option...")
            
            gateway_selectors = [
                "//span[contains(@class, 'i-radio')]/following-sibling::text()[contains(., 'Gateway')]/..",
                "//span[contains(@class, 'i-radio-off')]/parent::*[contains(., 'Gateway')]",
                "//*[contains(., 'Gateway') and .//span[contains(@class, 'i-radio')]]",
                "text=Gateway",
                "//span[text()='Gateway']"
            ]
            
            for selector in gateway_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    for el in elements:
                        if 'Gateway' in el.text_content():
                            el.click()
                            logging.info(f"Clicked Gateway using selector: {selector}")
                            gateway_clicked = True
                            time.sleep(2)
                            break
                    if gateway_clicked:
                        break
                except Exception as e:
                    logging.warning(f"Failed Gateway selector {selector}: {e}")
                    continue
            
            if not gateway_clicked:
                logging.error("Could not select Gateway!")
                self.page.screenshot(path="gateway_error.png")
            else:
                logging.info("Gateway selection complete")
            
            # Click Court Booking tile
            for selector in ["//span[@class='tile__name size-16 weight-900' and text()='Court Booking']", "text=Court Booking"]:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    time.sleep(2)
                    break
                except:
                    continue
            
            # Select Tennis
            for selector in ["//div[text()='Tennis']", ".category-selected:has-text('Tennis')", "text=Tennis"]:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    time.sleep(1)
                    logging.info("Selected Tennis")
                    break
                except:
                    continue
            
            # Select 90 minutes duration
            for selector in ["//span[text()='90 minutes ']", "text=90 minutes"]:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    time.sleep(1)
                    logging.info("Selected 90 minutes duration")
                    break
                except:
                    continue
            
            # Click NEXT button
            for selector in ["//button[contains(text(), 'NEXT')]", "button.btn-light-blue:has-text('NEXT')", "button:has-text('NEXT')"]:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    logging.info("Clicked NEXT button")
                    break
                except:
                    continue
            
            # Wait for calendar page to load
            logging.info("Waiting for calendar page to load...")
            try:
                self.page.wait_for_load_state("networkidle", timeout=10000)
            except:
                logging.warning("Network not idle, but continuing...")
            time.sleep(3)
            
            # Click HOUR VIEW
            self._click_hour_view()
            
            # Select the date if provided
            if date:
                target_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                today = datetime.datetime.now()
                days_diff = (target_date.date() - today.date()).days
                
                # Determine day label
                if days_diff == 0:
                    day_label = "Today"
                else:
                    day_names = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
                    day_label = day_names[target_date.weekday()]
                
                day_number = str(target_date.day)
                
                logging.info(f"Looking for day: {day_label} {day_number}")
                
                # Try to click the date
                date_selectors = [
                    f"//div[contains(@class, 'slider-item') and contains(., '{day_label}') and contains(., '{day_number}')]",
                    f".slider-item:has-text('{day_label}'):has-text('{day_number}')"
                ]
                
                clicked = False
                for selector in date_selectors:
                    try:
                        elements = self.page.query_selector_all(selector)
                        if elements:
                            elements[0].click()
                            logging.info(f"Clicked date: {day_label} {day_number}")
                            clicked = True
                            break
                    except:
                        continue
                
                if clicked:
                    # Wait longer for the date change to trigger content reload
                    logging.info("Waiting for date change to complete...")
                    time.sleep(5)  # Increased wait time
                    
                    # Wait for network activity after date change
                    try:
                        self.page.wait_for_load_state("networkidle", timeout=15000)
                        logging.info("Network settled after date selection")
                    except:
                        logging.warning("Network didn't settle, continuing anyway")
                        time.sleep(3)
                    
                    logging.info(f"Date selection complete: {day_label} {day_number}")
            
            # Parse available time slots (only clickable ones)
            # Wait for time slots to load dynamically
            try:
                logging.info("Waiting for time slots to load...")
                
                # Try multiple approaches to wait for content
                slots_found = False
                
                # Approach 1: Wait for app-court-time-slot-item
                try:
                    self.page.wait_for_selector("app-court-time-slot-item", timeout=15000)
                    logging.info("Court time slot items appeared")
                    slots_found = True
                except Exception as e1:
                    logging.warning(f"app-court-time-slot-item not found: {e1}")
                    
                    # Approach 2: Wait for .time-slot with clickable class
                    try:
                        self.page.wait_for_selector(".time-slot.clickable", timeout=15000)
                        logging.info("Clickable time slot divs appeared")
                        slots_found = True
                    except Exception as e2:
                        logging.warning(f".time-slot.clickable not found: {e2}")
                        
                        # Approach 3: Just wait for any .time-slot
                        try:
                            self.page.wait_for_selector(".time-slot", timeout=15000)
                            logging.info("Time slot divs appeared")
                            slots_found = True
                        except Exception as e3:
                            logging.warning(f".time-slot not found: {e3}")
                            
                            # Approach 4: Look for the item-tile container
                            try:
                                self.page.wait_for_selector(".item-tile", timeout=15000)
                                logging.info("Item tile container appeared")
                                slots_found = True
                            except Exception as e4:
                                logging.error(f".item-tile not found: {e4}")
                
                # Wait for text-lowercase divs with actual time content
                try:
                    self.page.wait_for_selector(".text-lowercase:has-text('AM'), .text-lowercase:has-text('PM')", timeout=10000)
                    logging.info("Text-lowercase divs with time content appeared")
                except:
                    logging.warning("Could not find text-lowercase with AM/PM")
                
                # Wait for network to be idle
                try:
                    self.page.wait_for_load_state("networkidle", timeout=5000)
                    logging.info("Network idle, all slots should be loaded")
                except:
                    logging.info("Network not idle yet, but continuing")
                
                # Final wait to ensure all dynamic content is rendered
                time.sleep(2)
                logging.info("Time slots should be fully loaded")
            except Exception as e:
                logging.warning(f"Timeout waiting for time slots: {e}")
                time.sleep(3)  # Fallback to fixed wait
            
            available_times = []
            
            try:
                # Use JavaScript to get ALL app-court-time-slot-item elements
                court_items_data = self.page.evaluate("""
                    () => {
                        const items = document.querySelectorAll('app-court-time-slot-item');
                        return Array.from(items).map(item => {
                            const timeSlot = item.querySelector('.time-slot');
                            const textDiv = item.querySelector('.text-lowercase');
                            
                            if (timeSlot && textDiv) {
                                const isDisabled = timeSlot.classList.contains('disabled');
                                const isClickable = timeSlot.classList.contains('clickable');
                                return {
                                    time: textDiv.textContent.trim(),
                                    clickable: isClickable,
                                    disabled: isDisabled
                                };
                            }
                            return null;
                        }).filter(item => item !== null);
                    }
                """)
                logging.info(f"Found {len(court_items_data)} court time slot items")
                
                # Parse JavaScript results
                if len(court_items_data) > 0:
                    import re
                    # Stricter pattern: must start with digit, proper time format
                    time_pattern = re.compile(r'^\s*(\d{1,2}):([0-9]{2})\s*-\s*(\d{1,2}):([0-9]{2})\s*([AP]M)\s*$', re.IGNORECASE)
                    
                    for i, item in enumerate(court_items_data):
                        time_text = item['time'].strip()
                        is_clickable = item['clickable']
                        is_disabled = item['disabled']
                        
                        # Log all items for debugging
                        logging.info(f"Item {i+1}/{len(court_items_data)}: '{time_text}' (clickable={is_clickable}, disabled={is_disabled})")
                        
                        # Only include clickable, non-disabled items with valid time format
                        match = time_pattern.match(time_text)
                        if match and is_clickable and not is_disabled:
                            # Validate that minutes are 00 or 30 (standard court times)
                            start_min = match.group(2)
                            end_min = match.group(4)
                            
                            # Only accept times with :00 or :30 minutes
                            if start_min in ['00', '30'] and end_min in ['00', '30']:
                                if time_text not in available_times:
                                    available_times.append(time_text)
                                    logging.info(f"✓ ADDED: {time_text}")
                            else:
                                logging.info(f"✗ Rejected (invalid minutes): {time_text}")
                        elif match:
                            logging.info(f"✗ Rejected (not clickable={is_clickable} or disabled={is_disabled}): {time_text}")
                        else:
                            logging.info(f"✗ Rejected (malformed): '{time_text}'")
                    
                    if len(available_times) > 0:
                        logging.info(f"Successfully parsed {len(available_times)} valid times")
                        return available_times
                
                logging.warning("No court time slots found")
                return []
                    
            except Exception as e:
                logging.error(f"Failed to parse time slots: {e}")
                return []
            
        except Exception as e:
            logging.error(f"Failed to check tennis courts: {e}")
            return False

    def book_tennis_court(self, date=None, time_slot=None, club_name="San Francisco"):
        """Book a tennis court for a given date and time"""
        try:
            # Navigate to plan-visit page
            self.page.goto("https://bayclubconnect.com/plan-visit")
            self.page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(2)
            
            # Open club dropdown and select club
            for selector in ["app-input-select input.form-control", "input#input_select", ".form-control.clickable"]:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    time.sleep(1)
                    break
                except:
                    continue
            
            # Click club name
            for selector in [f"//span[text()='{club_name}']", f"text={club_name}"]:
                try:
                    elements = self.page.query_selector_all(selector)
                    for el in elements:
                        if el.text_content().strip() == club_name:
                            el.click()
                            time.sleep(1)
                            break
                    break
                except:
                    continue
            
            # Select Gateway - try multiple approaches for radio button
            gateway_clicked = False
            logging.info("Looking for Gateway option...")
            
            gateway_selectors = [
                "//span[contains(@class, 'i-radio')]/following-sibling::text()[contains(., 'Gateway')]/..",
                "//span[contains(@class, 'i-radio-off')]/parent::*[contains(., 'Gateway')]",
                "//*[contains(., 'Gateway') and .//span[contains(@class, 'i-radio')]]",
                "text=Gateway",
                "//span[text()='Gateway']"
            ]
            
            for selector in gateway_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    for el in elements:
                        if 'Gateway' in el.text_content():
                            el.click()
                            logging.info(f"Clicked Gateway using selector: {selector}")
                            gateway_clicked = True
                            time.sleep(2)
                            break
                    if gateway_clicked:
                        break
                except Exception as e:
                    logging.warning(f"Failed Gateway selector {selector}: {e}")
                    continue
            
            if not gateway_clicked:
                logging.error("Could not select Gateway!")
                self.page.screenshot(path="gateway_error.png")
            else:
                logging.info("Gateway selection complete")
            
            # Click Court Booking tile
            for selector in ["//span[@class='tile__name size-16 weight-900' and text()='Court Booking']", "text=Court Booking"]:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    time.sleep(2)
                    break
                except:
                    continue
            
            # Select Tennis
            for selector in ["//div[text()='Tennis']", ".category-selected:has-text('Tennis')", "text=Tennis"]:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    time.sleep(1)
                    logging.info("Selected Tennis")
                    break
                except:
                    continue
            
            # Select 90 minutes duration
            for selector in ["//span[text()='90 minutes ']", "text=90 minutes"]:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    time.sleep(1)
                    logging.info("Selected 90 minutes duration")
                    break
                except:
                    continue
            
            # Click NEXT button
            for selector in ["//button[contains(text(), 'NEXT')]", "button.btn-light-blue:has-text('NEXT')", "button:has-text('NEXT')"]:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    logging.info("Clicked NEXT button")
                    break
                except:
                    continue
            
            # Wait for calendar page to load
            logging.info("Waiting for calendar page to load...")
            try:
                self.page.wait_for_load_state("networkidle", timeout=10000)
            except:
                logging.warning("Network not idle, but continuing...")
            time.sleep(3)
            
            # Click HOUR VIEW
            self._click_hour_view()
            
            # Select the date if provided
            if date:
                target_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                today = datetime.datetime.now()
                days_diff = (target_date.date() - today.date()).days
                
                # Determine day label
                if days_diff == 0:
                    day_label = "Today"
                else:
                    day_names = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
                    day_label = day_names[target_date.weekday()]
                
                day_number = str(target_date.day)
                
                logging.info(f"Looking for day: {day_label} {day_number}")
                
                # Try to click the date
                date_selectors = [
                    f"//div[contains(@class, 'slider-item') and contains(., '{day_label}') and contains(., '{day_number}')]",
                    f".slider-item:has-text('{day_label}'):has-text('{day_number}')"
                ]
                
                for selector in date_selectors:
                    try:
                        elements = self.page.query_selector_all(selector)
                        if elements:
                            elements[0].click()
                            time.sleep(2)
                            logging.info(f"Selected date: {day_label} {day_number}")
                            break
                    except:
                        continue
            
            # Click the specific time slot if provided
            if time_slot:
                time.sleep(2)  # Wait for times to load
                logging.info(f"Looking for time slot: {time_slot}")
                
                # Normalize the time slot search string (remove extra spaces)
                import re
                normalized_search = re.sub(r'\s+', ' ', time_slot.strip())
                logging.info(f"Normalized search: {normalized_search}")
                
                try:
                    time_slots = self.page.query_selector_all(".time-slot")
                    logging.info(f"Found {len(time_slots)} total time-slot elements")
                    clicked = False
                    
                    for i, slot in enumerate(time_slots):
                        try:
                            slot_text = slot.text_content().strip()
                            # Normalize the slot text (remove extra spaces)
                            normalized_slot = re.sub(r'\s+', ' ', slot_text)
                            
                            logging.info(f"Slot {i+1}: '{normalized_slot}' (original: '{slot_text}')")
                            
                            # Check if clickable before matching
                            class_name = slot.get_attribute("class") or ""
                            is_disabled = "disabled" in class_name.lower()
                            is_clickable = "clickable" in class_name.lower()
                            
                            try:
                                is_visible = slot.is_visible()
                            except:
                                is_visible = True
                            
                            # Flexible matching: normalize both strings and compare
                            if normalized_search.lower() in normalized_slot.lower() or normalized_slot.lower() in normalized_search.lower():
                                logging.info(f"  → MATCH! clickable={is_clickable}, disabled={is_disabled}, visible={is_visible}")
                                
                                if is_visible and not is_disabled and is_clickable:
                                    slot.click()
                                    time.sleep(2)
                                    logging.info(f"✓ Clicked time slot: {slot_text}")
                                    clicked = True
                                    break
                                else:
                                    logging.warning(f"  → Match found but not clickable (clickable={is_clickable}, disabled={is_disabled}, visible={is_visible})")
                        except Exception as e:
                            logging.warning(f"Error checking slot {i+1}: {e}")
                            continue
                    
                    if not clicked:
                        logging.error(f"Could not find or click time slot: {time_slot}")
                        self.page.screenshot(path="time_slot_error.png")
                        return False
                        
                except Exception as e:
                    logging.error(f"Failed to click time slot: {e}")
                    self.page.screenshot(path="time_slot_error.png")
                    return False
            
            # Click NEXT button to proceed to player selection
            for selector in ["//button[contains(text(), 'NEXT')]", "button.btn-light-blue:has-text('NEXT')", "button:has-text('NEXT')"]:
                try:
                    self.page.wait_for_selector(selector, timeout=5000).click()
                    time.sleep(2)
                    logging.info("Clicked NEXT button")
                    break
                except:
                    continue
            
            # Click on member (Samuel Wang or whoever is shown)
            logging.info("Looking for member to select...")
            time.sleep(2)  # Wait for member list to load
            
            member_clicked = False
            
            # Try using JavaScript to click the clickable div inside app-racquet-sports-person
            try:
                member_clicked = self.page.evaluate("""
                    () => {
                        const person = document.querySelector('app-racquet-sports-person');
                        if (person) {
                            const clickableDiv = person.querySelector('div.clickable');
                            if (clickableDiv) {
                                clickableDiv.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                
                if member_clicked:
                    logging.info("Clicked member using JavaScript")
                    time.sleep(2)
                else:
                    logging.warning("Could not find member with JavaScript")
            except Exception as e:
                logging.warning(f"JavaScript click failed: {e}")
            
            # Fallback to CSS selectors
            if not member_clicked:
                member_selectors = [
                    "app-racquet-sports-person .clickable",
                    ".my-1.clickable",
                    "div.clickable",
                    "app-racquet-sports-person div.my-1"
                ]
                
                for selector in member_selectors:
                    try:
                        self.page.wait_for_selector(selector, timeout=5000).click()
                        time.sleep(2)
                        logging.info(f"Clicked member using selector: {selector}")
                        member_clicked = True
                        break
                    except:
                        continue
            
            if not member_clicked:
                logging.warning("Could not click member, trying to proceed anyway")
            else:
                # Wait longer for CONFIRM BOOKING button to appear after selecting member
                logging.info("Waiting for CONFIRM BOOKING button to appear...")
                time.sleep(3)
            
            # Take a screenshot before attempting to click CONFIRM BOOKING
            try:
                self.page.screenshot(path="before_confirm_booking.png")
                logging.info("Saved screenshot: before_confirm_booking.png")
            except:
                pass
            
            # Click CONFIRM BOOKING button - use JavaScript (most reliable)
            logging.info("Looking for CONFIRM BOOKING button...")
            
            confirmed = False
            try:
                confirmed = self.page.evaluate("""
                    () => {
                        // Find button containing CONFIRM BOOKING text
                        const buttons = Array.from(document.querySelectorAll('button'));
                        for (const btn of buttons) {
                            if (btn.textContent.includes('CONFIRM BOOKING')) {
                                btn.click();
                                return true;
                            }
                        }
                        
                        // Try finding by span text inside button
                        const spans = Array.from(document.querySelectorAll('button span'));
                        for (const span of spans) {
                            if (span.textContent.includes('CONFIRM BOOKING')) {
                                span.parentElement.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                
                if confirmed:
                    logging.info("Clicked CONFIRM BOOKING using JavaScript")
                    time.sleep(2)
                else:
                    logging.warning("Could not find CONFIRM BOOKING with JavaScript")
            except Exception as e:
                logging.warning(f"JavaScript click failed: {e}")
            
            # Fallback to selectors
            if not confirmed:
                confirm_selectors = [
                    "//button[.//span[text()='CONFIRM BOOKING']]",
                    "//button[contains(@class, 'darker-blue-bg')]//span[text()='CONFIRM BOOKING']",
                    "button:has-text('CONFIRM BOOKING')",
                    "//button[contains(text(), 'CONFIRM BOOKING')]",
                    "text=CONFIRM BOOKING"
                ]
                
                for selector in confirm_selectors:
                    try:
                        self.page.wait_for_selector(selector, timeout=5000).click()
                        time.sleep(2)
                        logging.info(f"Clicked CONFIRM BOOKING using selector: {selector}")
                        confirmed = True
                        break
                    except Exception as e:
                        logging.warning(f"Selector {selector} failed: {e}")
                        continue
            
            if not confirmed:
                logging.error("Could not click CONFIRM BOOKING button!")
                self.page.screenshot(path="confirm_booking_error.png")
                return False
            
            logging.info("Successfully booked tennis court")
            return True
            
        except Exception as e:
            logging.error(f"Failed to book tennis court: {e}")
            self.page.screenshot(path="court_booking_error.png")
            return False

    def save_screenshot(self, filename='screen.png', enabled=True, delay=0):
        """Save a screenshot of the current page"""
        if enabled:
            time.sleep(delay)
            self.page.screenshot(path=filename)
