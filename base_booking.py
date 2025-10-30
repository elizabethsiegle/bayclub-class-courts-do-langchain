"""
Base Bay Club Booking Module

This module provides the foundation class for all Bay Club booking operations.
Handles authentication, browser management, and common functionality.

Author: Bay Club Booking Team
License: MIT
"""

import os
import time
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


class BaseBayClubBooking:
    """
    Base class for Bay Club booking operations.
    
    Provides common functionality for authentication, browser management,
    and location selection that is shared across different booking types.
    """
    
    def __init__(self, target_url, headless=False):
        """
        Initialize the base booking class.
        
        Args:
            target_url (str): The URL to navigate to after login
            headless (bool): Whether to run browser in headless mode
        """
        self.target_url = target_url
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self):
        """Context manager entry"""
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
    
    def start_browser(self):
        """Start the Playwright browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        
        # Set a longer timeout for page operations
        self.page.set_default_timeout(30000)  # 30 seconds
        
        self.logger.info("Browser started successfully")
    
    def cleanup(self):
        """Clean up browser resources"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.logger.info("Browser cleanup completed")
    
    def login(self, username, password):
        """
        Log into Bay Club Connect
        
        Args:
            username (str): Bay Club username
            password (str): Bay Club password
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            self.logger.info("Navigating to Bay Club Connect login page...")
            self.page.goto("https://bayclubconnect.com/login")
            
            # Wait for login form
            self.page.wait_for_selector("input[name='username']", timeout=15000)
            
            # Fill in credentials
            self.page.fill("input[name='username']", username)
            self.page.fill("input[name='password']", password)
            
            # Submit login
            self.page.click("button[type='submit']")
            
            # Wait for redirect to dashboard
            self.page.wait_for_url("**/dashboard", timeout=15000)
            self.logger.info("Login successful")
            
            return True
            
        except PlaywrightTimeoutError as e:
            self.logger.error(f"Login timeout: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False
    
    def select_location(self, location="SF"):
        """
        Select Bay Club location
        
        Args:
            location (str): Location code (default: "SF")
            
        Returns:
            bool: True if location selected successfully
        """
        try:
            # Look for location dropdown or selector
            location_selectors = [
                f"text={location}",
                f"[data-location='{location}']",
                f".location-{location.lower()}",
                "select[name='location']"
            ]
            
            for selector in location_selectors:
                try:
                    if self.page.is_visible(selector):
                        self.page.click(selector)
                        self.logger.info(f"Selected location: {location}")
                        time.sleep(2)
                        return True
                except:
                    continue
            
            # If no specific location selector, try to find and click SF location
            sf_elements = self.page.query_selector_all("text=/San Francisco|SF/i")
            for element in sf_elements:
                try:
                    if element.is_visible():
                        element.click()
                        self.logger.info("Selected SF location")
                        time.sleep(2)
                        return True
                except:
                    continue
            
            self.logger.warning(f"Could not find location selector for {location}")
            return True  # Continue anyway, might already be on correct location
            
        except Exception as e:
            self.logger.error(f"Error selecting location: {e}")
            return False
    
    def navigate_to_target(self):
        """
        Navigate to the target URL after login
        
        Returns:
            bool: True if navigation successful
        """
        try:
            self.logger.info(f"Navigating to {self.target_url}")
            self.page.goto(self.target_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Check if we're on the right page
            current_url = self.page.url
            if self.target_url.split('/')[-1] in current_url:
                self.logger.info("Successfully navigated to target page")
                return True
            else:
                self.logger.warning(f"May not be on correct page. Current URL: {current_url}")
                return True  # Continue anyway
                
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False
    
    def wait_for_element(self, selector, timeout=10000):
        """
        Wait for an element to be visible with error handling
        
        Args:
            selector (str): CSS selector or text selector
            timeout (int): Timeout in milliseconds
            
        Returns:
            bool: True if element found
        """
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            self.logger.warning(f"Timeout waiting for element: {selector}")
            return False
        except Exception as e:
            self.logger.error(f"Error waiting for element {selector}: {e}")
            return False
    
    def is_logged_in(self):
        """
        Check if user is currently logged in
        
        Returns:
            bool: True if logged in
        """
        try:
            # Check for logout button or user profile elements
            logout_selectors = [
                "text=Logout",
                "text=Sign Out", 
                ".user-profile",
                ".logout-btn",
                "[href*='logout']"
            ]
            
            for selector in logout_selectors:
                if self.page.is_visible(selector):
                    return True
            
            # Check if we're on dashboard
            if "dashboard" in self.page.url.lower():
                return True
            
            return False
            
        except Exception:
            return False