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
        """Login to Bay Club with provided credentials"""
        try:
            # Wait for and fill username
            logging.info("Looking for username field...")
            username_field = self.page.wait_for_selector("#username", timeout=15000)
            username_field.fill(user_name)
            logging.info("Username filled")
            
            # Wait for and fill password
            logging.info("Looking for password field...")
            password_field = self.page.wait_for_selector("#password", timeout=15000)
            password_field.fill(user_password)
            logging.info("Password filled")
            
            # Try multiple possible login button selectors
            login_button = None
            login_selectors = [
                "xpath=/html/body/app-root/div/app-login/div/app-login-connect/div[1]/div/div/div/form/button",
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Login')",
                "button:has-text('Sign In')"
            ]
            
            for selector in login_selectors:
                try:
                    logging.info(f"Trying login button selector: {selector}")
                    login_button = self.page.wait_for_selector(selector, timeout=5000)
                    break
                except PlaywrightTimeoutError:
                    continue
            
            if not login_button:
                # Take screenshot for debugging
                self.page.screenshot(path="login_debug.png")
                raise PlaywrightTimeoutError("Could not find login button with any selector")
            
            logging.info("Clicking login button...")
            login_button.click()
            
            # Wait for page to load after login - try multiple approaches
            logging.info("Waiting for page to load after login...")
            try:
                # Wait for either network idle or a specific element that indicates successful login
                self.page.wait_for_load_state("networkidle", timeout=10000)
                logging.info("Page loaded (networkidle)")
            except PlaywrightTimeoutError:
                logging.info("Networkidle timeout, trying to wait for specific elements...")
                try:
                    # Look for elements that indicate successful login
                    self.page.wait_for_selector("text=Classes", timeout=10000)
                    logging.info("Found 'Classes' text - login successful")
                except PlaywrightTimeoutError:
                    try:
                        # Try waiting for any class-related element
                        self.page.wait_for_selector("[class*='class']", timeout=5000)
                        logging.info("Found class-related element - login successful")
                    except PlaywrightTimeoutError:
                        logging.warning("Could not confirm login success, but continuing...")
            
            # Small delay to ensure page is fully loaded
            time.sleep(2)
            
            # Select Bay Club San Francisco location
            self.select_location("San Francisco")
            
            
            logging.info("Login process completed")
            
        except PlaywrightTimeoutError as e:
            logging.error(f"Login failed: {e}")
            self.page.screenshot(path="login_error.png")
            raise

    def select_location(self, location_name="San Francisco"):
        """Select the Bay Club location from the dropdown"""
        try:
            logging.info(f"Looking for location dropdown for {location_name}...")
            
            # First, check if we're already on the correct location
            current_location_selectors = [
                "//*[contains(text(), 'San Francisco')]",
                "//*[contains(text(), 'Bay Club San Francisco')]",
                "//*[contains(text(), 'Club: San Francisco')]"
            ]
            
            for selector in current_location_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    for element in elements:
                        text = element.text_content().strip()
                        if "San Francisco" in text and "Bay Club" in text:
                            logging.info(f"Already on San Francisco location: {text}")
                            return True
                except Exception as e:
                    logging.info(f"Location check selector {selector} failed: {e}")
                    continue
            
            # If not already on San Francisco, try to open the dropdown
            dropdown_selectors = [
                "[dropdown]",
                ".btn-group .select-border",
                ".clickable.select-border",
                "span[dropdowntoggle]"
            ]
            
            dropdown_opened = False
            for selector in dropdown_selectors:
                try:
                    logging.info(f"Trying to open dropdown with selector: {selector}")
                    dropdown = self.page.wait_for_selector(selector, timeout=5000)
                    dropdown.click()
                    time.sleep(1)  # Wait for dropdown to open
                    dropdown_opened = True
                    logging.info("Dropdown opened successfully")
                    break
                except Exception as e:
                    logging.info(f"Dropdown selector {selector} failed: {e}")
                    continue
            
            if not dropdown_opened:
                logging.warning("Could not open location dropdown - might already be on San Francisco")
                # Check if we can find San Francisco text on the page
                sf_elements = self.page.query_selector_all("//*[contains(text(), 'San Francisco')]")
                if sf_elements:
                    logging.info("Found San Francisco text on page - assuming correct location")
                    return True
                else:
                    # Check for any Bay Club location text
                    bay_club_elements = self.page.query_selector_all("//*[contains(text(), 'Bay Club')]")
                    if bay_club_elements:
                        for element in bay_club_elements:
                            text = element.text_content().strip()
                            logging.info(f"Found Bay Club text: {text}")
                        logging.info("Found Bay Club text - assuming correct location")
                        return True
                    else:
                        logging.warning("No location text found - continuing anyway")
                        return False
            
            # Step 1: Click on the "San Francisco" span to expand the submenu
            logging.info("Step 1: Looking for San Francisco span to expand submenu...")
            sf_span_selectors = [
                "//li[contains(@class, 'ml-2')]//span[text()='San Francisco']",
                "//span[text()='San Francisco']",
                "text=San Francisco"
            ]
            
            sf_span_element = None
            for selector in sf_span_selectors:
                try:
                    logging.info(f"Looking for SF span with selector: {selector}")
                    elements = self.page.query_selector_all(selector)
                    if elements:
                        for element in elements:
                            text = element.text_content().strip()
                            if text == 'San Francisco':
                                sf_span_element = element
                                logging.info(f"Found San Francisco span: '{text}'")
                                break
                        if sf_span_element:
                            break
                except Exception as e:
                    logging.info(f"SF span selector {selector} failed: {e}")
                    continue
            
            if not sf_span_element:
                logging.warning("Could not find San Francisco span in dropdown")
                self.page.screenshot(path="location_sf_span_debug.png")
                return
            
            # Click on the San Francisco span to expand submenu
            try:
                logging.info("Clicking on San Francisco span to expand submenu...")
                # Try different click methods for the span
                try:
                    sf_span_element.click()
                    logging.info("Regular click successful")
                except Exception as e1:
                    logging.info(f"Regular click failed: {e1}, trying force click...")
                    try:
                        sf_span_element.click(force=True)
                        logging.info("Force click successful")
                    except Exception as e2:
                        logging.info(f"Force click failed: {e2}, trying JavaScript click...")
                        self.page.evaluate("element => element.click()", sf_span_element)
                        logging.info("JavaScript click successful")
                
                time.sleep(1)  # Wait for submenu to expand
                logging.info("San Francisco submenu expanded")
            except Exception as e:
                logging.warning(f"Failed to click San Francisco span: {e}")
                return
            
            # Step 2: Click on the specific San Francisco option in the submenu
            logging.info("Step 2: Looking for San Francisco option in submenu...")
            sf_option_selectors = [
                "//div[@class='w-100 black' and text()='San Francisco']",
                "//div[contains(@class, 'w-100') and contains(@class, 'black') and text()='San Francisco']",
                "//*[contains(@class, 'w-100') and text()='San Francisco']",
                "//*[text()='San Francisco' and contains(@class, 'black')]"
            ]
            
            sf_option_element = None
            for selector in sf_option_selectors:
                try:
                    logging.info(f"Looking for SF option with selector: {selector}")
                    elements = self.page.query_selector_all(selector)
                    if elements:
                        logging.info(f"Found {len(elements)} elements with this selector")
                        for i, element in enumerate(elements):
                            text = element.text_content().strip()
                            class_attr = element.get_attribute('class') or ''
                            logging.info(f"Element {i}: text='{text}', class='{class_attr}'")
                            # Make sure it's exactly "San Francisco" and not "South San Francisco"
                            if text == 'San Francisco' and 'w-100' in class_attr:
                                sf_option_element = element
                                logging.info(f"Found exact San Francisco option: '{text}'")
                                break
                        if sf_option_element:
                            break
                except Exception as e:
                    logging.info(f"SF option selector {selector} failed: {e}")
                    continue
            
            if not sf_option_element:
                logging.warning("Could not find San Francisco option in submenu")
                self.page.screenshot(path="location_sf_option_debug.png")
                return
            
            # Click on the San Francisco option
            try:
                logging.info("Clicking on San Francisco option in submenu...")
                sf_option_element.click()
                time.sleep(2)  # Wait for selection to take effect
                logging.info("San Francisco location selected successfully")
            except Exception as e:
                logging.info(f"Regular click failed: {e}, trying force click...")
                try:
                    # Try force click for hidden elements
                    sf_option_element.click(force=True)
                    time.sleep(2)
                    logging.info("San Francisco location selected via force click")
                except Exception as e2:
                    logging.info(f"Force click failed: {e2}, trying JavaScript click...")
                    try:
                        # Try JavaScript click as final fallback
                        self.page.evaluate("element => element.click()", sf_option_element)
                        time.sleep(2)
                        logging.info("San Francisco location selected via JavaScript")
                    except Exception as e3:
                        logging.warning(f"All click methods failed: {e3}")
                        return
            
        except Exception as e:
            logging.warning(f"Location selection failed: {e}")
            self.page.screenshot(path="location_error.png")

    def select_day(self, day_of_week, logging):
        """Select the appropriate day based on current day of week"""
        # Map day numbers to day codes (0=Monday, 6=Sunday)
        day_codes = {
            0: "Mo",  # Monday
            1: "Tu",  # Tuesday
            2: "We",  # Wednesday
            3: "Th",  # Thursday
            4: "Fr",  # Friday
            5: "Sa",  # Saturday
            6: "Su"   # Sunday
        }
        
        day_names = {
            0: "Monday",
            1: "Tuesday", 
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday"
        }
        
        # Get the day code for the current day
        day_code = day_codes.get(day_of_week, "Mo")
        day_name = day_names.get(day_of_week, "Monday")
        
        logging.info(f"Today is {day_name}, looking for Ignite classes...")
        
        # Try to find and click on the day selector
        try:
            # Look for day selector elements - use simpler patterns based on what we found
            day_selectors = [
                f"//*[text()='{day_code}']",  # Exact match for day code
                f"//*[text()='{day_name}']",  # Exact match for day name
                f"//*[contains(text(), '{day_code}') and string-length(text()) < 10]",  # Short text containing day code
                f"//*[contains(text(), '{day_name}') and string-length(text()) < 20]",  # Short text containing day name
                f"//button[contains(text(), '{day_code}')]",
                f"//button[contains(text(), '{day_name}')]",
                f"//div[contains(text(), '{day_code}')]",
                f"//div[contains(text(), '{day_name}')]",
                f"//span[contains(text(), '{day_code}')]",
                f"//span[contains(text(), '{day_name}')]"
            ]
            
            day_element = None
            for selector in day_selectors:
                try:
                    logging.info(f"Looking for day selector: {selector}")
                    elements = self.page.query_selector_all(selector)
                    if elements:
                        for element in elements:
                            text = element.text_content().strip()
                            # Make sure it's not CSS content and is actually clickable
                            if (day_name in text or day_code in text) and len(text) < 100 and not text.startswith(':'):
                                # Check if element is visible and clickable
                                try:
                                    is_visible = element.is_visible()
                                    is_enabled = element.is_enabled()
                                    if is_visible and is_enabled:
                                        day_element = element
                                        logging.info(f"Found clickable day element: '{text}'")
                                        break
                                except:
                                    # If we can't check visibility, try it anyway
                                    day_element = element
                                    logging.info(f"Found day element: '{text}'")
                                    break
                        if day_element:
                            break
                except Exception as e:
                    logging.info(f"Day selector {selector} failed: {e}")
                    continue
            
            if day_element:
                try:
                    day_element.click()
                    logging.info(f"Clicked on {day_name} day selector")
                    # Wait for page to update
                    import time
                    time.sleep(2)
                    return True
                except Exception as e:
                    logging.info(f"Failed to click day selector: {e}")
                    return True  # Continue anyway
            else:
                logging.info(f"Could not find {day_name} day selector, continuing with current view")
                return True
                
        except Exception as e:
            logging.info(f"Error in day selection: {e}")
            return True  # Continue anyway

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

    def save_screenshot(self, filename='screen.png', enabled=True, delay=0):
        """Save a screenshot of the current page"""
        if enabled:
            time.sleep(delay)
            self.page.screenshot(path=filename)
