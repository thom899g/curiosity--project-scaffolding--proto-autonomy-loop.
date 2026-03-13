"""
Firebase utility functions for initializing the app and getting database references.
"""
import firebase_admin
from firebase_admin import credentials, db, firestore
import os
import json

def initialize_firebase():
    """
    Initialize the Firebase app with the service account key.
    The service account key is expected to be in the file 'firebase-creds.json'
    in the current directory, or set in the environment variable GOOGLE_APPLICATION_CREDENTIALS.
    """
    if not firebase_admin._apps:
        # Check for environment variable
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'firebase-creds.json')
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        else:
            # If the file doesn't exist, try to get the key from an environment variable
            # This is useful for deployment environments like Heroku
            firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
            if firebase_creds_json:
                cred_dict = json.loads(firebase_creds_json)
                cred = credentials.Certificate(cred_dict)
            else:
                raise FileNotFoundError(
                    "Firebase credentials not found. Either set GOOGLE_APPLICATION_CREDENTIALS, "
                    "FIREBASE_CREDENTIALS_JSON environment variable, or place the file at 'firebase-creds.json'."
                )
        
        # Initialize the app with the Realtime Database URL and project ID from environment or default
        database_url = os.environ.get('FIREBASE_DATABASE_URL', 'https://scaffolding-cortex.firebaseio.com')
        project_id = os.environ.get('FIREBASE_PROJECT_ID', 'scaffolding-cortex')
        
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url,
            'projectId': project_id
        })
    
    return firebase_admin.get_app()

def get_realtime_db():
    """Get the Realtime Database reference."""
    return db.reference()

def get_firestore_db():
    """Get the Firestore client."""
    return firestore.client()