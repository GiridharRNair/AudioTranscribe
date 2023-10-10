import os
import gridfs
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


def connect_to_mongodb():
    try:
        mongo_client = MongoClient(os.environ.get('MONGO_URI'))
        db = mongo_client.TalkToText
        user_info_collection = db["files"]
        fs = gridfs.GridFS(db)
        return db, fs, user_info_collection
    except Exception as e:
        print(f"Failed to connect to MongoDB: {str(e)}")
        return None, None, None


def cleanup_mongodb_files():
    try:
        db, fs, user_info_collection = connect_to_mongodb()

        if db and fs:
            user_info_collection.delete_many({})
            fs_files = db['fs.files']
            fs_chunks = db['fs.chunks']
            fs_files.delete_many({})
            fs_chunks.delete_many({})

            print("MongoDB files collection cleaned up successfully.")
        else:
            print("MongoDB connection failed. Cleanup aborted.")
    except Exception as e:
        print(f"Failed to clean up MongoDB files: {str(e)}")


if __name__ == "__main__":
    cleanup_mongodb_files()
