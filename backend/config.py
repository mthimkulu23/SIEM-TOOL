# backend/config.py
import os

class Config:
    """
    Configuration settings for the SIEM backend application.
    These values would typically be loaded from environment variables in a production setup.
    """
    # MongoDB Database Configuration
    # In a production setup, you would load this from an environment variable:
    # MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/siem_database")
    MONGO_URI = "mongodb+srv://thabang23mthimkulu:66F13mOoZCZAQ2O8@cluster0.wam26ka.mongodb.net/siem_database"
    DB_NAME = "siem_database"
    LOGS_COLLECTION_NAME = "logs"
    ALERTS_COLLECTION_NAME = "alerts"

    # Anomaly Detection Configuration
    # Number of failed login attempts within the time window to trigger an alert
    FAILED_LOGIN_THRESHOLD = 3
    # Time window (in seconds) for the failed login attempts to be considered a burst
    FAILED_LOGIN_TIME_WINDOW_SECONDS = 60

    # API Configuration
    # 0.0.0.0 makes the Flask app accessible from other devices on the local network.
    # For production, this would typically be set by the WSGI server (Gunicorn) itself.
    API_HOST = "0.0.0.0"
    API_PORT = 5000

    # Log Ingestion Configuration (conceptual)
    # Example: Port for a Syslog listener
    SYSLOG_LISTENER_PORT = 514
    # Kafka broker address (if using Kafka for ingestion)
    KAFKA_BROKER = "localhost:9092"