import os
import firebase_admin
from firebase_admin import credentials, messaging
from app.config import settings

_fcm_initialized = False

def init_firebase():
    global _fcm_initialized
    if _fcm_initialized:
        return
    if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
        try:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            _fcm_initialized = True
            print("[Firebase] Initialized with service account.")
        except Exception as e:
            print(f"[Firebase Init Warning] {e}")
    else:
        print(f"[Firebase] No credentials file found at {settings.FIREBASE_CREDENTIALS_PATH}. Push notifications will run in mock/log mode.")

def send_deal_push_notification(fcm_token: str, title: str, body: str, data_payload: dict = None) -> bool:
    if not fcm_token:
        return False
    init_firebase()
    if not _fcm_initialized:
        print(f"[FCM Mock Push] To: {fcm_token[:10]}... | Title: {title} | Body: {body} | Data: {data_payload}")
        return True

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data_payload or {},
            token=fcm_token
        )
        response = messaging.send(message)
        print(f"[FCM Success] Sent message: {response}")
        return True
    except Exception as e:
        print(f"[FCM Error] Failed to send push: {e}")
        return False
