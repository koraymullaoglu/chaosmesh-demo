"""
Payment Service - Yeni Mikroservis
Ödeme işlemlerini simüle eden bir servis
Agresif kaos senaryoları için hedef
"""
from flask import Flask, request, jsonify
import requests
import time
import random
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
INVENTORY_SERVICE = os.getenv("INVENTORY_SERVICE", "http://inventory-service:5002")
NOTIFICATION_SERVICE = os.getenv("NOTIFICATION_SERVICE", "http://notification-service:5003")

@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "payment-service",
        "timestamp": time.time()
    })

@app.route("/")
def home():
    return jsonify({
        "message": "Payment Service - Kaos Test Hedefi",
        "version": "1.0.0",
        "endpoints": [
            "/health - Sağlık kontrolü",
            "/payment/process - Ödeme işlemi (POST)",
            "/payment/status/<id> - Ödeme durumu",
            "/payment/refund - İade işlemi (POST)",
            "/payment/validate - Kart doğrulama (POST)",
            "/payment/chain - Zincirleme işlem (inventory + notification)"
        ]
    })

@app.route("/payment/process", methods=["POST"])
def process_payment():
    """
    Ödeme işlemi endpoint'i
    Kaos testleri için kritik endpoint - gecikme ve paket kaybı senaryoları
    """
    start_time = time.time()
    data = request.get_json() or {}
    
    logger.info(f"Ödeme isteği alındı: {data}")
    
    # Simüle edilmiş ödeme işlemi
    payment_id = f"PAY-{random.randint(10000, 99999)}"
    
    # Inventory kontrolü yap
    try:
        inventory_check = requests.get(
            f"{INVENTORY_SERVICE}/check/{data.get('product_id', 'unknown')}",
            timeout=10
        )
        inventory_status = inventory_check.json() if inventory_check.ok else {"available": False}
    except Exception as e:
        logger.error(f"Inventory kontrolü başarısız: {e}")
        inventory_status = {"available": False, "error": str(e)}
    
    elapsed = time.time() - start_time
    
    return jsonify({
        "payment_id": payment_id,
        "status": "success",
        "amount": data.get("amount", 0),
        "currency": data.get("currency", "TRY"),
        "inventory_check": inventory_status,
        "processing_time_ms": round(elapsed * 1000, 2),
        "timestamp": time.time()
    })

@app.route("/payment/status/<payment_id>")
def payment_status(payment_id):
    """Ödeme durumu sorgulama"""
    return jsonify({
        "payment_id": payment_id,
        "status": random.choice(["completed", "pending", "processing"]),
        "last_update": time.time()
    })

@app.route("/payment/refund", methods=["POST"])
def refund_payment():
    """İade işlemi - kritik işlem, kaos testleri için önemli"""
    data = request.get_json() or {}
    
    # Simüle edilmiş işlem süresi
    time.sleep(0.2)
    
    return jsonify({
        "refund_id": f"REF-{random.randint(10000, 99999)}",
        "original_payment_id": data.get("payment_id"),
        "amount": data.get("amount", 0),
        "status": "refunded",
        "timestamp": time.time()
    })

@app.route("/payment/validate", methods=["POST"])
def validate_card():
    """Kart doğrulama - hassas işlem"""
    data = request.get_json() or {}
    
    card_number = data.get("card_number", "")
    is_valid = len(card_number) >= 16 if card_number else False
    
    return jsonify({
        "valid": is_valid,
        "card_type": "visa" if card_number.startswith("4") else "mastercard",
        "masked_number": f"****-****-****-{card_number[-4:]}" if len(card_number) >= 4 else "****",
        "timestamp": time.time()
    })

@app.route("/payment/chain", methods=["POST"])
def chain_transaction():
    """
    Zincirleme işlem - Birden fazla servisi çağırır
    Kaos senaryolarında kısmi başarısızlıkları test etmek için ideal
    """
    data = request.get_json() or {}
    results = {
        "steps": [],
        "overall_status": "success",
        "total_time_ms": 0
    }
    
    start_total = time.time()
    
    # Adım 1: Inventory kontrolü
    try:
        start = time.time()
        resp = requests.get(f"{INVENTORY_SERVICE}/check/{data.get('product_id', '1')}", timeout=15)
        elapsed = time.time() - start
        results["steps"].append({
            "step": 1,
            "service": "inventory",
            "status": "success",
            "latency_ms": round(elapsed * 1000, 2)
        })
    except Exception as e:
        results["steps"].append({
            "step": 1,
            "service": "inventory",
            "status": "failed",
            "error": str(e)
        })
        results["overall_status"] = "partial_failure"
    
    # Adım 2: Notification gönderimi
    try:
        start = time.time()
        resp = requests.post(
            f"{NOTIFICATION_SERVICE}/send",
            json={"message": "Ödeme işlemi başlatıldı", "type": "payment"},
            timeout=15
        )
        elapsed = time.time() - start
        results["steps"].append({
            "step": 2,
            "service": "notification",
            "status": "success",
            "latency_ms": round(elapsed * 1000, 2)
        })
    except Exception as e:
        results["steps"].append({
            "step": 2,
            "service": "notification",
            "status": "failed",
            "error": str(e)
        })
        results["overall_status"] = "partial_failure"
    
    results["total_time_ms"] = round((time.time() - start_total) * 1000, 2)
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
