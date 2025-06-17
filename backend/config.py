# backend/config.py
import os

class Config:
    """
    Configuration settings for the SIEM backend application.
    These values would typically be loaded from environment variables in a production setup.
    """
    # MongoDB Database Configuration
    # Prioritize loading from environment variable for production deployment
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://thabang23mthimkulu:66F13mOoZCZAQ2O8@cluster0.wam26ka.mongodb.net/siem_database")
    # The second argument to os.getenv() is the default value if the env var is not set.
    # You can leave your hardcoded cloud string here as the default for local testing,
    # or change it to a local MongoDB URI if you prefer.
    # For ultimate security, you might make the default None and ensure the env var is always set.

    DB_NAME = "siem_database"
    LOGS_COLLECTION_NAME = "logs"
    ALERTS_COLLECTION_NAME = "alerts"

    # Anomaly Detection Configuration
    FAILED_LOGIN_THRESHOLD = 3
    FAILED_LOGIN_TIME_WINDOW_SECONDS = 60

    # API Configuration
    API_HOST = "0.0.0.0"
    API_PORT = 5000

    # Log Ingestion Configuration (conceptual)
    SYSLOG_LISTENER_PORT = 514
    KAFKA_BROKER = "localhost:9092"