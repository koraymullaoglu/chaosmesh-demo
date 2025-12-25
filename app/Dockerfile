FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Varsayılan olarak payment service, override edilebilir
ENV SERVICE_TYPE=payment

# Port mapping:
# payment: 5002
# inventory: 5003
# notification: 5004

CMD if [ "$SERVICE_TYPE" = "inventory" ]; then \
        gunicorn -b 0.0.0.0:5003 inventory_service:app; \
    elif [ "$SERVICE_TYPE" = "notification" ]; then \
        gunicorn -b 0.0.0.0:5004 notification_service:app; \
    else \
        gunicorn -b 0.0.0.0:5002 payment_service:app; \
    fi
