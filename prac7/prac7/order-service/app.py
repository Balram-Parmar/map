from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import requests
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_PATH = 'orders.db'
PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://product-service:5001')

def init_db():
    """Initialize the orders database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'order-service'}), 200

@app.route('/orders', methods=['POST'])
def create_order():
    """Create a new order (synchronous communication with Product Service)"""
    data = request.get_json()
    
    if not all(k in data for k in ('customer_id', 'product_id', 'quantity')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Synchronous call to Product Service to check availability and get product details
    try:
        product_response = requests.get(f'{PRODUCT_SERVICE_URL}/products/{data["product_id"]}')
        
        if product_response.status_code == 404:
            return jsonify({'error': 'Product not found'}), 404
        
        product_response.raise_for_status()
        product = product_response.json()
        
        if product['stock'] < data['quantity']:
            return jsonify({
                'error': 'Insufficient stock',
                'available': product['stock'],
                'requested': data['quantity']
            }), 400
        
        # Update stock in Product Service (synchronous)
        stock_response = requests.put(
            f'{PRODUCT_SERVICE_URL}/products/{data["product_id"]}/stock',
            json={'quantity': data['quantity']}
        )
        stock_response.raise_for_status()
        
        # Calculate total price
        total_price = product['price'] * data['quantity']
        
        # Create order in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO orders (customer_id, product_id, product_name, quantity, total_price, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (data['customer_id'], data['product_id'], product['name'], 
             data['quantity'], total_price, 'PENDING', datetime.now().isoformat())
        )
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        order_data = {
            'id': order_id,
            'customer_id': data['customer_id'],
            'product_id': data['product_id'],
            'product_name': product['name'],
            'quantity': data['quantity'],
            'total_price': total_price,
            'status': 'PENDING',
            'message': 'Order created successfully'
        }
        
        return jsonify(order_data), 201
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to communicate with Product Service: {str(e)}'}), 500

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order details by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, customer_id, product_id, product_name, quantity, total_price, status, created_at FROM orders WHERE id = ?',
        (order_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        order = {
            'id': row[0],
            'customer_id': row[1],
            'product_id': row[2],
            'product_name': row[3],
            'quantity': row[4],
            'total_price': row[5],
            'status': row[6],
            'created_at': row[7]
        }
        return jsonify(order), 200
    else:
        return jsonify({'error': 'Order not found'}), 404

@app.route('/orders/customer/<int:customer_id>', methods=['GET'])
def get_customer_orders(customer_id):
    """Get all orders for a specific customer"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, customer_id, product_id, product_name, quantity, total_price, status, created_at FROM orders WHERE customer_id = ?',
        (customer_id,)
    )
    orders = []
    for row in cursor.fetchall():
        orders.append({
            'id': row[0],
            'customer_id': row[1],
            'product_id': row[2],
            'product_name': row[3],
            'quantity': row[4],
            'total_price': row[5],
            'status': row[6],
            'created_at': row[7]
        })
    conn.close()
    return jsonify(orders), 200

@app.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({'error': 'Missing status field'}), 400
    
    valid_statuses = ['PENDING', 'CONFIRMED', 'SHIPPED', 'DELIVERED', 'CANCELLED']
    if data['status'] not in valid_statuses:
        return jsonify({'error': 'Invalid status', 'valid_statuses': valid_statuses}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (data['status'], order_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Order status updated successfully', 'status': data['status']}), 200

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
