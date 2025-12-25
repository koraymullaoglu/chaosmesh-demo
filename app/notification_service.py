"""
Notification Service - Bildirim Mikroservisi
Payment service tarafından çağrılır
"""
from flask import Flask, request, jsonify
import time
import random
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simüle edilmiş bildirim geçmişi
NOTIFICATION_HISTORY = []

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "notification-service",
        "timestamp": time.time()
    })

@app.route("/")
def home():
    return jsonify({
        "message": "Notification Service",
        "version": "1.0.0",
        "endpoints": [
            "/health - Sağlık kontrolü",
            "/send - Bildirim gönder (POST)",
            "/history - Bildirim geçmişi",
            "/status/<notification_id> - Bildirim durumu"
        ]
    })

@app.route("/send", methods=["POST"])
def send_notification():
    """Bildirim gönderimi"""
    data = request.get_json() or {}
    
    notification_id = f"NOT-{random.randint(10000, 99999)}"
    notification = {
        "id": notification_id,
        "message": data.get("message", ""),
        "type": data.get("type", "info"),
        "recipient": data.get("recipient", "system"),
        "status": "sent",
        "timestamp": time.time()
    }
    
    NOTIFICATION_HISTORY.append(notification)
    logger.info(f"Bildirim gönderildi: {notification_id}")
    
    return jsonify(notification)

@app.route("/history")
def get_history():
    """Bildirim geçmişi"""
    return jsonify({
        "notifications": NOTIFICATION_HISTORY[-50:],  # Son 50 bildirim
        "total_count": len(NOTIFICATION_HISTORY),
        "timestamp": time.time()
    })

@app.route("/status/<notification_id>")
def notification_status(notification_id):
    """Bildirim durumu sorgulama"""
    for n in NOTIFICATION_HISTORY:
        if n["id"] == notification_id:
            return jsonify(n)
    
    return jsonify({
        "id": notification_id,
        "status": "not_found"
    }), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
