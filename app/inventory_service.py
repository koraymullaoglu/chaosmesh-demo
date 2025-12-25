"""
Inventory Service - Stok Yönetimi Mikroservisi
Payment service tarafından çağrılır
"""
from flask import Flask, request, jsonify
import time
import random

app = Flask(__name__)

# Simüle edilmiş stok verileri
INVENTORY = {
    "1": {"name": "Laptop", "stock": 50, "price": 15000},
    "2": {"name": "Telefon", "stock": 100, "price": 8000},
    "3": {"name": "Tablet", "stock": 30, "price": 5000},
    "4": {"name": "Kulaklık", "stock": 200, "price": 500},
    "5": {"name": "Şarj Cihazı", "stock": 500, "price": 150}
}

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "inventory-service",
        "timestamp": time.time()
    })

@app.route("/")
def home():
    return jsonify({
        "message": "Inventory Service",
        "version": "1.0.0",
        "endpoints": [
            "/health - Sağlık kontrolü",
            "/check/<product_id> - Stok kontrolü",
            "/reserve - Stok rezervasyonu (POST)",
            "/list - Tüm ürünleri listele"
        ]
    })

@app.route("/check/<product_id>")
def check_stock(product_id):
    """Stok kontrolü - Payment service tarafından çağrılır"""
    product = INVENTORY.get(product_id)
    
    if product:
        return jsonify({
            "product_id": product_id,
            "name": product["name"],
            "available": product["stock"] > 0,
            "stock_count": product["stock"],
            "price": product["price"],
            "timestamp": time.time()
        })
    else:
        return jsonify({
            "product_id": product_id,
            "available": False,
            "error": "Ürün bulunamadı"
        }), 404

@app.route("/reserve", methods=["POST"])
def reserve_stock():
    """Stok rezervasyonu"""
    data = request.get_json() or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    
    product = INVENTORY.get(product_id)
    if product and product["stock"] >= quantity:
        return jsonify({
            "reservation_id": f"RES-{random.randint(10000, 99999)}",
            "product_id": product_id,
            "quantity": quantity,
            "status": "reserved",
            "timestamp": time.time()
        })
    else:
        return jsonify({
            "error": "Yetersiz stok",
            "available": product["stock"] if product else 0
        }), 400

@app.route("/list")
def list_products():
    """Tüm ürünleri listele"""
    return jsonify({
        "products": [
            {"id": k, **v} for k, v in INVENTORY.items()
        ],
        "timestamp": time.time()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
