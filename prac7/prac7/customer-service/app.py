from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import stomp
import json
import threading
import time

app = Flask(__name__)
CORS(app)

# Kong Gateway URLs (external access point)
KONG_GATEWAY_URL = os.environ.get('KONG_GATEWAY_URL', 'http://kong:8000')
ACTIVEMQ_HOST = os.environ.get('ACTIVEMQ_HOST', 'localhost')
ACTIVEMQ_PORT = int(os.environ.get('ACTIVEMQ_PORT', 61613))

# Store order notifications in memory (in production, use a database)
order_notifications = []

class OrderNotificationListener(stomp.ConnectionListener):
    """Listener for ActiveMQ order notifications"""
    
    def on_error(self, frame):
        print(f'ActiveMQ Error: {frame.body}')
    
    def on_message(self, frame):
        print(f'Received message: {frame.body}')
        try:
            message = json.loads(frame.body)
            order_notifications.append(message)
            print(f'Order notification added: {message}')
        except Exception as e:
            print(f'Error processing message: {e}')

# ActiveMQ connection setup
activemq_conn = None

def connect_activemq():
    """Connect to ActiveMQ broker"""
    global activemq_conn
    activemq_conn = stomp.Connection([(ACTIVEMQ_HOST, ACTIVEMQ_PORT)])
    activemq_conn.set_listener('', OrderNotificationListener())
    # This call may raise an exception if the broker is unreachable or credentials are invalid.
    # Let the caller handle retries so we can report failure correctly.
    activemq_conn.connect('admin', 'admin', wait=True)
    activemq_conn.subscribe(destination='/queue/order-notifications', id=1, ack='auto')
    print('Connected to ActiveMQ successfully')

# Connect to ActiveMQ on startup (with retry logic)
def init_activemq():
    """Initialize ActiveMQ connection with retry logic"""
    # Start a background thread that will keep trying to (re)connect
    def monitor():
        retry_delay = 5
        while True:
            try:
                if activemq_conn is None or not activemq_conn.is_connected():
                    print('Attempting to connect to ActiveMQ...')
                    try:
                        connect_activemq()
                        print('ActiveMQ connection established')
                    except Exception as e:
                        print(f'ActiveMQ connection failed: {e}')
                # If connected, sleep longer; otherwise retry after short delay
                time.sleep(retry_delay if activemq_conn is None or not (activemq_conn and activemq_conn.is_connected()) else 10)
            except Exception as e:
                print(f'ActiveMQ monitor encountered error: {e}')
                time.sleep(retry_delay)

    threading.Thread(target=monitor, daemon=True).start()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    activemq_status = 'connected' if activemq_conn and activemq_conn.is_connected() else 'disconnected'
    return jsonify({
        'status': 'healthy',
        'service': 'customer-service',
        'activemq': activemq_status
    }), 200

@app.route('/products', methods=['GET'])
def get_products():
    """Get all products via Kong Gateway (synchronous)"""
    try:
        response = requests.get(f'{KONG_GATEWAY_URL}/product-service/products')
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to fetch products: {str(e)}'}), 500

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get specific product via Kong Gateway (synchronous)"""
    try:
        response = requests.get(f'{KONG_GATEWAY_URL}/product-service/products/{product_id}')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to fetch product: {str(e)}'}), 500

@app.route('/orders', methods=['POST'])
def create_order():
    """
    Create an order via Kong Gateway (synchronous) 
    and send notification via ActiveMQ (asynchronous)
    """
    data = request.get_json()
    
    if not all(k in data for k in ('customer_id', 'product_id', 'quantity')):
        return jsonify({'error': 'Missing required fields: customer_id, product_id, quantity'}), 400
    
    try:
        # Synchronous: Create order via Kong Gateway to Order Service
        response = requests.post(
            f'{KONG_GATEWAY_URL}/order-service/orders',
            json=data
        )
        
        if response.status_code == 201:
            order_data = response.json()
            
            # Asynchronous: Send order notification to ActiveMQ
            if activemq_conn and activemq_conn.is_connected():
                notification_message = {
                    'event': 'ORDER_CREATED',
                    'order_id': order_data['id'],
                    'customer_id': data['customer_id'],
                    'product_name': order_data.get('product_name', 'Unknown'),
                    'quantity': data['quantity'],
                    'total_price': order_data.get('total_price', 0),
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                activemq_conn.send(
                    body=json.dumps(notification_message),
                    destination='/queue/order-notifications'
                )
                
                order_data['notification_sent'] = True
            else:
                order_data['notification_sent'] = False
                order_data['warning'] = 'Order created but notification service unavailable'
            
            return jsonify(order_data), 201
        else:
            return jsonify(response.json()), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to create order: {str(e)}'}), 500

@app.route('/orders/customer/<int:customer_id>', methods=['GET'])
def get_customer_orders(customer_id):
    """Get customer orders via Kong Gateway (synchronous)"""
    try:
        response = requests.get(f'{KONG_GATEWAY_URL}/order-service/orders/customer/{customer_id}')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to fetch orders: {str(e)}'}), 500

@app.route('/notifications', methods=['GET'])
def get_notifications():
    """Get all order notifications (asynchronous messages from ActiveMQ)"""
    return jsonify({
        'notifications': order_notifications,
        'count': len(order_notifications)
    }), 200

@app.route('/notifications/customer/<int:customer_id>', methods=['GET'])
def get_customer_notifications(customer_id):
    """Get notifications for a specific customer"""
    customer_notifs = [n for n in order_notifications if n.get('customer_id') == customer_id]
    return jsonify({
        'notifications': customer_notifs,
        'count': len(customer_notifs)
    }), 200

@app.route('/test-message', methods=['POST'])
def send_test_message():
    """Send a test message to ActiveMQ (for testing async communication)"""
    data = request.get_json()
    
    if not activemq_conn or not activemq_conn.is_connected():
        return jsonify({'error': 'ActiveMQ not connected'}), 503
    
    try:
        test_message = {
            'event': 'TEST_MESSAGE',
            'message': data.get('message', 'Test message'),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        activemq_conn.send(
            body=json.dumps(test_message),
            destination='/queue/order-notifications'
        )
        
        return jsonify({'message': 'Test message sent successfully', 'data': test_message}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to send message: {str(e)}'}), 500

@app.route('/payment-methods', methods=['GET'])
def get_payment_methods():
    """Get available payment methods via Kong Gateway (synchronous)"""
    try:
        response = requests.get(f'{KONG_GATEWAY_URL}/payment-service/payment-methods')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to fetch payment methods: {str(e)}'}), 500

@app.route('/payments', methods=['POST'])
def process_payment():
    """
    Process payment via Kong Gateway (synchronous)
    and send notification via ActiveMQ (asynchronous)
    """
    data = request.get_json()
    
    if not all(k in data for k in ('order_id', 'customer_id', 'amount', 'payment_method')):
        return jsonify({'error': 'Missing required fields: order_id, customer_id, amount, payment_method'}), 400
    
    try:
        # Synchronous: Process payment via Kong Gateway to Payment Service
        response = requests.post(
            f'{KONG_GATEWAY_URL}/payment-service/payments',
            json=data
        )
        
        if response.status_code in [201, 402]:
            payment_data = response.json()
            
            # Asynchronous: Send payment notification to ActiveMQ
            if activemq_conn and activemq_conn.is_connected():
                notification_message = {
                    'event': 'PAYMENT_PROCESSED',
                    'payment_id': payment_data.get('id'),
                    'order_id': data['order_id'],
                    'customer_id': data['customer_id'],
                    'amount': data['amount'],
                    'status': payment_data.get('status'),
                    'transaction_id': payment_data.get('transaction_id'),
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                activemq_conn.send(
                    body=json.dumps(notification_message),
                    destination='/queue/order-notifications'
                )
                
                payment_data['notification_sent'] = True
            else:
                payment_data['notification_sent'] = False
            
            return jsonify(payment_data), response.status_code
        else:
            return jsonify(response.json()), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to process payment: {str(e)}'}), 500

@app.route('/payments/customer/<int:customer_id>', methods=['GET'])
def get_customer_payments(customer_id):
    """Get customer payments via Kong Gateway (synchronous)"""
    try:
        response = requests.get(f'{KONG_GATEWAY_URL}/payment-service/payments/customer/{customer_id}')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to fetch payments: {str(e)}'}), 500

@app.route('/payments/order/<int:order_id>', methods=['GET'])
def get_order_payments(order_id):
    """Get order payments via Kong Gateway (synchronous)"""
    try:
        response = requests.get(f'{KONG_GATEWAY_URL}/payment-service/payments/order/{order_id}')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to fetch order payments: {str(e)}'}), 500

if __name__ == '__main__':
    # Initialize ActiveMQ in a separate thread
    threading.Thread(target=init_activemq, daemon=True).start()
    
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=True)
