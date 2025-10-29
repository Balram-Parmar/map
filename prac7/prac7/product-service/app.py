from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

DB_PATH = 'products.db'

def init_db():
    """Initialize the database with sample products"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    
    # Check if table is empty and add sample data
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ('Laptop', 'High-performance laptop', 999.99, 10),
            ('Smartphone', 'Latest smartphone model', 699.99, 25),
            ('Headphones', 'Wireless noise-cancelling headphones', 199.99, 50),
            ('Tablet', '10-inch tablet with stylus', 449.99, 15),
            ('Smart Watch', 'Fitness tracking smartwatch', 299.99, 30)
        ]
        cursor.executemany(
            'INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)',
            sample_products
        )
    
    conn.commit()
    conn.close()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'product-service'}), 200

@app.route('/products', methods=['GET'])
def get_products():
    """Get all products"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, price, stock FROM products')
    products = []
    for row in cursor.fetchall():
        products.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'price': row[3],
            'stock': row[4]
        })
    conn.close()
    return jsonify(products), 200

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, price, stock FROM products WHERE id = ?', (product_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        product = {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'price': row[3],
            'stock': row[4]
        }
        return jsonify(product), 200
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/products', methods=['POST'])
def create_product():
    """Create a new product"""
    data = request.get_json()
    
    if not all(k in data for k in ('name', 'price', 'stock')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)',
        (data['name'], data.get('description', ''), data['price'], data['stock'])
    )
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': product_id, 'message': 'Product created successfully'}), 201

@app.route('/products/<int:product_id>/stock', methods=['PUT'])
def update_stock(product_id):
    """Update product stock (used by Order Service)"""
    data = request.get_json()
    
    if 'quantity' not in data:
        return jsonify({'error': 'Missing quantity field'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check current stock
    cursor.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404
    
    current_stock = row[0]
    new_stock = current_stock - data['quantity']
    
    if new_stock < 0:
        conn.close()
        return jsonify({'error': 'Insufficient stock', 'available': current_stock}), 400
    
    cursor.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product_id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Stock updated successfully', 'new_stock': new_stock}), 200

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
