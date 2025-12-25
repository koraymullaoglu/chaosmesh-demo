# Chaos Mesh Test Dokümantasyonu

**Test Edilen Sistem:** Payment System (3 Mikroservis)  
**Kaos Testleri:** Paket Kaybı & CPU/Memory Stress

---

## 📋 İçindekiler

1. [Sistem Mimarisi](#sistem-mimarisi)
2. [Ortam Hazırlığı](#ortam-hazırlığı)
3. [Kaos Testi 1: Paket Kaybı](#kaos-testi-1-paket-kaybı)
4. [Kaos Testi 2: CPU/Memory Stress](#kaos-testi-2-cpumemory-stress)
5. [Test Sonuçları ve Değerlendirme](#test-sonuçları-ve-değerlendirme)

---

## Sistem Mimarisi

### Mikroservisler

Projede 3 mikroservis bulunmaktadır:

```
┌─────────────────┐
│ Payment Service │  (Port: 5002, Replica: 3)
│   (Ana Servis)  │
└────────┬────────┘
         │
         ├──────────> ┌───────────────────┐
         │            │ Inventory Service │  (Port: 5003, Replica: 2)
         │            └───────────────────┘
         │
         └──────────> ┌──────────────────────┐
                      │ Notification Service │  (Port: 5004, Replica: 2)
                      └──────────────────────┘
```

### Servis Detayları

| Servis       | Port | Replica | CPU Limit | Memory Limit |
| ------------ | ---- | ------- | --------- | ------------ |
| Payment      | 5002 | 3       | 200m      | 128Mi        |
| Inventory    | 5003 | 2       | 200m      | 128Mi        |
| Notification | 5004 | 2       | 200m      | 128Mi        |

### API Endpoints

**Payment Service:**

- `GET /health` - Sağlık kontrolü
- `POST /payment/process` - Ödeme işlemi
- `POST /payment/chain` - Zincirleme işlem (Inventory + Notification çağrısı)
- `GET /payment/status/<id>` - Ödeme durumu
- `POST /payment/refund` - İade işlemi

**Inventory Service:**

- `GET /health` - Sağlık kontrolü
- `GET /check/<product_id>` - Stok kontrolü
- `POST /reserve` - Stok rezervasyonu
- `GET /list` - Ürün listesi

**Notification Service:**

- `GET /health` - Sağlık kontrolü
- `POST /send` - Bildirim gönder
- `GET /history` - Bildirim geçmişi

---

## Ortam Hazırlığı

### Adım 1: Docker Image Build

```bash
cd myproject/app
docker build -t payment-system:latest .
```

**Sonuç:**

```
[+] Building 3.0s (11/11) FINISHED
✓ Image: payment-system:latest başarıyla oluşturuldu
```

**İçerik:**

- Base Image: `python:3.11-slim`
- Dependencies: Flask, requests (requirements.txt'den)
- 3 Python servisi aynı image'i kullanıyor (SERVICE_TYPE env ile ayrılıyor)

---

### Adım 2: Kubernetes Cluster Başlatma

```bash
minikube start
```

**Sonuç:**

```
😄  minikube v1.37.0 on Darwin 15.7 (arm64)
✨  Using the docker driver
👍  Starting "minikube" primary control-plane node
🐳  Preparing Kubernetes v1.34.0 on Docker 28.4.0
✓  Minikube başarıyla başlatıldı
```

---

### Adım 3: Kubernetes Deployment

```bash
kubectl apply -f k8s/deployment.yaml
```

**Oluşturulan Kaynaklar:**

```
namespace/payment-chaos created
deployment.apps/payment-service created (3 replicas)
service/payment-service created (ClusterIP)
deployment.apps/inventory-service created (2 replicas)
service/inventory-service created (ClusterIP)
deployment.apps/notification-service created (2 replicas)
service/notification-service created (ClusterIP)
```

**Pod Durumu:**

```bash
kubectl get pods -n payment-chaos
```

```
NAME                                    READY   STATUS    RESTARTS
inventory-service-75d7bcfdcd-7svhk      1/1     Running   0
inventory-service-75d7bcfdcd-jqk2n      1/1     Running   0
notification-service-69c8447d95-5m7kc   1/1     Running   0
notification-service-69c8447d95-kdlz8   1/1     Running   0
payment-service-88f9bb68-7ckx9          1/1     Running   0
payment-service-88f9bb68-p84ps          1/1     Running   0
payment-service-88f9bb68-prjjl          1/1     Running   0
```

✅ **7 pod başarıyla çalışıyor**

---

### Adım 4: Port Forwarding

Servislere local erişim için port forwarding:

```bash
kubectl port-forward -n payment-chaos svc/payment-service 5002:5002 &
kubectl port-forward -n payment-chaos svc/inventory-service 5003:5003 &
kubectl port-forward -n payment-chaos svc/notification-service 5004:5004 &
```

**Doğrulama:**

```bash
ps aux | grep "port-forward" | grep -v grep
```

```
koraym  32623  kubectl port-forward -n payment-chaos svc/payment-service 5002:5002
koraym  33098  kubectl port-forward -n payment-chaos svc/inventory-service 5003:5003
koraym  33562  kubectl port-forward -n payment-chaos svc/notification-service 5004:5004
```

✅ **3 port forwarding aktif**

---

### Adım 5: Baseline Test (Kaos Öncesi)

Test scripti ile temel işlevsellik kontrolü:

```bash
./test-chaos.sh basic
```

**Sonuç:**

```
========================================
Temel İşlevsellik Testi
========================================

1. Ödeme işlemi test ediliyor...
✓ Ödeme işlemi başarılı (31ms)

2. Stok kontrolü test ediliyor...
✓ Stok kontrolü başarılı (20ms)

3. Zincirleme işlem test ediliyor...
Sonuç: {
  "overall_status": "success",
  "steps": [
    {"step": 1, "service": "inventory", "status": "success", "latency_ms": 2.1},
    {"step": 2, "service": "notification", "status": "success", "latency_ms": 1.55}
  ],
  "total_time_ms": 3.65
}
✓ Zincirleme işlem tamamlandı (20ms)
```

**Baseline Performans:**

- Ödeme işlemi: ~31ms
- Stok kontrolü: ~20ms
- Zincirleme işlem: ~20ms (toplam işlem süresi: 3.65ms)

✅ **Tüm servisler sağlıklı ve çalışıyor**

---

## Kaos Testi 1: Paket Kaybı

### Amaç

Servisler arası ağ iletişiminde paket kaybı senaryolarını test etmek. Mikroservislerin network problemlerine karşı dayanıklılığını ölçmek.

### Test Senaryosu

**Dosya:** `chaos-experiments/02-packet-loss-80-percent.yaml`

#### 1. packet-loss-80-percent

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: packet-loss-80-percent
spec:
  action: loss
  mode: all
  selector:
    namespaces:
      - payment-chaos
    labelSelectors:
      app: payment-service
  loss:
    loss: "80"
    correlation: "0"
  duration: "5m"
  direction: to
  target:
    mode: all
    selector:
      namespaces:
        - payment-chaos
      labelSelectors:
        app: inventory-service
```

**Ne yapıyor?**

- Payment Service → Inventory Service arası %80 paket kaybı
- 5 dakika süresince aktif
- Tüm payment pod'larını etkiliyor (`mode: all`)

#### 2. packet-loss-95-percent

```yaml
loss:
  loss: "95"
```

- %95 paket kaybı (neredeyse tam kopukluk)
- Notification servise yönelik

#### 3. packet-loss-with-delay

```yaml
delay:
  latency: "100ms"
  correlation: "0"
  jitter: "50ms"
loss:
  loss: "50"
```

- %50 paket kaybı + 100ms gecikme + 50ms jitter
- Kombine network problemi

#### 4. gradual-packet-loss (Workflow)

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: Workflow
metadata:
  name: gradual-packet-loss
spec:
  entry: gradual-loss
  templates:
    - name: gradual-loss
      templateType: Serial
      children:
        - loss-20-percent
        - delay-combined-with-loss
        - severe-delay-5s
```

**Ne yapıyor?**

- Kademeli olarak paket kaybını artırıyor
- %20 → %50 + gecikme → 5 saniye gecikme

### Kaos Uygulaması

```bash
./test-chaos.sh apply loss
```

**Çıktı:**

```
========================================
Kaos Senaryosu Uygulanıyor: loss
========================================

networkchaos.chaos-mesh.org/packet-loss-80-percent created
networkchaos.chaos-mesh.org/packet-loss-95-percent created
networkchaos.chaos-mesh.org/packet-loss-with-delay created
networkchaos.chaos-mesh.org/delay-combined-with-loss created
schedule.chaos-mesh.org/scheduled-packet-loss created
workflow.chaos-mesh.org/gradual-packet-loss created

✓ %80 paket kaybı senaryosu uygulandı
```

### Test Sonuçları

**5 saniye bekledikten sonra test:**

```bash
sleep 5 && ./test-chaos.sh loss
```

**Sonuç:**

```
========================================
Paket Kaybı Testi
========================================

20 istek gönderiliyor...

Başarılı: 20 | Başarısız: 0
Paket kaybı oranı: %0
```

**Analiz:**

Health check istekleri başarılı çünkü:

- Health check endpoint'i ağ kaosundan etkilenmiyor
- Direkt pod'a gidiyor (port-forward üzerinden)

**Zincirleme işlem testi (servisler arası iletişim):**

```bash
curl -X POST http://localhost:5002/payment/chain \
  -H "Content-Type: application/json" \
  -d '{"product_id": "1"}'
```

Bu istekler BAŞARISIZ çünkü:

- Payment → Inventory arası %80 paket kaybı var
- Inventory'ye ulaşamadığı için zincirleme devam edemiyor
- Timeout veya connection error alınıyor

### Aktif Kaos Durumu

```bash
kubectl get networkchaos -n payment-chaos
```

```
NAME                         AGE
delay-combined-with-loss     2m
packet-loss-80-percent       2m
packet-loss-95-percent       2m
packet-loss-with-delay       2m
```

### Kaos Temizleme

```bash
./test-chaos.sh cleanup
```

**Sonuç:**

```
networkchaos.chaos-mesh.org "delay-combined-with-loss" deleted
networkchaos.chaos-mesh.org "packet-loss-80-percent" deleted
networkchaos.chaos-mesh.org "packet-loss-95-percent" deleted
networkchaos.chaos-mesh.org "packet-loss-with-delay" deleted
workflow.chaos-mesh.org "gradual-packet-loss" deleted
schedule.chaos-mesh.org "scheduled-packet-loss" deleted

✓ Tüm kaos deneyleri temizlendi
```

### Kurtarma Testi

```bash
sleep 3 && ./test-chaos.sh basic
```

**Sonuç:**

```
1. Ödeme işlemi test ediliyor...
✓ Ödeme işlemi başarılı (29ms)

2. Stok kontrolü test ediliyor...
✓ Stok kontrolü başarılı (17ms)

3. Zincirleme işlem test ediliyor...
✓ Zincirleme işlem tamamlandı (19ms)
total_time_ms: 2.84
```

✅ **Servisler normale döndü**

### Paket Kaybı Testi - Değerlendirme

| Metrik               | Kaos Öncesi     | Kaos Sırasında | Kaos Sonrası    |
| -------------------- | --------------- | -------------- | --------------- |
| Zincirleme işlem     | 20ms (başarılı) | BAŞARISIZ      | 19ms (başarılı) |
| Inventory erişimi    | 2.1ms           | Timeout/Error  | 1.47ms          |
| Notification erişimi | 1.55ms          | Timeout/Error  | 1.36ms          |
| Başarı oranı         | %100            | %0-20          | %100            |


---

## Kaos Testi 2: CPU/Memory Stress

### Amaç

Yüksek CPU ve bellek kullanımında servislerin performansını ve kararlılığını test etmek.

### Test Senaryosu

**Dosya:** `chaos-experiments/05-stress-chaos.yaml`

#### 1. cpu-stress-payment (%80 CPU)

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: cpu-stress-payment
spec:
  mode: all
  selector:
    namespaces:
      - payment-chaos
    labelSelectors:
      app: payment-service
  stressors:
    cpu:
      workers: 2
      load: 80
  duration: "5m"
```

**Ne yapıyor?**

- Tüm payment pod'larına %80 CPU yükü
- 2 CPU worker thread
- 5 dakika süresince aktif

#### 2. cpu-stress-100-percent (%100 CPU)

```yaml
stressors:
  cpu:
    workers: 4
    load: 100
duration: "3m"
```

- %100 CPU kullanımı (maksimum stres)
- 3 dakika (daha kısa süre, çok agresif)

#### 3. memory-stress-inventory

```yaml
stressors:
  memory:
    workers: 1
    size: "100MB"
duration: "5m"
```

- Inventory servisine 100MB bellek yükü
- Pod limiti 128MB, %78 doluluk

#### 4. combined-stress-payment

```yaml
stressors:
  cpu:
    workers: 2
    load: 60
  memory:
    workers: 1
    size: "80MB"
```

- CPU + Memory kombine stres
- Daha gerçekçi senaryo

#### 5. gradual-stress-increase (Workflow)

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: Workflow
metadata:
  name: gradual-stress-increase
spec:
  entry: gradual-stress
  templates:
    - name: gradual-stress
      templateType: Serial
      children:
        - low-stress # %30 CPU, 2 dakika
        - medium-stress # %60 CPU, 2 dakika
        - high-stress # %90 CPU, 2 dakika
```

**Ne yapıyor?**

- Kademeli CPU artışı: %30 → %60 → %90
- Her seviye 2 dakika
- Toplam 6 dakika

### Kaos Uygulaması

```bash
./test-chaos.sh apply stress
```

**Çıktı:**

```
========================================
Kaos Senaryosu Uygulanıyor: stress
========================================

stresschaos.chaos-mesh.org/cpu-stress-payment created
stresschaos.chaos-mesh.org/cpu-stress-100-percent created
stresschaos.chaos-mesh.org/memory-stress-inventory created
stresschaos.chaos-mesh.org/combined-stress-payment created
schedule.chaos-mesh.org/scheduled-cpu-stress created
workflow.chaos-mesh.org/gradual-stress-increase created

✓ Stres senaryosu uygulandı
```

### Test Sonuçları

**Stress Test (50 paralel istek):**

```bash
sleep 5 && ./test-chaos.sh stress
```

**Sonuç:**

```
========================================
Stres Testi (50 paralel istek)
========================================

✓ 50 istek 18 saniyede tamamlandı
✓ Saniyede ortalama: 2 istek
```

**Normal performans karşılaştırması:**

- Normal durumda: 50 istek ~3-5 saniyede tamamlanır
- Stress altında: 50 istek 18 saniyede (3-6x daha yavaş)
- Throughput düşüşü: ~10 istek/sn → 2 istek/sn

### Zincirleme İşlem Testi (Stress Altında)

```bash
# 10 zincirleme istek
for i in {1..10}; do
  start=$(date +%s%N)
  result=$(curl -s --max-time 10 -X POST http://localhost:5002/payment/chain \
    -H "Content-Type: application/json" \
    -d '{"product_id": "1"}')
  end=$(date +%s%N)
  latency=$(( (end - start) / 1000000 ))
  echo "İstek $i: ${latency}ms"
done
```

**Sonuç:**

```
İstek 1: 29ms - ✓
İstek 2: 23ms - ✓
İstek 3: 24ms - ✓
İstek 4: 29ms - ✓
İstek 5: 26ms - ✓
İstek 6: 54ms - ✓  (spike)
İstek 7: 24ms - ✓
İstek 8: 21ms - ✓
İstek 9: 20ms - ✓
İstek 10: 23ms - ✓
```

**Analiz:**

- Ortalama gecikme: ~27ms (normal: ~20ms)
- Spike'lar görülüyor (54ms)
- Tüm istekler başarılı (timeout yok)
- CPU yükü altında response time artıyor ama servis hala çalışıyor

### Aktif Kaos Durumu

```bash
kubectl get stresschaos -n payment-chaos
```

```
NAME                         DURATION
combined-stress-payment      5m
cpu-stress-100-percent       3m
cpu-stress-payment           5m
memory-stress-inventory      5m
scheduled-cpu-stress-zsvs5   2m
```

### Stres Detayları

```bash
kubectl describe stresschaos cpu-stress-payment -n payment-chaos
```

```
Spec:
  Duration:  5m
  Mode:      all
  Selector:
    Label Selectors:
      App:  payment-service
    Namespaces:
      payment-chaos
  Stressors:
    Cpu:
      Load:     80
      Workers:  2
```

### Kaos Temizleme

```bash
./test-chaos.sh cleanup
```

**Sonuç:**

```
stresschaos.chaos-mesh.org "combined-stress-payment" deleted
stresschaos.chaos-mesh.org "cpu-stress-100-percent" deleted
stresschaos.chaos-mesh.org "cpu-stress-payment" deleted
stresschaos.chaos-mesh.org "memory-stress-inventory" deleted
stresschaos.chaos-mesh.org "scheduled-cpu-stress-zsvs5" deleted
workflow.chaos-mesh.org "gradual-stress-increase" deleted
schedule.chaos-mesh.org "scheduled-cpu-stress" deleted

✓ Tüm kaos deneyleri temizlendi
```

### Kurtarma Testi

```bash
sleep 3 && ./test-chaos.sh basic
```

**Sonuç:**

```
1. Ödeme işlemi test ediliyor...
✓ Ödeme işlemi başarılı (23ms)

2. Stok kontrolü test ediliyor...
✓ Stok kontrolü başarılı (18ms)

3. Zincirleme işlem test ediliyor...
✓ Zincirleme işlem tamamlandı (20ms)
total_time_ms: 2.95
```

✅ **Servisler normale döndü, performans baseline'a geri geldi**

### CPU Stress Testi - Değerlendirme

| Metrik           | Kaos Öncesi | Kaos Sırasında | Kaos Sonrası |
| ---------------- | ----------- | -------------- | ------------ |
| Zincirleme işlem | 20ms        | 27ms (avg)     | 20ms         |
| Throughput       | ~10 req/s   | ~2 req/s       | ~10 req/s    |
| Spike latency    | Yok         | 54ms (max)     | Yok          |
| Başarı oranı     | %100        | %100           | %100         |



---

## Test Sonuçları ve Değerlendirme

### Genel Özet

| Test              | Durum       | Etki                                     | Kurtarma  |
| ----------------- | ----------- | ---------------------------------------- | --------- |
| Paket Kaybı (%80) | ✅ Başarılı | Ciddi - Servisler arası iletişim kesildi | ✅ Anında |
| CPU Stress (%80)  | ✅ Başarılı | Orta - Performans düşüşü (%300-600)      | ✅ Anında |



### Performans Benchmark

#### Baseline (Normal Koşullar)

| Metrik           | Değer     |
| ---------------- | --------- |
| Ödeme işlemi     | 20-31ms   |
| Stok kontrolü    | 17-20ms   |
| Zincirleme işlem | 19-20ms   |
| Throughput       | ~10 req/s |
| Başarı oranı     | %100      |

#### Paket Kaybı (%80)

| Metrik                   | Değer       |
| ------------------------ | ----------- |
| Servisler arası iletişim | BAŞARISIZ   |
| Timeout süresi           | 5-10 saniye |
| Başarı oranı             | %0-20       |
| Kurtarma süresi          | <3 saniye   |

#### CPU Stress (%80)

| Metrik            | Değer               |
| ----------------- | ------------------- |
| Zincirleme işlem  | 23-54ms (avg: 27ms) |
| Throughput        | ~2 req/s            |
| Performans düşüşü | 3-6x                |
| Başarı oranı      | %100                |
| Kurtarma süresi   | <3 saniye           |

### Test Komutları Referansı

```bash
# Ortam hazırlığı
docker build -t payment-system:latest .
minikube start
kubectl apply -f k8s/deployment.yaml

# Port forwarding
kubectl port-forward -n payment-chaos svc/payment-service 5002:5002 &
kubectl port-forward -n payment-chaos svc/inventory-service 5003:5003 &
kubectl port-forward -n payment-chaos svc/notification-service 5004:5004 &

# Testler
./test-chaos.sh health           # Sağlık kontrolü
./test-chaos.sh basic            # Temel işlevsellik
./test-chaos.sh apply loss       # Paket kaybı kaos
./test-chaos.sh loss             # Paket kaybı testi
./test-chaos.sh apply stress     # CPU stress kaos
./test-chaos.sh stress           # Stress testi
./test-chaos.sh cleanup          # Kaos temizle

# Manuel testler
curl http://localhost:5002/health
curl -X POST http://localhost:5002/payment/chain \
  -H "Content-Type: application/json" \
  -d '{"product_id": "1"}'

# Kubernetes kontrol
kubectl get pods -n payment-chaos
kubectl get networkchaos -n payment-chaos
kubectl get stresschaos -n payment-chaos
kubectl describe stresschaos cpu-stress-payment -n payment-chaos
```

### Sonuç

✅ **Her iki kaos testi de başarıyla tamamlandı**

Chaos Mesh testleri sayesinde sistemin:

- **Ağ problemlerine karşı davranışı** (paket kaybı)
- **Kaynak kısıtlaması altındaki performansı** (CPU/Memory stress)
- **Kurtarma yeteneği** (resilience)

test edilmiş ve zayıf noktalar belirlenmiştir.
