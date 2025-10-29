# Shopping Microservices Application - Complete Guide

A comprehensive microservices-based shopping application demonstrating Kong API Gateway, synchronous REST communication, and asynchronous messaging with ActiveMQ.

---

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Installation & Setup](#installation--setup)
4. [Testing with Postman](#testing-with-postman)
5. [API Endpoints Reference](#api-endpoints-reference)
6. [Understanding the Flow](#understanding-the-flow)
7. [Troubleshooting](#troubleshooting)
8. [Stopping the Application](#stopping-the-application)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT (Browser/Postman)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              CUSTOMER SERVICE (External - Port 5003)            │
│              - Customer-facing API                              │
│              - ActiveMQ Integration (Async)                     │
│              - Payment Processing Coordination                  │
└──────────────┬─────────────────────────────┬────────────────────┘
               │                             │
               │ (via Kong Gateway)          │ (ActiveMQ STOMP)
               │                             │
               ▼                             ▼
┌──────────────────────────────┐   ┌─────────────────────────────┐
│    KONG API GATEWAY          │   │       ACTIVEMQ              │
│    Ports: 8000, 8001         │   │  Ports: 61616, 61613, 8161  │
│    - Routes external to      │   │  - Message Broker           │
│      internal services       │   │  - Async Communication      │
└──────────┬───────────────────┘   └─────────────────────────────┘
           │
           │ Routes to internal/external services
           │
     ┌─────┴──────┬────────────┐
     │            │            │
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ PRODUCT │  │  ORDER  │  │ PAYMENT │
│ SERVICE │◄─┤ SERVICE │◄─┤ SERVICE │
│ (5001)  │  │ (5002)  │  │ (5004)  │
└─────────┘  └─────────┘  └─────────┘
  Internal      Internal     External
  (Sync)        (Sync)       (Sync)
```

**Key Components:**
- **2 Internal Services:** Product Service, Order Service (communicate via REST)
- **2 External Services:** Customer Service, Payment Service (use both sync & async communication)
- **Kong API Gateway:** Routes external traffic to internal/external services
- **ActiveMQ:** Message broker for asynchronous communication

---

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ **Docker Desktop** installed and running
- ✅ **Docker Compose** (comes with Docker Desktop)
- ✅ **Postman** (for testing) or any REST client
- ✅ At least **8GB RAM** available for Docker

**Check Docker installation:**
```powershell
docker --version
docker-compose --version
```

---

## 🚀 Installation & Setup

### Step 1: Navigate to Project Directory

```powershell
cd d:\7-MAP\prac7
```

### Step 2: Start All Services

```powershell
# Start all containers in detached mode
docker-compose up -d
```

**Expected output:**
```
[+] Running 6/6
 ✔ Container kong-database     Started
 ✔ Container activemq          Started
 ✔ Container product-service   Started
 ✔ Container order-service     Started
 ✔ Container kong-gateway      Started
 ✔ Container customer-service  Started
```

### Step 3: Wait for Services to Initialize

```powershell
# Wait 30-45 seconds for all services to start
timeout /t 45
```

### Step 4: Verify All Services are Running

```powershell
# Check status of all containers
docker-compose ps
```

**All services should show "Up" or "Up (healthy)" status:**
```
NAME               STATUS
activemq           Up (unhealthy)     ← This is OK, it's running
customer-service   Up (healthy)
kong-gateway       Up (healthy)
order-service      Up (healthy)
product-service    Up (healthy)
kong-database      Up (healthy)
```

### Step 5: Quick Health Check

```powershell
# Test the main entry point
Invoke-WebRequest http://localhost:5003/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "customer-service",
  "activemq": "connected"
}
```

✅ **If you see this, your application is ready to use!**

---

## 🧪 Testing with Postman

### Quick Start: Essential Tests

Open Postman and test these endpoints in order:

---

### 1. Health Check - Verify System Status

```
Method: GET
URL: http://localhost:5003/health
```

**Expected Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "customer-service",
  "activemq": "connected"
}
```

---

### 2. Get All Products - Test Synchronous Communication

```
Method: GET
URL: http://localhost:5003/products
```

**Expected Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Laptop",
    "description": "High-performance laptop",
    "price": 999.99,
    "stock": 10
  },
  {
    "id": 2,
    "name": "Smartphone",
    "description": "Latest smartphone model",
    "price": 699.99,
    "stock": 25
  },
  {
    "id": 3,
    "name": "Headphones",
    "description": "Wireless noise-cancelling headphones",
    "price": 199.99,
    "stock": 50
  },
  {
    "id": 4,
    "name": "Tablet",
    "description": "10-inch tablet with stylus",
    "price": 449.99,
    "stock": 15
  },
  {
    "id": 5,
    "name": "Smart Watch",
    "description": "Fitness tracking smartwatch",
    "price": 299.99,
    "stock": 30
  }
]
```

✅ **This tests:** Customer Service → Kong Gateway → Product Service

---

### 3. Get Single Product

```
Method: GET
URL: http://localhost:5003/products/1
```

**Expected Response (200 OK):**
```json
{
  "id": 1,
  "name": "Laptop",
  "description": "High-performance laptop",
  "price": 999.99,
  "stock": 10
}
```

---

### 4. Create Order - Test Both Sync & Async Communication

```
Method: POST
URL: http://localhost:5003/orders
Headers:
  Content-Type: application/json
Body (raw JSON):
```
```json
{
  "customer_id": 1,
  "product_id": 1,
  "quantity": 2
}
```

**Expected Response (201 Created):**
```json
{
  "id": 1,
  "customer_id": 1,
  "product_id": 1,
  "product_name": "Laptop",
  "quantity": 2,
  "total_price": 1999.98,
  "status": "PENDING",
  "message": "Order created successfully",
  "notification_sent": true
}
```

✅ **This tests:** 
- **Synchronous:** Customer → Kong → Order → Product (validates & updates stock)
- **Asynchronous:** Order notification sent to ActiveMQ queue

---

### 5. Get Customer Orders

```
Method: GET
URL: http://localhost:5003/orders/customer/1
```

**Expected Response (200 OK):**
```json
[
  {
    "id": 1,
    "customer_id": 1,
    "product_id": 1,
    "product_name": "Laptop",
    "quantity": 2,
    "total_price": 1999.98,
    "status": "PENDING",
    "created_at": "2025-10-01T10:30:00"
  }
]
```

---

### 6. Get Notifications - Test ActiveMQ Asynchronous Messaging

```
Method: GET
URL: http://localhost:5003/notifications
```

**Expected Response (200 OK):**
```json
{
  "notifications": [
    {
      "event": "ORDER_CREATED",
      "order_id": 1,
      "customer_id": 1,
      "product_name": "Laptop",
      "quantity": 2,
      "total_price": 1999.98,
      "timestamp": "2025-10-01 10:30:00"
    }
  ],
  "count": 1
}
```

✅ **This tests:** ActiveMQ asynchronous messaging - notification was sent and received!

---

### 7. Send Test Message to ActiveMQ

```
Method: POST
URL: http://localhost:5003/test-message
Headers:
  Content-Type: application/json
Body (raw JSON):
```
```json
{
  "message": "Testing ActiveMQ from Postman!"
}
```

**Expected Response (200 OK):**
```json
{
  "message": "Test message sent successfully",
  "data": {
    "event": "TEST_MESSAGE",
    "message": "Testing ActiveMQ from Postman!",
    "timestamp": "2025-10-01 10:35:00"
  }
}
```

Then check notifications again - you should see the test message!

---

### 8. Get Payment Methods - Test Payment Service

```
Method: GET
URL: http://localhost:5003/payment-methods
```

**Expected Response (200 OK):**
```json
{
  "payment_methods": [
    {
      "id": "credit_card",
      "name": "Credit Card",
      "enabled": true
    },
    {
      "id": "debit_card",
      "name": "Debit Card",
      "enabled": true
    },
    {
      "id": "paypal",
      "name": "PayPal",
      "enabled": true
    },
    {
      "id": "bank_transfer",
      "name": "Bank Transfer",
      "enabled": true
    },
    {
      "id": "cash_on_delivery",
      "name": "Cash on Delivery",
      "enabled": true
    }
  ]
}
```

✅ **This tests:** Customer Service → Kong Gateway → Payment Service

---

### 9. Process Payment

```
Method: POST
URL: http://localhost:5003/payments
Headers:
  Content-Type: application/json
Body (raw JSON):
```
```json
{
  "order_id": 1,
  "customer_id": 1,
  "amount": 1999.98,
  "payment_method": "credit_card"
}
```

**Expected Response (201 Created):**
```json
{
  "id": 1,
  "order_id": 1,
  "customer_id": 1,
  "amount": 1999.98,
  "payment_method": "credit_card",
  "status": "SUCCESS",
  "transaction_id": "TXN1234567890",
  "message": "Payment processed successfully",
  "notification_sent": true
}
```

✅ **This tests:** 
- **Synchronous:** Customer → Kong → Payment → Order (updates order status)
- **Asynchronous:** Payment notification sent to ActiveMQ queue

**Note:** The payment has a 90% success rate. If payment fails, you'll get:
```json
{
  "id": 1,
  "order_id": 1,
  "customer_id": 1,
  "amount": 1999.98,
  "payment_method": "credit_card",
  "status": "FAILED",
  "transaction_id": "TXN1234567890",
  "message": "Payment processing failed"
}
```

---

### 10. Get Customer Payments

```
Method: GET
URL: http://localhost:5003/payments/customer/1
```

**Expected Response (200 OK):**
```json
[
  {
    "id": 1,
    "order_id": 1,
    "customer_id": 1,
    "amount": 1999.98,
    "payment_method": "credit_card",
    "status": "SUCCESS",
    "transaction_id": "TXN1234567890",
    "created_at": "2025-10-01T10:40:00"
  }
]
```

---

### 11. Get Order Payments

```
Method: GET
URL: http://localhost:5003/payments/order/1
```

**Expected Response (200 OK):**
```json
[
  {
    "id": 1,
    "order_id": 1,
    "customer_id": 1,
    "amount": 1999.98,
    "payment_method": "credit_card",
    "status": "SUCCESS",
    "transaction_id": "TXN1234567890",
    "created_at": "2025-10-01T10:40:00"
  }
]
```

---

### 12. Get Customer-Specific Notifications

```
Method: GET
URL: http://localhost:5003/notifications/customer/1
```

**Expected Response (200 OK):**
```json
{
  "notifications": [
    {
      "event": "ORDER_CREATED",
      "order_id": 1,
      "customer_id": 1,
      "product_name": "Laptop",
      "quantity": 2,
      "total_price": 1999.98,
      "timestamp": "2025-10-01 10:30:00"
    },
    {
      "event": "PAYMENT_PROCESSED",
      "payment_id": 1,
      "order_id": 1,
      "customer_id": 1,
      "amount": 1999.98,
      "status": "SUCCESS",
      "timestamp": "2025-10-01 10:40:00"
    }
  ],
  "count": 2
}
```

---

### 📦 Import Postman Collection

Save this as `Shopping-Microservices.postman_collection.json` and import into Postman:

```json
{
  "info": {
    "name": "Shopping Microservices",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "1. Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:5003/health"
      }
    },
    {
      "name": "2. Get All Products",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:5003/products"
      }
    },
    {
      "name": "3. Get Product by ID",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:5003/products/1"
      }
    },
    {
      "name": "4. Create Order",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\"customer_id\": 1, \"product_id\": 1, \"quantity\": 2}"
        },
        "url": "http://localhost:5003/orders"
      }
    },
    {
      "name": "5. Get Customer Orders",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:5003/orders/customer/1"
      }
    },
    {
      "name": "6. Get All Notifications",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:5003/notifications"
      }
    },
    {
      "name": "7. Send Test Message",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\"message\": \"Testing ActiveMQ!\"}"
        },
        "url": "http://localhost:5003/test-message"
      }
    },
    {
      "name": "8. Get Payment Methods",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:5003/payment-methods"
      }
    },
    {
      "name": "9. Process Payment",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\"order_id\": 1, \"customer_id\": 1, \"amount\": 1999.98, \"payment_method\": \"credit_card\"}"
        },
        "url": "http://localhost:5003/payments"
      }
    },
    {
      "name": "10. Get Customer Payments",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:5003/payments/customer/1"
      }
    },
    {
      "name": "11. Get Order Payments",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:5003/payments/order/1"
      }
    },
    {
      "name": "12. Get Customer Notifications",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:5003/notifications/customer/1"
      }
    }
  ]
}
```

**To import:**
1. Open Postman
2. Click **Import** → **Upload Files**
3. Select the JSON file
4. Start testing!

---

## 📚 API Endpoints Reference

### Customer Service (Port 5003) - Main Entry Point

All endpoints accessed via: `http://localhost:5003`

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| `GET` | `/health` | Health check with ActiveMQ status | - |
| `GET` | `/products` | Get all products (via Kong) | - |
| `GET` | `/products/{id}` | Get specific product | - |
| `POST` | `/orders` | Create new order (sync + async) | `{"customer_id": 1, "product_id": 1, "quantity": 2}` |
| `GET` | `/orders/customer/{id}` | Get customer orders | - |
| `GET` | `/payment-methods` | Get available payment methods | - |
| `POST` | `/payments` | Process payment | `{"order_id": 1, "customer_id": 1, "amount": 1999.98, "payment_method": "credit_card"}` |
| `GET` | `/payments/customer/{id}` | Get customer payments | - |
| `GET` | `/payments/order/{id}` | Get order payments | - |
| `GET` | `/notifications` | Get all ActiveMQ notifications | - |
| `GET` | `/notifications/customer/{id}` | Get customer notifications | - |
| `POST` | `/test-message` | Send test message to ActiveMQ | `{"message": "test"}` |

### Product Service (Port 5001) - Direct Access (Optional)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health check |
| `GET` | `/products` | Get all products |
| `GET` | `/products/{id}` | Get product by ID |
| `POST` | `/products` | Create new product |
| `PUT` | `/products/{id}/stock` | Update stock |

### Order Service (Port 5002) - Direct Access (Optional)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health check |
| `POST` | `/orders` | Create order |
| `GET` | `/orders/{id}` | Get order by ID |
| `GET` | `/orders/customer/{id}` | Get customer orders |
| `PUT` | `/orders/{id}/status` | Update order status |

### Payment Service (Port 5004) - Direct Access (Optional)

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| `GET` | `/health` | Service health check | - |
| `GET` | `/payment-methods` | Get available payment methods | - |
| `POST` | `/payments` | Process payment | `{"order_id": 1, "customer_id": 1, "amount": 1999.98, "payment_method": "credit_card"}` |
| `GET` | `/payments/{id}` | Get payment by ID | - |
| `GET` | `/payments/customer/{id}` | Get customer payments | - |
| `GET` | `/payments/order/{id}` | Get order payments | - |
| `POST` | `/payments/{id}/refund` | Process refund | `{"reason": "Customer request"}` |

### Kong Gateway (Port 8000) - Alternative Access

| Endpoint | Destination |
|----------|-------------|
| `http://localhost:8000/product-service/*` | Product Service |
| `http://localhost:8000/order-service/*` | Order Service |
| `http://localhost:8000/payment-service/*` | Payment Service |

### Web Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| ActiveMQ Console | http://localhost:8161 | admin / admin |
| Kong Admin API | http://localhost:8001 | - |

---

## 🔍 Understanding the Flow

### What Happens When You Create an Order and Process Payment?

```
PART 1: Order Creation Flow
═══════════════════════════════════════════════════════════════
Step 1: Client sends POST request
   ↓
   POST http://localhost:5003/orders
   {"customer_id": 1, "product_id": 1, "quantity": 2}

Step 2: Customer Service receives request
   ↓
   Forwards to Kong Gateway (Synchronous)

Step 3: Kong routes to Order Service
   ↓
   http://kong:8000/order-service/orders

Step 4: Order Service validates with Product Service
   ↓
   GET http://product-service:5001/products/1
   Checks if stock >= quantity

Step 5: Product Service updates stock
   ↓
   PUT http://product-service:5001/products/1/stock
   {"quantity": 2}
   Stock: 10 → 8

Step 6: Order Service creates order
   ↓
   Saves to database with status "PENDING"

Step 7: Customer Service sends notification to ActiveMQ (Asynchronous)
   ↓
   Publishes message to queue: "order-notifications"
   {
     "event": "ORDER_CREATED",
     "order_id": 1,
     "customer_id": 1,
     "product_name": "Laptop",
     "quantity": 2,
     "total_price": 1999.98
   }

Step 8: Customer Service receives notification from ActiveMQ
   ↓
   Subscribes to queue: "order-notifications"
   Stores notification in memory

Step 9: Client receives response
   ↓
   {
     "id": 1,
     "message": "Order created successfully",
     "notification_sent": true
   }


PART 2: Payment Processing Flow
═══════════════════════════════════════════════════════════════
Step 1: Client sends payment request
   ↓
   POST http://localhost:5003/payments
   {"order_id": 1, "customer_id": 1, "amount": 1999.98, "payment_method": "credit_card"}

Step 2: Customer Service receives request
   ↓
   Forwards to Kong Gateway (Synchronous)

Step 3: Kong routes to Payment Service
   ↓
   http://kong:8000/payment-service/payments

Step 4: Payment Service processes payment
   ↓
   Simulates payment gateway (90% success rate)
   Creates payment record with transaction ID

Step 5: Payment Service updates Order status
   ↓
   PUT http://order-service:5002/orders/1/status
   {"status": "PAID"}
   Order status: PENDING → PAID

Step 6: Payment Service returns to Customer Service
   ↓
   {
     "id": 1,
     "status": "SUCCESS",
     "transaction_id": "TXN1234567890"
   }

Step 7: Customer Service sends payment notification to ActiveMQ (Asynchronous)
   ↓
   Publishes message to queue: "order-notifications"
   {
     "event": "PAYMENT_PROCESSED",
     "payment_id": 1,
     "order_id": 1,
     "customer_id": 1,
     "amount": 1999.98,
     "status": "SUCCESS"
   }

Step 8: Customer Service receives notification from ActiveMQ
   ↓
   Subscribes to queue: "order-notifications"
   Stores notification in memory

Step 9: Client receives response
   ↓
   {
     "id": 1,
     "status": "SUCCESS",
     "message": "Payment processed successfully",
     "notification_sent": true
   }
```

**Communication Patterns Demonstrated:**
- ✅ **Synchronous:** Customer → Kong → Order → Product (REST APIs)
- ✅ **Synchronous:** Customer → Kong → Payment → Order (REST APIs)
- ✅ **Asynchronous:** Order & Payment notifications via ActiveMQ (STOMP)
- ✅ **API Gateway:** Kong routes external to internal/external services
- ✅ **Service Isolation:** 2 Internal services (Product, Order) + 2 External services (Customer, Payment)
- ✅ **Payment Gateway Simulation:** 90% success rate with transaction IDs

---

## 🐛 Troubleshooting

### Issue 1: Services Not Starting

**Problem:** Containers exit or show unhealthy status

**Solution:**
```powershell
# Stop everything
docker-compose down

# Remove old containers and volumes
docker-compose down -v

# Rebuild and start
docker-compose up --build -d

# Wait 45 seconds
timeout /t 45
```

---

### Issue 2: Connection Refused / 404 Errors

**Problem:** Getting "Connection refused" or 404 on endpoints

**Solution:**
```powershell
# Check all services are running
docker-compose ps

# Should see all with "Up" status
# If kong-gateway is not healthy, restart it
docker restart kong-gateway

# Wait 10 seconds
timeout /t 10

# Try again
Invoke-WebRequest http://localhost:5003/health
```

---

### Issue 3: No Notifications Appearing

**Problem:** Notifications endpoint returns empty array

**Solution:**
1. First, check ActiveMQ is running:
   ```powershell
   docker logs activemq --tail 20
   ```
   Should see: "Apache ActiveMQ ... started"

2. Check customer-service connection:
   ```powershell
   docker logs customer-service --tail 30
   ```
   Should see: "Connected to ActiveMQ successfully"

3. If not connected, restart customer-service:
   ```powershell
   docker restart customer-service
   timeout /t 10
   ```

---

### Issue 4: Stock Not Updating

**Problem:** Orders succeed but product stock doesn't decrease

**Solution:**
```powershell
# Check product-service logs
docker logs product-service --tail 30

# Check order-service logs
docker logs order-service --tail 30

# Restart both services
docker restart product-service order-service

# Wait and retry
timeout /t 10
```

---

### Issue 5: Port Already in Use

**Problem:** Error "port is already allocated"

**Solution:**
```powershell
# Find what's using the port (example for 5003)
netstat -ano | findstr :5003

# Stop the process using the port
# Or change ports in docker-compose.yml
```

---

### View Logs for Debugging

```powershell
# All services
docker-compose logs -f

# Specific service
docker logs customer-service -f
docker logs product-service -f
docker logs order-service -f
docker logs kong-gateway -f
docker logs activemq -f

# Last 50 lines
docker logs customer-service --tail 50
```

---

### Verify Services Individually

```powershell
# Product Service
Invoke-WebRequest http://localhost:5001/health

# Order Service
Invoke-WebRequest http://localhost:5002/health

# Customer Service
Invoke-WebRequest http://localhost:5003/health

# Kong Gateway
Invoke-WebRequest http://localhost:8001/status

# ActiveMQ Console (browser)
# http://localhost:8161
```

---

### Complete Reset

If nothing works, do a complete reset:

```powershell
# Stop and remove everything
docker-compose down -v

# Remove all shopping-related containers
docker ps -a | findstr prac7

# Remove images (optional)
docker rmi prac7-customer-service prac7-order-service prac7-product-service

# Start fresh
docker-compose up --build -d

# Wait 60 seconds
timeout /t 60

# Test
Invoke-WebRequest http://localhost:5003/health
```

---

## 🛑 Stopping the Application

### Normal Stop

```powershell
# Stop all containers
docker-compose down
```

### Stop and Remove All Data

```powershell
# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Remove Everything Including Images

```powershell
# Stop, remove volumes, and remove built images
docker-compose down -v --rmi all
```

---

## ✅ Verification Checklist

Use this to verify your application is working correctly:

- [ ] All 6 containers are running (`docker-compose ps`)
- [ ] Health check returns "healthy" and "connected"
- [ ] Can retrieve all 5 products
- [ ] Can get individual product by ID
- [ ] Can create an order successfully
- [ ] Order response shows `notification_sent: true`
- [ ] Can view customer orders
- [ ] Notifications endpoint shows order notification
- [ ] Can send test message to ActiveMQ
- [ ] Test message appears in notifications list
- [ ] Stock decreases after placing orders
- [ ] Can access ActiveMQ console at http://localhost:8161
- [ ] Error handling works (try invalid product ID)

---

## 🎯 Quick 2-Minute Test

Want to verify everything quickly? Run this sequence in Postman:

1. ✅ `GET http://localhost:5003/health` → 200 OK
2. ✅ `GET http://localhost:5003/products` → 5 products
3. ✅ `POST http://localhost:5003/orders` (Laptop, qty: 2) → 201 Created
4. ✅ `GET http://localhost:5003/notifications` → Order notification present
5. ✅ `GET http://localhost:5003/products` → Laptop stock reduced by 2

**If all 5 work → Application is 100% functional! 🎉**

---

## 📊 Sample Data

The application comes pre-loaded with these products:

| ID | Name | Description | Price | Stock |
|----|------|-------------|-------|-------|
| 1 | Laptop | High-performance laptop | $999.99 | 10 |
| 2 | Smartphone | Latest smartphone model | $699.99 | 25 |
| 3 | Headphones | Wireless noise-cancelling | $199.99 | 50 |
| 4 | Tablet | 10-inch tablet with stylus | $449.99 | 15 |
| 5 | Smart Watch | Fitness tracking smartwatch | $299.99 | 30 |

---

## 🎓 What You're Learning

This application demonstrates:

1. **Microservices Architecture** - Independent, loosely coupled services
2. **API Gateway Pattern** - Kong routes external requests to internal services
3. **Synchronous Communication** - REST APIs for real-time operations
4. **Asynchronous Communication** - Message queues for background processing
5. **Service Discovery** - Services communicate via container names
6. **Container Orchestration** - Docker Compose manages multi-container app
7. **Health Checks** - Monitoring service availability
8. **Message Broker** - ActiveMQ for pub/sub messaging

---

## 📝 Project Structure

```
prac7/
├── docker-compose.yml          # Container orchestration
├── kong.yml                    # Kong Gateway configuration
├── customer-service/           # External service
│   ├── app.py                 # Customer API + ActiveMQ
│   ├── Dockerfile
│   └── requirements.txt
├── order-service/              # Internal service
│   ├── app.py                 # Order processing
│   ├── Dockerfile
│   └── requirements.txt
├── product-service/            # Internal service
│   ├── app.py                 # Product catalog
│   ├── Dockerfile
│   └── requirements.txt
└── USER_GUIDE.md              # This file
```

---

## 🚀 Next Steps (Optional Enhancements)

Want to extend this project? Try adding:

1. **Authentication** - JWT tokens for secure API access
2. **Rate Limiting** - Configure Kong to limit requests
3. **Database** - Replace SQLite with PostgreSQL/MySQL
4. **Caching** - Add Redis for frequently accessed data
5. **Monitoring** - Prometheus + Grafana dashboards
6. **Logging** - Centralized logging with ELK stack
7. **Circuit Breaker** - Handle service failures gracefully
8. **Load Balancing** - Multiple instances of each service

---

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. View service logs: `docker logs <service-name>`
3. Verify all services are up: `docker-compose ps`
4. Try complete reset (see Troubleshooting section)

---

**🎉 Congratulations! You now have a fully functional microservices application demonstrating both synchronous and asynchronous communication patterns!**

**Happy Shopping! 🛒**
