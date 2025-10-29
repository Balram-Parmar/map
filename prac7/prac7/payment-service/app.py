from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import requests
import os
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

DB_PATH = 'payments.db'
ORDER_SERVICE_URL = os.environ.get('ORDER_SERVICE_URL', 'http://order-service:5002')

# Simulated payment gateways
PAYMENT_GATEWAYS = ['Stripe', 'PayPal', 'Razorpay', 'Square']

def init_db():
    """Initialize the payments database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            payment_gateway TEXT NOT NULL,
            transaction_id TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'payment-service'}), 200

@app.route('/payment-methods', methods=['GET'])
def get_payment_methods():
    """Get available payment methods"""
    methods = [
        {'id': 1, 'name': 'Credit Card', 'type': 'card', 'fee_percentage': 2.9},
        {'id': 2, 'name': 'Debit Card', 'type': 'card', 'fee_percentage': 2.5},
        {'id': 3, 'name': 'PayPal', 'type': 'digital_wallet', 'fee_percentage': 3.5},
        {'id': 4, 'name': 'UPI', 'type': 'upi', 'fee_percentage': 0.0},
        {'id': 5, 'name': 'Net Banking', 'type': 'bank', 'fee_percentage': 1.5}
    ]
    return jsonify(methods), 200

@app.route('/payments', methods=['POST'])
def process_payment():
    """
    Process a payment for an order
    Validates order, processes payment, updates order status
    """
    data = request.get_json()
    
    if not all(k in data for k in ('order_id', 'customer_id', 'amount', 'payment_method')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate amount
    if data['amount'] <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    # Simulate payment processing
    payment_gateway = random.choice(PAYMENT_GATEWAYS)
    transaction_id = f"TXN-{random.randint(100000, 999999)}"
    
    # Simulate payment success/failure (90% success rate)
    payment_success = random.random() < 0.9
    
    if payment_success:
        # Store payment record
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO payments (order_id, customer_id, amount, payment_method, payment_gateway, transaction_id, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (data['order_id'], data['customer_id'], data['amount'], 
             data['payment_method'], payment_gateway, transaction_id, 'SUCCESS', datetime.now().isoformat())
        )
        payment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update order status in Order Service (synchronous call)
        try:
            order_response = requests.put(
                f'{ORDER_SERVICE_URL}/orders/{data["order_id"]}/status',
                json={'status': 'CONFIRMED'}
            )
            order_updated = order_response.status_code == 200
        except:  
            order_updated = False
        
        return jsonify({
            'id': payment_id,
            'transaction_id': transaction_id,
            'order_id': data['order_id'],
            'amount': data['amount'],
            'payment_method': data['payment_method'],
            'payment_gateway': payment_gateway,
            'status': 'SUCCESS',
            'message': 'Payment processed successfully',
            'order_status_updated': order_updated
        }), 201
    else:
        # Payment failed
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO payments (order_id, customer_id, amount, payment_method, payment_gateway, transaction_id, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (data['order_id'], data['customer_id'], data['amount'], 
             data['payment_method'], payment_gateway, transaction_id, 'FAILED', datetime.now().isoformat())
        )
        payment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'id': payment_id,
            'transaction_id': transaction_id,
            'order_id': data['order_id'],
            'amount': data['amount'],
            'payment_method': data['payment_method'],
            'payment_gateway': payment_gateway,
            'status': 'FAILED',
            'message': 'Payment processing failed. Please try again.',
            'error_code': 'PAYMENT_DECLINED'
        }), 402

@app.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    """Get payment details by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, order_id, customer_id, amount, payment_method, payment_gateway, transaction_id, status, created_at FROM payments WHERE id = ?',
        (payment_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        payment = {
            'id': row[0],
            'order_id': row[1],
            'customer_id': row[2],
            'amount': row[3],
            'payment_method': row[4],
            'payment_gateway': row[5],
            'transaction_id': row[6],
            'status': row[7],
            'created_at': row[8]
        }
        return jsonify(payment), 200
    else:
        return jsonify({'error': 'Payment not found'}), 404

@app.route('/payments/order/<int:order_id>', methods=['GET'])
def get_payments_by_order(order_id):
    """Get all payment attempts for an order"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, order_id, customer_id, amount, payment_method, payment_gateway, transaction_id, status, created_at FROM payments WHERE order_id = ?',
        (order_id,)
    )
    payments = []
    for row in cursor.fetchall():
        payments.append({
            'id': row[0],
            'order_id': row[1],
            'customer_id': row[2],
            'amount': row[3],
            'payment_method': row[4],
            'payment_gateway': row[5],
            'transaction_id': row[6],
            'status': row[7],
            'created_at': row[8]
        })
    conn.close()
    return jsonify(payments), 200

@app.route('/payments/customer/<int:customer_id>', methods=['GET'])
def get_payments_by_customer(customer_id):
    """Get all payments for a customer"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, order_id, customer_id, amount, payment_method, payment_gateway, transaction_id, status, created_at FROM payments WHERE customer_id = ?',
        (customer_id,)
    )
    payments = []
    for row in cursor.fetchall():
        payments.append({
            'id': row[0],
            'order_id': row[1],
            'customer_id': row[2],
            'amount': row[3],
            'payment_method': row[4],
            'payment_gateway': row[5],
            'transaction_id': row[6],
            'status': row[7],
            'created_at': row[8]
        })
    conn.close()
    return jsonify(payments), 200

@app.route('/payments/<int:payment_id>/refund', methods=['POST'])
def refund_payment(payment_id):
    """Process a refund for a payment"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get payment details
    cursor.execute('SELECT status, amount, order_id FROM payments WHERE id = ?', (payment_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({'error': 'Payment not found'}), 404
    
    status, amount, order_id = row
    
    if status != 'SUCCESS':
        conn.close()
        return jsonify({'error': 'Can only refund successful payments'}), 400
    
    # Update payment status to REFUNDED
    cursor.execute('UPDATE payments SET status = ? WHERE id = ?', ('REFUNDED', payment_id))
    conn.commit()
    conn.close()
    
    # Update order status back to PENDING
    try:
        requests.put(
            f'{ORDER_SERVICE_URL}/orders/{order_id}/status',
            json={'status': 'CANCELLED'}
        )
    except:
        pass
    
    return jsonify({
        'message': 'Refund processed successfully',
        'payment_id': payment_id,
        'amount_refunded': amount,
        'status': 'REFUNDED'
    }), 200

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5004))
    app.run(host='0.0.0.0', port=port, debug=True)
