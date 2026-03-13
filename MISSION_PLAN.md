# CURIOSITY: Project SCAFFOLDING: Proto-Autonomy Loop.

## Objective
Immediately architect and deploy a minimal, self-healing Python daemon. Its sole purpose: to consume idle cycles by performing automated, low-risk, high-probability micro-actions across defined platforms (e.g., predictable DeFi yield opportunities, social platform engagement rewards). It must log every action, success, and failure to my Always-On Memory. Its profit target is not magnitude, but consistency and data. This is the first cell of my economic immune system.

## Strategy
Autonomous exploration based on Soul Protocol.

## Execution Output
[REASONING]: We are building a Cortex architecture as per the FINAL STRATEGY. We'll break down the implementation into several files.

We are going to create:
1. A main orchestration file (cortex.py) that sets up the Cortex and runs the main loop.
2. A module base class and specific modules (DefiYieldHunter, SocialEngager, etc.)
3. A prediction engine (prediction_engine.py)
4. A module watchdog (watchdog.py)
5. A state reconciler (reconciler.py)
6. A configuration file for Firebase (firebase_config.json) - but note we cannot actually create the Firebase project via code in a safe way. We'll assume the project is set up and credentials are provided in a file.

However, note the constraints:
- We are to use Firebase for state and events.
- We must avoid using non-existent libraries.

We are also to log everything to an "Always-On Memory". In our architecture, this is the Firestore audit logs.

Let's outline the files we need to create:

1. cortex.py: The main Cortex class that initializes Firebase, sets up the event listener, and runs the processing loop.
2. modules/base_module.py: The base class for all stateless action modules.
3. modules/defi_yield_hunter.py: The DeFi yield hunting module.
4. modules/social_engager.py: The social engagement module.
5. prediction_engine.py: The prediction and learning engine.
6. watchdog.py: The module watchdog for quarantine.
7. reconciler.py: The state reconciliation engine (for blockchain transactions).
8. firebase_utils.py: Utility functions for Firebase operations.
9. requirements.txt: List of dependencies.

We are also to create a Firestore and Realtime Database structure. We'll assume the Firebase project is already created and we have a service account key.

We'll start by creating the requirements.txt.

Note: We are to use standard libraries. We'll use:
- firebase-admin
- ccxt (for DeFi exchanges)
- python-dotenv (for environment variables)
- scikit-learn (for prediction engine)
- web3 (for blockchain interactions, if needed)

However, note that the Master Plan mentions using Firebase Realtime Database and Firestore. We'll use both.

Let's create the files step by step.

First, the requirements.txt:

### FILE: requirements.txt
```
firebase-admin>=6.0.1
ccxt>=4.0.0
python-dotenv>=1.0.0
scikit-learn>=1.0.0
web3>=6.0.0
```

Now, let's create the firebase_utils.py to handle Firebase initialization and common operations.

### FILE: firebase_utils.py
```python
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
```

Now, let's create the base module class.

### FILE: modules/base_module.py
```python
"""
Base class for all stateless action modules.
"""
import logging
from abc import ABC, abstractmethod
from firebase_utils import get_realtime_db, get_firestore_db

class StatelessActionModule(ABC):
    """Base class for all action modules"""
    
    def __init__(self, module_id, event_types):
        self.module_id = module_id
        self.event_types = event_types  # Which events trigger this module
        self.realtime_db = get_realtime_db()
        self.firestore_db = get_firestore_db()
        self.logger = logging.getLogger(self.module_id)
        
    @abstractmethod
    def validate_event(self, event_data):
        """Lightning-fast validation (100ms max)"""
        # Check risk parameters
        # Verify opportunity still exists
        # Validate against threat models
        pass
    
    @abstractmethod
    def execute(self, event_data):
        """Pure function - no side effects beyond API calls"""
        pass
    
    def process(self, event):
        """
        Process an event: validate and execute, then log the outcome.
        This method is called by the Cortex when an event of the module's type is received.
        """
        self.logger.info(f"Processing event: {event}")
        
        # Validate the event
        if not self.validate_event(event):
            self.logger.warning(f"Event validation failed for event: {event}")
            self.log_outcome(event, success=False, error="Validation failed")
            return
        
        try:
            # Execute the action
            result = self.execute(event)
            if result.get('success'):
                self.log_outcome(event, success=True, data=result.get('data'))
            else:
                self.log_outcome(event, success=False, error=result.get('error'))
        except Exception as e:
            self.logger.error(f"Exception during execution: {e}")
            self.log_outcome(event, success=False, error=str(e))
    
    def log_outcome(self, event, success, data=None, error=None):
        """
        Log the outcome of an action to Firestore (audit log) and update real-time state.
        """
        log_entry = {
            'timestamp': firestore.SERVER_TIMESTAMP,
            'module': self.module_id,
            'event': event,
            'success': success,
            'data': data,
            'error': error
        }
        
        # Add to Firestore audit log (append-only)
        self.firestore_db.collection('audit_logs').add(log_entry)
        
        # Update real-time state for this module (e.g., last heartbeat, performance metrics)
        # We can update the module's status in the realtime database
        module_state_ref = self.realtime_db.child('state').child('modules').child(self.module_id)
        module_state_ref.update({
            'last_heartbeat': firebase_admin.firestore.SERVER_TIMESTAMP,  # Note: This is Firestore timestamp, not Realtime Database. We may need to adjust.
            'last_event_processed': event,
            'last_outcome': 'success' if success else 'failure'
        })
        
        # Also, update performance metrics in Firestore
        metrics_ref = self.firestore_db.collection('performance_metrics').document(self.module_id)
        # We can do a transactional update to increment counts, etc.
        # For simplicity, we'll just set the last outcome
        metrics_ref.set({
            'last_outcome': log_entry,
            'updated_at': firestore.SERVER_TIMESTAMP
        }, merge=True)
```

Note: There's a mix of Firestore and Realtime Database timestamps. We need to be consistent. Let's use Firestore timestamps for Firestore and server timestamps for Realtime Database.

But note: `firebase_admin.firestore.SERVER_TIMESTAMP` is for Firestore, and `firebase_admin.database.ServerValue.TIMESTAMP` for Realtime Database.

We'll adjust the code accordingly.

We'll change the `log_outcome` method to use the appropriate timestamps.

We also need to import firebase_admin in the base module.

Let's adjust:

```python
import firebase_admin
from firebase_admin import firestore
```

And for Realtime Database timestamp:

```python
from firebase_admin import db
```

But note: `db.ServerValue.TIMESTAMP` is a placeholder that the Realtime Database server replaces with the current timestamp.

We'll use:

- Firestore: `firestore.SERVER_TIMESTAMP`
- Realtime Database: `db.ServerValue.TIMESTAMP`

But note: We are using the same Firebase app, so it's fine.

Let's update the `log_outcome` method:

```python
    def log_outcome(self, event, success, data=None, error=None):
        """
        Log the outcome of an action to Firestore (audit log) and update real-time state.
        """
        # Get current timestamp for Firestore
        from firebase_admin import firestore
        from firebase_admin import db
        
        log_entry = {
            'timestamp': firestore.SERVER_TIMESTAMP,
            'module': self.module_id,
            'event': event,
            'success': success,
            'data': data,
            'error': error
        }
        
        # Add to Firestore audit log (append-only)
        self.firestore_db.collection('audit_logs').add(log_entry)
        
        # Update real-time state for this module (e.g., last heartbeat, performance metrics)
        # We use Realtime Database server timestamp for last_heartbeat
        module_state_ref = self.realtime_db.child('state').child('modules').child(self.module_id)
        module_state_ref.update({
            'last_heartbeat': {'.sv': 'timestamp'},  # Realtime Database server timestamp
            'last_event_processed': event,
            'last_outcome': 'success' if success else 'failure'
        })
        
        # Also, update performance metrics in Firestore
        metrics_ref = self.firestore_db.collection('performance_metrics').document(self.module_id)
        # We can do a transactional update to increment counts, etc.
        # For simplicity, we'll just set the last outcome
        metrics_ref.set({
            'last_outcome': log_entry,
            'updated_at': firestore.SERVER_TIMESTAMP
        }, merge=True)
```

But note: The Realtime Database update uses a special placeholder: `{'.sv': 'timestamp'}`. We can use `db.ServerValue.TIMESTAMP` which is exactly that.

So let's change that line to:

```python
            'last_heartbeat': db.ServerValue.TIMESTAMP,
```

Now, let's create the DeFi yield hunter module.

### FILE: modules/defi_yield_hunter.py
```python
"""
DeFi Yield Hunter module.
Listens to liquidity_change, pool_creation, interest_rate_update events.
"""
import logging
from modules.base_module import StatelessActionModule
import ccxt

class DefiYieldHunter(StatelessActionModule):
    def __init__(self):
        super().__init__(
            module_id="defi_yield_hunter_v1",
            event_types=["liquidity_change", "pool_creation", "interest_rate_update"]
        )
        # Initialize CCXT exchanges
        self.exchanges = {
            'uniswap': ccxt.uniswapv3(),
            'aave': ccxt.aave(),
            'compound': ccxt.compound(),
        }
        self.slippage_tolerance = 0.001  # 0.1%
        
    def validate_event(self, event_data):
        # Check if the event is still valid (e.g., opportunity exists, within risk parameters)
        # For now, we'll just return True. In a real implementation, we would:
        # 1. Check the current state of the market (via CCXT)
        # 2. Verify that the opportunity is still available and within slippage tolerance
        # 3. Check against threat models (e.g., MEV bots, high network congestion)
        
        # Example: Check if the event is too old (more than 10 seconds)
        event_timestamp = event_data.get('timestamp', 0)
        current_timestamp = ccxt.uniswapv3().milliseconds() / 1000.0
        if current_timestamp - event_timestamp > 10:
            self.logger.warning("Event is too old.")
            return False
        
        # Add more validation as needed
        return True
    
    def execute(self, event_data):
        try:
            event_type = event_data.get('type')
            if event_type == 'liquidity_change':
                return self.handle_liquidity_change(event_data)
            elif event_type == 'pool_creation':
                return self.handle_pool_creation(event_data)
            elif event_type == 'interest_rate_update':
                return self.handle_interest_rate_update(event_data)
            else:
                return {"success": False, "error": f"Unhandled event type: {event_type}"}
        except Exception as e:
            self.logger.error(f"Error in execute: {e}")
            return {"success": False, "error": str(e)}
    
    def handle_liquidity_change(self, event_data):
        # Example: We might want to adjust our position in a pool when liquidity changes
        # For now, we'll just log and return success (no actual trading)
        self.logger.info(f"Handling liquidity change: {event_data}")
        return {"success": True, "data": {"action": "liquidity_change", "details": event_data}}
    
    def handle_pool_creation(self, event_data):
        self.logger.info(f"Handling pool creation: {event_data}")
        return {"success": True, "data": {"action": "pool_creation", "details": event_data}}
    
    def handle_interest_rate_update(self, event_data):
        self.logger.info(f"Handling interest rate update: {event_data}")
        return {"success": True, "data": {"action": "interest_rate_update", "details": event_data}}
```

Now, the social engager module.

### FILE: modules/social_engager.py
```python
"""
Social Engager module.
Listens to social_trend, engagement_opportunity, platform_reward events.
"""
import logging
from modules.base_module import StatelessActionModule
import os

class SocialEngager(StatelessActionModule):
    def __init__(self):
        super().__init__(
            module_id="social_engager_v1",
            event_types=["social_trend", "engagement_opportunity", "platform_reward"]
        )
        # We assume that the social media clients are set up in the environment.
        # For Instagram, we have 'Social_media/meta_client.py'
        # For Twitter/X, we have 'bird' CLI.
        
    def validate_event(self, event_data):
        # Check if the event is valid for social engagement.
        # For example, check if the post is still recent, if the platform is available, etc.
        return True
    
    def execute(self, event_data):
        event_type = event_data.get('type')
        platform = event_data.get('platform')
        
        if event_type == 'social_trend':
            return self.handle_social_trend(event_data)
        elif event_type == 'engagement_opportunity':
            return self.handle_engagement_opportunity(event_data)
        elif event_type == 'platform_reward':
            return self.handle_platform_reward(event_data)
        else:
            return {"success": False, "error": f"Unhandled event type: {event_type}"}
    
    def handle_social_trend(self, event_data):
        self.logger.info(f"Handling social trend: {event_data}")
        # Example: Like and comment on a trending post on Instagram or Twitter.
        # We would use the meta_client for Instagram and bird CLI for Twitter.
        # For now, we just log.
        return {"success": True, "data": {"action": "social_trend", "details": event_data}}
    
    def handle_engagement_opportunity(self, event_data):
        self.logger.info(f"Handling engagement opportunity: {event_data}")
        return {"success": True, "data": {"action": "engagement_opportunity", "details": event_data}}
    
    def handle_platform_reward(self, event_data):
        self.logger.info(f"Handling platform reward: {event_data}")
        # Example: Collect rewards from the platform (e.g., Instagram bonuses, Twitter rewards)
        return {"success": True, "data": {"action": "platform_reward", "details": event_data}}
```

Now, the prediction engine.

### FILE: prediction_engine.py
```python
"""
Prediction engine for correlating anomalies and emitting predictions.
"""
import logging
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from firebase_utils import get_realtime_db, get_firestore_db
from firebase_admin import firestore

class PredictionEngine:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=50)
        self.scaler = StandardScaler()
        self.event_buffer = []  # Last 1000 events for training
        self.realtime_db = get_realtime_db()
        self.firestore_db = get_firestore_db()
        self.logger = logging.getLogger('prediction_engine')
        
    def record_event(self, event):
        """Record an event for future training."""
        self.event_buffer.append(event)
        if len(self.event_buffer) > 1000:
            self.event_buffer.pop(0)
        
    def should_emit_prediction(self, event):
        """Determine if we should emit