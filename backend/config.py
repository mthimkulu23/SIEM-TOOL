import os
from dotenv import load_dotenv

# Load environment variables from a .env file.
# This should be at the very top to ensure variables are loaded
# before the Config class attempts to use os.getenv().
load_dotenv()

class Config:
    """
    Configuration settings for the SIEM backend application.
    These values are loaded from environment variables, with default fallbacks
    for easier local development.
    """
    def __init__(self):
        # MongoDB Database Configuration
        # CRITICAL: Renamed from MONGO_URI to MONGODB_URI to match db_client.py expectation.
        # Prioritize loading from environment variable (Render environment)
        # The default value is provided for local testing if the env var isn't set.
        self.MONGODB_URI = os.getenv(
            "MONGODB_URI",
            "mongodb+srv://thabang23mthimkulu:66F13mOoZCZAQ2O8@cluster0.wam26ka.mongodb.net/siem_database"
        )
        
        # MongoDB database name
        self.MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "siem_database") # Also use os.getenv for this

        # Collection names (can remain class-level or move to self. if preferred)
        self.LOGS_COLLECTION_NAME = "logs"
        self.ALERTS_COLLECTION_NAME = "alerts"

        # Anomaly Detection Configuration
        self.FAILED_LOGIN_THRESHOLD = int(os.getenv("FAILED_LOGIN_THRESHOLD", 3))
        self.FAILED_LOGIN_TIME_WINDOW_SECONDS = int(os.getenv("FAILED_LOGIN_TIME_WINDOW_SECONDS", 60))

        # API Configuration
        # Render provides the PORT environment variable. Ensure it's an integer.
        self.API_HOST = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT = int(os.getenv("PORT", 5000))

        # Flask Secret Key for security (CRITICAL for production!)
        # CHANGE THIS DEFAULT IN YOUR RENDER ENVIRONMENT VARIABLES
        self.SECRET_KEY = os.getenv("SECRET_KEY", "a_very_long_and_random_string_replace_me_in_prod!")

        # Log Ingestion Configuration (conceptual)
        self.SYSLOG_LISTENER_PORT = int(os.getenv("SYSLOG_LISTENER_PORT", 514))
        self.KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")