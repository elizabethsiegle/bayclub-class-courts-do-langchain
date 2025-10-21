#!/usr/bin/python3

"""
Configuration management for Bay Club Booking System

Handles environment variables and configuration settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the Bay Club booking system"""
    
    # Bay Club credentials
    BAY_CLUB_USERNAME = os.getenv("BAY_CLUB_USERNAME", "")
    BAY_CLUB_PASSWORD = os.getenv("BAY_CLUB_PASSWORD", "")
    
    # Gradient API key
    DIGITALOCEAN_INFERENCE_KEY = os.getenv("DIGITALOCEAN_INFERENCE_KEY", "")
    
    # Default booking settings
    DEFAULT_TIME = "7:00"
    DEFAULT_MERIDIEM = "AM"
    DEFAULT_HEADLESS = False
    
    # Common Ignite class times
    IGNITE_TIMES = ["6:30", "7:00", "7:30", "8:00", "8:30", "9:00"]
    
    @classmethod
    def validate_credentials(cls):
        """Validate that required credentials are set"""
        missing = []
        
        if not cls.BAY_CLUB_USERNAME:
            missing.append("BAY_CLUB_USERNAME")
        if not cls.BAY_CLUB_PASSWORD:
            missing.append("BAY_CLUB_PASSWORD")
        if not cls.DIGITALOCEAN_INFERENCE_KEY:
            missing.append("DIGITALOCEAN_INFERENCE_KEY")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
    
    @classmethod
    def get_credentials_status(cls):
        """Get status of credentials"""
        return {
            "bay_club_username": "✅ Set" if cls.BAY_CLUB_USERNAME else "❌ Not set",
            "bay_club_password": "✅ Set" if cls.BAY_CLUB_PASSWORD else "❌ Not set",
            "gradient_api_key": "✅ Set" if cls.DIGITALOCEAN_INFERENCE_KEY else "❌ Not set"
        }

# Create a sample .env file if it doesn't exist
def create_sample_env():
    """Create a sample .env file"""
    env_content = """# Bay Club Credentials
BAY_CLUB_USERNAME=your_username_here
BAY_CLUB_PASSWORD=your_password_here

# Gradient API Key
DIGITALOCEAN_INFERENCE_KEY=your_gradient_api_key_here
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("📝 Created .env file with sample values")
        print("   Please edit .env with your actual credentials")
    else:
        print("📝 .env file already exists")

if __name__ == "__main__":
    # Test configuration
    try:
        Config.validate_credentials()
        print("✅ All credentials are properly configured")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nTo fix this:")
        print("1. Create a .env file with your credentials")
        print("2. Or set environment variables directly")
        create_sample_env()
    
    # Show current status
    status = Config.get_credentials_status()
    print("\n📊 Current configuration status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
