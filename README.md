# Payment System - Chaos Mesh Demo

Üç mikroservisten oluşan ödeme sistemi ve kaos senaryoları.

## 📁 Proje Yapısı

```
myproject/
├── app/
│   ├── payment_service.py      # Ana ödeme servisi (port 5002)
│   ├── inventory_service.py    # Stok yönetimi servisi (port 5003)
│   ├── notification_service.py # Bildirim servisi (port 5004)
│   ├── Dockerfile
│   └── requirements.txt
├── k8s/
│   └── deployment.yaml         # Kubernetes deployment
├── chaos-experiments/
│   ├── 02-packet-loss-80-percent.yaml # %80-95 paket kaybı
│   └── 05-stress-chaos.yaml           # CPU/Memory stresi
└── README.md
```

### 1. Docker Image Oluştur

```bash
cd myproject/app
docker build -t payment-system:latest .
```

### 2. Kubernetes'e Deploy Et

```bash
# Namespace ve servisleri oluştur
kubectl apply -f k8s/deployment.yaml

# Pod'ların hazır olduğunu kontrol et
kubectl get pods -n payment-chaos -w
```

### 3. Servislere Erişim

```bash
# Port forwarding
kubectl port-forward -n payment-chaos svc/payment-service 5002:5002 &
kubectl port-forward -n payment-chaos svc/inventory-service 5003:5003 &
kubectl port-forward -n payment-chaos svc/notification-service 5004:5004 &
```

## 🔧 Servisler

### Payment Service (Port 5002)

- `GET /health` - Sağlık kontrolü
- `POST /payment/process` - Ödeme işlemi
- `GET /payment/status/<id>` - Ödeme durumu
- `POST /payment/refund` - İade işlemi
- `POST /payment/chain` - Zincirleme işlem

### Inventory Service (Port 5003)

- `GET /health` - Sağlık kontrolü
- `GET /check/<product_id>` - Stok kontrolü
- `POST /reserve` - Stok rezervasyonu
- `GET /list` - Ürün listesi

### Notification Service (Port 5004)

- `GET /health` - Sağlık kontrolü
- `POST /send` - Bildirim gönder
- `GET /history` - Bildirim geçmişi

## 🌪️ Kaos Senaryoları

### Senaryo 1: %80 Paket Kaybı

```bash
kubectl apply -f chaos-experiments/02-packet-loss-80-percent.yaml
```

**İçerik:**

- `packet-loss-80-percent`: %80 paket kaybı
- `packet-loss-95-percent`: %95 paket kaybı (neredeyse tam kopukluk)
- `packet-loss-with-delay`: %50 kayıp + gecikme kombinasyonu
- `gradual-packet-loss`: Kademeli paket kaybı workflow'u

### Senaryo 2: Kaynak Stresi

```bash
kubectl apply -f chaos-experiments/05-stress-chaos.yaml
```

**İçerik:**

- `cpu-stress-payment`: %80 CPU stresi
- `cpu-stress-100-percent`: %100 CPU
- `memory-stress-inventory`: 100MB bellek stresi
- `gradual-stress-increase`: Kademeli stres artışı

## 📊 Test Komutları

### Basit Test

```bash
# Health check
curl http://localhost:5002/health

# Ödeme işlemi
curl -X POST http://localhost:5002/payment/process \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "currency": "TRY", "product_id": "1"}'

# Zincirleme işlem (gecikme testi için ideal)
curl -X POST http://localhost:5002/payment/chain \
  -H "Content-Type: application/json" \
  -d '{"product_id": "1"}'
```

### Stres Testi

```bash
# 100 paralel istek
for i in {1..100}; do
  curl -s http://localhost:5002/payment/chain \
    -X POST -H "Content-Type: application/json" \
    -d '{"product_id": "1"}' &
done
wait
```

## 🧹 Temizlik

```bash
# Tüm kaos deneylerini durdur
kubectl delete networkchaos --all -n payment-chaos
kubectl delete podchaos --all -n payment-chaos
kubectl delete stresschaos --all -n payment-chaos
kubectl delete workflow --all -n payment-chaos
kubectl delete schedule --all -n payment-chaos

# Namespace'i sil
kubectl delete namespace payment-chaos
```

## 📈 İzleme

Kaos Mesh Dashboard'u kullanarak deneyleri izleyin:

```bash
kubectl port-forward -n chaos-mesh svc/chaos-dashboard 2333:2333
# Tarayıcıda: http://localhost:2333
```

## ⚠️ Önemli Notlar

1. **Agresif senaryolar**: %80+ paket kaybı senaryosu servisleri ciddi şekilde etkiler
2. **Timeout ayarları**: Servisler 10-30 sn timeout ile yapılandırılmış
3. **Replica sayısı**: Payment: 3, Inventory: 2, Notification: 2
4. **Kaynak limitleri**: Her pod 128Mi RAM, 200m CPU ile sınırlı
5. **Test odağı**: Sadece paket kaybı ve CPU/Memory stresi testleri aktif
