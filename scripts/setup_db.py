# scripts/setup_db.py

# from pymongo import MongoClient, ASCENDING, DESCENDING
# from pymongo.errors import CollectionInvalid, ConnectionFailure

from backend.config import Config

def setup_mongodb():
    """
    Connects to MongoDB and ensures necessary collections and indexes are set up.
    This script should be run once during project setup.
    """
    config = Config()
    print(f"Attempting to connect to MongoDB at: {config.MONGO_URI}")

    # --- Real MongoDB Setup (Uncomment in a real project) ---
    # try:
    #     client = MongoClient(config.MONGO_URI)
    #     # The ping command is cheap and does not require auth.
    #     client.admin.command('ping')
    #     db = client[config.DB_NAME]
    #     print(f"Successfully connected to MongoDB database: '{config.DB_NAME}'")

    #     # Ensure 'logs' collection exists and create indexes
    #     try:
    #         db.create_collection(config.LOGS_COLLECTION_NAME)
    #         print(f"Collection '{config.LOGS_COLLECTION_NAME}' created.")
    #     except CollectionInvalid:
    #         print(f"Collection '{config.LOGS_COLLECTION_NAME}' already exists.")

    #     print(f"Ensuring indexes for '{config.LOGS_COLLECTION_NAME}'...")
    #     db[config.LOGS_COLLECTION_NAME].create_index([("timestamp", DESCENDING)], name="timestamp_desc_idx", background=True)
    #     db[config.LOGS_COLLECTION_NAME].create_index([("level", ASCENDING)], name="level_asc_idx", background=True)
    #     db[config.LOGS_COLLECTION_NAME].create_index([("source", ASCENDING)], name="source_asc_idx", background=True)
    #     db[config.LOGS_COLLECTION_NAME].create_index([("ip_address", ASCENDING)], name="ip_address_asc_idx", sparse=True, background=True)
    #     db[config.LOGS_COLLECTION_NAME].create_index([("message", ASCENDING)], name="message_text_idx", background=True) # For full-text search conceptual
    #     print(f"Indexes for '{config.LOGS_COLLECTION_NAME}' ensured.")

    #     # Ensure 'alerts' collection exists and create indexes
    #     try:
    #         db.create_collection(config.ALERTS_COLLECTION_NAME)
    #         print(f"Collection '{config.ALERTS_COLLECTION_NAME}' created.")
    #     except CollectionInvalid:
    #         print(f"Collection '{config.ALERTS_COLLECTION_NAME}' already exists.")

    #     print(f"Ensuring indexes for '{config.ALERTS_COLLECTION_NAME}'...")
    #     db[config.ALERTS_COLLECTION_NAME].create_index([("timestamp", DESCENDING)], name="timestamp_desc_idx", background=True)
    #     db[config.ALERTS_COLLECTION_NAME].create_index([("severity", ASCENDING)], name="severity_asc_idx", background=True)
    #     db[config.ALERTS_COLLECTION_NAME].create_index([("status", ASCENDING)], name="status_asc_idx", background=True)
    #     db[config.ALERTS_COLLECTION_NAME].create_index([("alert_type", ASCENDING)], name="alert_type_asc_idx", background=True)
    #     print(f"Indexes for '{config.ALERTS_COLLECTION_NAME}' ensured.")

    #     print("\nMongoDB setup complete.")

    # except ConnectionFailure as e:
    #     print(f"ERROR: Could not connect to MongoDB. Please ensure the MongoDB server is running at {config.MONGO_URI}. Details: {e}")
    # except Exception as e:
    #     print(f"An unexpected error occurred during MongoDB setup: {e}")
    # -------------------------------------------------------------

    print("Conceptual: MongoDB setup script. No actual connection made.")
    print("Please ensure MongoDB is running and accessible at the URI specified in backend/config.py.")
    print("In a real project, uncomment the 'pymongo' imports and the 'Real MongoDB Setup' block.")

if __name__ == "__main__":
    setup_mongodb()
