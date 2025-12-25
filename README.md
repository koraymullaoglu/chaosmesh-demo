# Payment System - Chaos Mesh Demo

A payment system with three microservices and chaos engineering scenarios.

## 🎯 Project Overview

This project demonstrates chaos engineering principles using **Chaos Mesh** on a simple payment microservices architecture. Two main chaos scenarios are implemented and tested:

1. **80% Packet Loss** - Network communication disruption between services
2. **CPU/Memory Stress** - Performance testing under resource constraints

## 📊 Test Results Summary

| Scenario    | Impact                             | Recovery      |
| ----------- | ---------------------------------- | ------------- |
| Packet Loss | 100% service communication failure | ✅ <3 seconds |
| CPU Stress  | 300-600% performance degradation   | ✅ <3 seconds |

## 📁 Project Structure

```
myproject/
├── app/
│   ├── payment_service.py      # Main payment service (port 5002)
│   ├── inventory_service.py    # Inventory management service (port 5003)
│   ├── notification_service.py # Notification service (port 5004)
│   ├── Dockerfile
│   └── requirements.txt
├── k8s/
│   └── deployment.yaml         # Kubernetes deployment
├── chaos-experiments/
│   ├── 02-packet-loss-80-percent.yaml # 80-95% packet loss scenarios
│   └── 05-stress-chaos.yaml           # CPU/Memory stress scenarios
├── test-chaos.sh               # Automated test script
├── README.md
└── Dokuman.md                  # Detailed documentation (Turkish)
```

## 🏗️ Architecture

```
┌─────────────────┐
│ Payment Service │  (Port: 5002, Replicas: 3)
│   (Main API)    │
└────────┬────────┘
         │
         ├──────────> ┌───────────────────┐
         │            │ Inventory Service │  (Port: 5003, Replicas: 2)
         │            └───────────────────┘
         │
         └──────────> ┌──────────────────────┐
                      │ Notification Service │  (Port: 5004, Replicas: 2)
                      └──────────────────────┘
```

## 🚀 Quick Start

### 1. Build Docker Image

```bash
cd app
docker build -t payment-system:latest .
```

### 2. Deploy to Kubernetes

```bash
# Create namespace and deploy services
kubectl apply -f k8s/deployment.yaml

# Check pod status
kubectl get pods -n payment-chaos -w
```

### 3. Port Forwarding

```bash
# Forward service ports to localhost
kubectl port-forward -n payment-chaos svc/payment-service 5002:5002 &
kubectl port-forward -n payment-chaos svc/inventory-service 5003:5003 &
kubectl port-forward -n payment-chaos svc/notification-service 5004:5004 &
```

## 🔧 Services

### Payment Service (Port 5002)

- `GET /health` - Health check
- `POST /payment/process` - Process payment
- `GET /payment/status/<id>` - Get payment status
- `POST /payment/refund` - Process refund
- `POST /payment/chain` - Chain request (calls Inventory + Notification)

### Inventory Service (Port 5003)

- `GET /health` - Health check
- `GET /check/<product_id>` - Check stock availability
- `POST /reserve` - Reserve stock
- `GET /list` - List products

### Notification Service (Port 5004)

- `GET /health` - Health check
- `POST /send` - Send notification
- `GET /history` - Get notification history

## 🌪️ Chaos Scenarios

### Scenario 1: 80% Packet Loss

```bash
kubectl apply -f chaos-experiments/02-packet-loss-80-percent.yaml
```

**Includes:**

- `packet-loss-80-percent`: 80% packet loss between services
- `packet-loss-95-percent`: 95% packet loss (near-complete disruption)
- `packet-loss-with-delay`: 50% loss + network delay combination
- `gradual-packet-loss`: Gradual packet loss workflow

**Expected Impact:** Complete failure of inter-service communication

### Scenario 2: Resource Stress

```bash
kubectl apply -f chaos-experiments/05-stress-chaos.yaml
```

**Includes:**

- `cpu-stress-payment`: 80% CPU stress on payment service
- `cpu-stress-100-percent`: 100% CPU stress
- `memory-stress-inventory`: 100MB memory stress on inventory
- `gradual-stress-increase`: Gradual stress increase workflow

**Expected Impact:** 3-6x performance degradation, increased latency

## 📊 Testing

### Automated Test Script

```bash
# Make script executable
chmod +x test-chaos.sh

# Health check
./test-chaos.sh health

# Basic functionality test
./test-chaos.sh basic

# Apply chaos scenarios
./test-chaos.sh apply loss      # Apply packet loss
./test-chaos.sh apply stress    # Apply CPU/memory stress

# Run tests
./test-chaos.sh loss            # Test packet loss impact
./test-chaos.sh stress          # Test stress impact

# Cleanup chaos experiments
./test-chaos.sh cleanup
```

### Manual Testing

```bash
# Health check
curl http://localhost:5002/health

# Payment processing
curl -X POST http://localhost:5002/payment/process \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "currency": "USD", "product_id": "1"}'

# Chain request (best for latency testing)
curl -X POST http://localhost:5002/payment/chain \
  -H "Content-Type: application/json" \
  -d '{"product_id": "1"}'
```

### Stress Test

```bash
# 100 parallel requests
for i in {1..100}; do
  curl -s http://localhost:5002/payment/chain \
    -X POST -H "Content-Type: application/json" \
    -d '{"product_id": "1"}' &
done
wait
```

## 🧹 Cleanup

### Stop All Chaos Experiments

```bash
kubectl delete networkchaos --all -n payment-chaos
kubectl delete podchaos --all -n payment-chaos
kubectl delete stresschaos --all -n payment-chaos
kubectl delete workflow --all -n payment-chaos
kubectl delete schedule --all -n payment-chaos
```

### Delete Namespace

```bash
kubectl delete namespace payment-chaos
```

## 📈 Monitoring

View experiments in Chaos Mesh Dashboard:

```bash
kubectl port-forward -n chaos-mesh svc/chaos-dashboard 2333:2333
# Open browser: http://localhost:2333
```

## 📚 Documentation

For detailed test process, results, and analysis, see: `Dokuman.md` (40+ pages, Turkish)

## 🛠️ Technologies

- **Python 3.11** (Flask framework)
- **Kubernetes** (Minikube)
- **Chaos Mesh** (v2.6+)
- **Docker**

## ⚙️ Resource Configuration

| Service      | Port | Replicas | CPU Limit | Memory Limit |
| ------------ | ---- | -------- | --------- | ------------ |
| Payment      | 5002 | 3        | 200m      | 128Mi        |
| Inventory    | 5003 | 2        | 200m      | 128Mi        |
| Notification | 5004 | 2        | 200m      | 128Mi        |

## ⚠️ Important Notes

1. **Aggressive scenarios**: 80%+ packet loss severely affects services
2. **Timeout settings**: Services configured with 10-30s timeouts
3. **Replica count**: Payment: 3, Inventory: 2, Notification: 2
4. **Resource limits**: Each pod limited to 128Mi RAM, 200m CPU
5. **Test focus**: Only packet loss and CPU/Memory stress tests are active

## 📄 License

MIT License - Educational project

## 🤝 Contributing

This is an educational project. Feel free to fork and experiment with different chaos scenarios!

## 🔗 References

- [Chaos Mesh Documentation](https://chaos-mesh.org/docs/)
- [NetworkChaos API](https://chaos-mesh.org/docs/simulate-network-chaos-on-kubernetes/)
- [StressChaos API](https://chaos-mesh.org/docs/simulate-heavy-stress-on-kubernetes/)
