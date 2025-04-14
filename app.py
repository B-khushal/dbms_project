from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL, MySQLdb
import re
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)

# Secret key for session
app.secret_key = 'bkpflorist123'

# Set up upload folder for product images
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'khushal893'
app.config['MYSQL_DB'] = 'bkp_florist'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialize MySQL
mysql = MySQL(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home page route
@app.route('/')
def home():
    # Get featured products
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT p.*, c.name as category_name, pi.image_url FROM products p LEFT JOIN categories c ON p.category_id = c.id LEFT JOIN product_images pi ON p.id = pi.product_id WHERE p.is_featured = 1 AND p.is_active = 1 GROUP BY p.id, p.name, p.sku, p.price, p.category_id, p.description, p.short_description, p.is_featured, p.is_active, p.in_stock, p.created_at, p.updated_at, c.name, pi.image_url ORDER BY p.created_at DESC LIMIT 8')
    featured_products = cursor.fetchall()
    
    # Get categories
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()
    
    return render_template('index.html', featured_products=featured_products, categories=categories)

# Products page route
@app.route('/products')
def products():
    category_id = request.args.get('category', None)
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get all categories for filter
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()
    
    # Get products with filters if applied
    if category_id:
        cursor.execute('''
            SELECT p.*, c.name as category_name, MIN(pi.image_url) as image_url 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            LEFT JOIN product_images pi ON p.id = pi.product_id 
            WHERE p.is_active = 1 AND p.category_id = %s
            GROUP BY p.id, p.name, p.sku, p.price, p.category_id, p.description, p.short_description, p.is_featured, p.is_active, p.in_stock, p.created_at, p.updated_at, c.name
            ORDER BY p.created_at DESC
        ''', (category_id,))
    else:
        cursor.execute('''
            SELECT p.*, c.name as category_name, MIN(pi.image_url) as image_url 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            LEFT JOIN product_images pi ON p.id = pi.product_id 
            WHERE p.is_active = 1
            GROUP BY p.id, p.name, p.sku, p.price, p.category_id, p.description, p.short_description, p.is_featured, p.is_active, p.in_stock, p.created_at, p.updated_at, c.name
            ORDER BY p.created_at DESC
        ''')
    
    products = cursor.fetchall()
    
    return render_template('products.html', products=products, categories=categories, selected_category=category_id)

# Product detail page
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get product details
    cursor.execute('''
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.id = %s AND p.is_active = 1
    ''', (product_id,))
    product = cursor.fetchone()
    
    if not product:
        flash('Product not found!')
        return redirect(url_for('products'))
    
    # Get product images
    cursor.execute('SELECT * FROM product_images WHERE product_id = %s ORDER BY sort_order', (product_id,))
    product_images = cursor.fetchall()
    
    # Get related products from same category
    cursor.execute('''
        SELECT p.*, MIN(pi.image_url) as image_url 
        FROM products p 
        LEFT JOIN product_images pi ON p.id = pi.product_id 
        WHERE p.category_id = %s AND p.id != %s AND p.is_active = 1
        GROUP BY p.id, p.name, p.sku, p.price, p.category_id, p.description, p.short_description, p.is_featured, p.is_active, p.in_stock, p.created_at, p.updated_at
        LIMIT 4
    ''', (product['category_id'], product_id))
    related_products = cursor.fetchall()
    
    return render_template('product_detail.html', product=product, product_images=product_images, related_products=related_products)

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        
        # For admin@springblossoms.com with password admin123
        if user and user['email'] == 'admin@springblossoms.com' and password == 'admin123':
            session['loggedin'] = True
            session['id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            
            flash('Login successful!')
            return redirect(url_for('home'))
        # For other users, use regular password checking
        elif user and check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            
            flash('Login successful!')
            return redirect(url_for('home'))
        else:
            flash('Incorrect email/password!')
    
    return render_template('login.html')

# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        
        if user:
            flash('Account already exists with this email!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not password or len(password) < 6:
            flash('Password must be at least 6 characters long!')
        else:
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)', (name, email, hashed_password))
            mysql.connection.commit()
            flash('You have successfully registered! Please login.')
            return redirect(url_for('login'))
    
    return render_template('register.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('name', None)
    session.pop('email', None)
    session.pop('role', None)
    
    return redirect(url_for('home'))

# Cart page
@app.route('/cart')
def cart():
    if 'cart' not in session:
        session['cart'] = []
        
    cart_items = session['cart']
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    return render_template('cart.html', cart_items=cart_items, total=total)

# Add to cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = int(request.form['product_id'])
    quantity = int(request.form['quantity'])
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT p.*, MIN(pi.image_url) as image_url 
        FROM products p 
        LEFT JOIN product_images pi ON p.id = pi.product_id 
        WHERE p.id = %s GROUP BY p.id, p.name, p.sku, p.price, p.category_id, p.description, p.short_description, p.is_featured, p.is_active, p.in_stock, p.created_at, p.updated_at
    ''', (product_id,))
    product = cursor.fetchone()
    
    if not product:
        flash('Product not found!')
        return redirect(url_for('products'))
    
    if 'cart' not in session:
        session['cart'] = []
    
    cart = session['cart']
    
    # Check if product already in cart
    found = False
    for item in cart:
        if item['id'] == product_id:
            item['quantity'] += quantity
            found = True
            break
    
    if not found:
        cart.append({
            'id': product_id,
            'name': product['name'],
            'price': float(product['price']),
            'image_url': product['image_url'],
            'quantity': quantity
        })
    
    session['cart'] = cart
    flash('Product added to cart!')
    
    return redirect(url_for('cart'))

# Update cart
@app.route('/update_cart', methods=['POST'])
def update_cart():
    cart = session['cart']
    
    product_id = int(request.form['product_id'])
    quantity = int(request.form['quantity'])
    
    for item in cart:
        if item['id'] == product_id:
            if quantity > 0:
                item['quantity'] = quantity
            else:
                cart.remove(item)
            break
    
    session['cart'] = cart
    
    return redirect(url_for('cart'))

# Remove from cart
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session['cart']
    
    for item in cart:
        if item['id'] == product_id:
            cart.remove(item)
            break
    
    session['cart'] = cart
    
    return redirect(url_for('cart'))

# Checkout page
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'cart' not in session or len(session['cart']) == 0:
        flash('Your cart is empty!')
        return redirect(url_for('cart'))
    
    cart_items = session['cart']
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    shipping_cost = 10.00
    total = subtotal + shipping_cost
    
    if request.method == 'POST':
        # Process order
        customer_name = request.form['customer_name']
        customer_email = request.form['customer_email']
        customer_phone = request.form['customer_phone']
        
        shipping_address = {
            'address': request.form['shipping_address'],
            'city': request.form['shipping_city'],
            'state': request.form['shipping_state'],
            'postal_code': request.form['shipping_postal_code'],
            'country': request.form['shipping_country']
        }
        
        billing_address = {
            'address': request.form['billing_address'],
            'city': request.form['billing_city'],
            'state': request.form['billing_state'],
            'postal_code': request.form['billing_postal_code'],
            'country': request.form['billing_country']
        }
        
        payment_method = request.form['payment_method']
        
        user_id = session.get('id', None)
        promo_code = request.form.get('promo_code', None)
        
        # Insert order into database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            INSERT INTO orders 
            (user_id, customer_name, customer_email, customer_phone, shipping_address, billing_address, payment_method, subtotal, shipping_cost, total, promo_code) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            user_id, customer_name, customer_email, customer_phone,
            json.dumps(shipping_address), json.dumps(billing_address),
            payment_method, subtotal, shipping_cost, total, promo_code
        ))
        order_id = cursor.lastrowid
        
        # Insert order items
        for item in cart_items:
            cursor.execute('''
                INSERT INTO order_items 
                (order_id, product_id, quantity, price) 
                VALUES (%s, %s, %s, %s)
            ''', (
                order_id, item['id'], item['quantity'], item['price']
            ))
        
        mysql.connection.commit()
        
        # Clear cart
        session.pop('cart', None)
        
        flash('Your order has been placed successfully!')
        return render_template('order_confirmation.html', order_id=order_id)
    
    return render_template('checkout.html', cart_items=cart_items, subtotal=subtotal, shipping_cost=shipping_cost, total=total)

# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get recent orders
    cursor.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT 5')
    recent_orders = cursor.fetchall()
    
    # Get order count
    cursor.execute('SELECT COUNT(*) as count FROM orders')
    order_count = cursor.fetchone()['count']
    
    # Get product count
    cursor.execute('SELECT COUNT(*) as count FROM products')
    product_count = cursor.fetchone()['count']
    
    # Get user count
    cursor.execute('SELECT COUNT(*) as count FROM users')
    user_count = cursor.fetchone()['count']
    
    return render_template('admin/dashboard.html', 
                          recent_orders=recent_orders, 
                          order_count=order_count, 
                          product_count=product_count, 
                          user_count=user_count)

# Admin products
@app.route('/admin/products')
def admin_products():
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.created_at DESC
    ''')
    products = cursor.fetchall()
    
    # Get categories for filters and forms
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()
    
    return render_template('admin/products.html', products=products, categories=categories)

# Add product route
@app.route('/add_product', methods=['POST'])
def add_product():
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form.get('sku', '')
        price = float(request.form['price'])
        category_id = int(request.form['category_id'])
        short_description = request.form.get('short_description', '')
        description = request.form.get('description', '')
        
        # Handle checkbox values
        is_featured = 1 if 'is_featured' in request.form else 0
        is_active = 1 if 'is_active' in request.form else 0
        in_stock = 1 if 'in_stock' in request.form else 0
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            # Insert product
            cursor.execute('''
                INSERT INTO products 
                (name, sku, price, category_id, short_description, description, is_featured, is_active, in_stock) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (name, sku, price, category_id, short_description, description, is_featured, is_active, in_stock))
            
            product_id = cursor.lastrowid
            
            # Handle image uploads
            if 'images' in request.files:
                images = request.files.getlist('images')
                
                # Ensure uploads directory exists
                uploads_dir = os.path.join('static', 'uploads', 'products', str(product_id))
                os.makedirs(uploads_dir, exist_ok=True)
                
                # Save each uploaded image
                for i, image in enumerate(images):
                    if image and image.filename:
                        # Get file extension
                        _, ext = os.path.splitext(image.filename)
                        
                        # Create unique filename
                        filename = f"product_{product_id}_{i+1}{ext}"
                        filepath = os.path.join(uploads_dir, filename)
                        
                        # Save image
                        image.save(filepath)
                        
                        # Create relative path for database
                        db_filepath = f"/static/uploads/products/{product_id}/{filename}"
                        
                        # Save image in database
                        cursor.execute('''
                            INSERT INTO product_images 
                            (product_id, image_url, sort_order) 
                            VALUES (%s, %s, %s)
                        ''', (product_id, db_filepath, i+1))
            
            mysql.connection.commit()
            flash('Product added successfully!')
        except Exception as e:
            flash(f'Error adding product: {str(e)}')
            
    return redirect(url_for('admin_products'))

# Admin orders
@app.route('/admin/orders')
def admin_orders():
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    # Get status filter if any
    status_filter = request.args.get('status', None)
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get all orders with optional filter
    if status_filter:
        cursor.execute('''
            SELECT o.*, COUNT(oi.id) as item_count
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.status = %s
            GROUP BY o.id
            ORDER BY o.created_at DESC
        ''', (status_filter,))
    else:
        cursor.execute('''
            SELECT o.*, COUNT(oi.id) as item_count
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            GROUP BY o.id
            ORDER BY o.created_at DESC
        ''')
    
    orders = cursor.fetchall()
    
    # Count orders by status
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM orders
        GROUP BY status
    ''')
    status_counts = cursor.fetchall()
    
    # Convert to a more usable format
    status_summary = {
        'pending': 0,
        'processing': 0,
        'shipped': 0,
        'delivered': 0,
        'cancelled': 0,
        'total': 0
    }
    
    for count in status_counts:
        if count['status'] in status_summary:
            status_summary[count['status']] = count['count']
            status_summary['total'] += count['count']
    
    return render_template('admin/orders.html', 
                          orders=orders, 
                          status_summary=status_summary,
                          current_filter=status_filter)

# Admin order detail
@app.route('/admin/order/<int:order_id>')
def admin_order_detail(order_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get order details
    cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()
    
    if not order:
        flash('Order not found!')
        return redirect(url_for('admin_orders'))
    
    # Initialize address with default values in case shipping_address or billing_address are not present
    address = {
        'full_name': order['customer_name'],
        'phone': order.get('customer_phone', ''),
        'street': '',
        'city': '',
        'state': '',
        'zip_code': '',
        'country': ''
    }
    
    # Parse JSON address fields if present
    if order.get('shipping_address'):
        try:
            shipping_address = json.loads(order['shipping_address'])
            # Update address with shipping information
            address.update({
                'street': shipping_address.get('address', ''),
                'city': shipping_address.get('city', ''),
                'state': shipping_address.get('state', ''),
                'zip_code': shipping_address.get('postal_code', ''),
                'country': shipping_address.get('country', ''),
                'apartment': shipping_address.get('apartment', '')
            })
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Get order items with product details
    cursor.execute('''
        SELECT oi.*, p.name as product_name, p.price, 
               (SELECT pi.image_url FROM product_images pi WHERE pi.product_id = p.id LIMIT 1) as image_url
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = %s
    ''', (order_id,))
    order_items = cursor.fetchall()
    
    return render_template('admin/order_detail.html', order=order, address=address, order_items=order_items)

# Update order status
@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    new_status = request.form['status']
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE orders SET status = %s WHERE id = %s', (new_status, order_id))
    mysql.connection.commit()
    
    flash(f'Order status updated to {new_status}!', 'success')
    return redirect(url_for('admin_order_detail', order_id=order_id))

# Admin customers
@app.route('/admin/customers')
def admin_customers():
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get all users
    cursor.execute('''
        SELECT u.*, COUNT(o.id) as order_count, SUM(o.total) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ''')
    customers = cursor.fetchall()
    
    return render_template('admin/customers.html', customers=customers)

# Edit product route
@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get product details
    cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cursor.fetchone()
    
    if not product:
        flash('Product not found!')
        return redirect(url_for('admin_products'))
    
    # Get product images
    cursor.execute('SELECT * FROM product_images WHERE product_id = %s ORDER BY sort_order', (product_id,))
    product_images = cursor.fetchall()
    
    # Get categories for dropdown
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()
    
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form.get('sku', '')
        price = float(request.form['price'])
        category_id = int(request.form['category_id'])
        short_description = request.form.get('short_description', '')
        description = request.form.get('description', '')
        
        # Handle checkbox values
        is_featured = 1 if 'is_featured' in request.form else 0
        is_active = 1 if 'is_active' in request.form else 0
        in_stock = 1 if 'in_stock' in request.form else 0
        
        try:
            # Update product
            cursor.execute('''
                UPDATE products 
                SET name = %s, sku = %s, price = %s, category_id = %s, 
                    short_description = %s, description = %s, 
                    is_featured = %s, is_active = %s, in_stock = %s
                WHERE id = %s
            ''', (name, sku, price, category_id, short_description, description, 
                  is_featured, is_active, in_stock, product_id))
            
            # Handle image uploads
            if 'images' in request.files:
                images = request.files.getlist('images')
                
                # Ensure uploads directory exists
                uploads_dir = os.path.join('static', 'uploads', 'products', str(product_id))
                os.makedirs(uploads_dir, exist_ok=True)
                
                # Save each uploaded image
                for i, image in enumerate(images):
                    if image and image.filename:
                        # Get file extension
                        _, ext = os.path.splitext(image.filename)
                        
                        # Create unique filename
                        filename = f"product_{product_id}_{i+1}{ext}"
                        filepath = os.path.join(uploads_dir, filename)
                        
                        # Save image
                        image.save(filepath)
                        
                        # Create relative path for database
                        db_filepath = f"/static/uploads/products/{product_id}/{filename}"
                        
                        # Save image in database
                        cursor.execute('''
                            INSERT INTO product_images 
                            (product_id, image_url, sort_order) 
                            VALUES (%s, %s, %s)
                        ''', (product_id, db_filepath, i+1))
            
            # Handle image deletions
            if 'delete_images' in request.form:
                delete_image_ids = request.form.getlist('delete_images')
                for image_id in delete_image_ids:
                    cursor.execute('SELECT image_url FROM product_images WHERE id = %s', (image_id,))
                    image = cursor.fetchone()
                    if image:
                        # Delete the file if it exists
                        file_path = os.path.join(os.getcwd(), image['image_url'].lstrip('/'))
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        
                        # Delete from database
                        cursor.execute('DELETE FROM product_images WHERE id = %s', (image_id,))
            
            mysql.connection.commit()
            flash('Product updated successfully!')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash(f'Error updating product: {str(e)}')
    
    return render_template('admin/edit_product.html', product=product, product_images=product_images, categories=categories)

# Delete product route
@app.route('/admin/delete_product/<int:product_id>')
def delete_product(product_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # First, delete any associated images
    cursor.execute('DELETE FROM product_images WHERE product_id = %s', (product_id,))
    
    # Then delete the product
    cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
    
    mysql.connection.commit()
    
    flash('Product deleted successfully!')
    return redirect(url_for('admin_products'))

# View customer details
@app.route('/admin/customer/<int:customer_id>')
def admin_view_customer(customer_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get customer details
    cursor.execute('SELECT * FROM users WHERE id = %s', (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        flash('Customer not found!')
        return redirect(url_for('admin_customers'))
    
    # Get customer orders
    cursor.execute('SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC', (customer_id,))
    orders = cursor.fetchall()
    
    return render_template('admin/customer_detail.html', customer=customer, orders=orders)

# Edit customer route
@app.route('/admin/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
def admin_edit_customer(customer_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get customer details
    cursor.execute('SELECT * FROM users WHERE id = %s', (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        flash('Customer not found!')
        return redirect(url_for('admin_customers'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']
        
        # Check if email exists for other user
        cursor.execute('SELECT * FROM users WHERE email = %s AND id != %s', (email, customer_id))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Email already exists for another user!')
        else:
            # Update user info
            cursor.execute('UPDATE users SET name = %s, email = %s, role = %s WHERE id = %s', 
                          (name, email, role, customer_id))
            
            # Update password if provided
            if 'password' in request.form and request.form['password'].strip():
                password = request.form['password']
                if len(password) < 6:
                    flash('Password must be at least 6 characters long!')
                else:
                    hashed_password = generate_password_hash(password)
                    cursor.execute('UPDATE users SET password = %s WHERE id = %s', 
                                 (hashed_password, customer_id))
            
            mysql.connection.commit()
            flash('Customer updated successfully!')
            return redirect(url_for('admin_customers'))
    
    return render_template('admin/edit_customer.html', customer=customer)

# Delete customer route
@app.route('/admin/delete_customer/<int:customer_id>')
def admin_delete_customer(customer_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Check if customer exists
    cursor.execute('SELECT * FROM users WHERE id = %s', (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        flash('Customer not found!')
        return redirect(url_for('admin_customers'))
    
    # Delete user
    cursor.execute('DELETE FROM users WHERE id = %s', (customer_id,))
    mysql.connection.commit()
    
    flash('Customer deleted successfully!')
    return redirect(url_for('admin_customers'))

# Admin categories
@app.route('/admin/categories')
def admin_categories():
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get categories with product counts
    cursor.execute('''
        SELECT c.*, COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id
        GROUP BY c.id
        ORDER BY c.name
    ''')
    categories = cursor.fetchall()
    
    return render_template('admin/categories.html', categories=categories)

# Add category route
@app.route('/admin/add_category', methods=['POST'])
def add_category():
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    name = request.form['name']
    slug = request.form.get('slug', '').lower().replace(' ', '-')
    description = request.form.get('description', '')
    
    # If no slug is provided, generate one from the name
    if not slug:
        slug = name.lower().replace(' ', '-')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Check if slug already exists
    cursor.execute('SELECT * FROM categories WHERE slug = %s', (slug,))
    existing_category = cursor.fetchone()
    
    if existing_category:
        flash('A category with this slug already exists!')
    else:
        try:
            # Insert category
            cursor.execute(
                'INSERT INTO categories (name, slug, description) VALUES (%s, %s, %s)',
                (name, slug, description)
            )
            category_id = cursor.lastrowid
            
            # Handle image upload
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename:
                    # Create directory if it doesn't exist
                    uploads_dir = os.path.join('static', 'images', 'categories')
                    os.makedirs(uploads_dir, exist_ok=True)
                    
                    # Get file extension
                    _, ext = os.path.splitext(image.filename)
                    
                    # Create filename
                    filename = f"category_{category_id}{ext}"
                    filepath = os.path.join(uploads_dir, filename)
                    
                    # Save image
                    image.save(filepath)
                    
                    # Save image path to database
                    cursor.execute(
                        'UPDATE categories SET image_url = %s WHERE id = %s',
                        (f"/static/images/categories/{filename}", category_id)
                    )
            
            mysql.connection.commit()
            flash('Category added successfully!')
        except Exception as e:
            flash(f'Error adding category: {str(e)}')
    
    return redirect(url_for('admin_categories'))

# Edit category route
@app.route('/admin/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get category details
    cursor.execute('SELECT * FROM categories WHERE id = %s', (category_id,))
    category = cursor.fetchone()
    
    if not category:
        flash('Category not found!')
        return redirect(url_for('admin_categories'))
    
    # Get product count for this category
    cursor.execute('SELECT COUNT(*) as count FROM products WHERE category_id = %s', (category_id,))
    product_count = cursor.fetchone()['count']
    category['product_count'] = product_count
    
    if request.method == 'POST':
        name = request.form['name']
        slug = request.form.get('slug', '').lower().replace(' ', '-')
        description = request.form.get('description', '')
        
        # If no slug is provided, generate one from the name
        if not slug:
            slug = name.lower().replace(' ', '-')
        
        # Check if slug already exists for another category
        cursor.execute('SELECT * FROM categories WHERE slug = %s AND id != %s', (slug, category_id))
        existing_category = cursor.fetchone()
        
        if existing_category:
            flash('A category with this slug already exists!')
        else:
            try:
                cursor.execute(
                    'UPDATE categories SET name = %s, slug = %s, description = %s WHERE id = %s',
                    (name, slug, description, category_id)
                )
                
                # Handle image upload
                if 'image' in request.files:
                    image = request.files['image']
                    if image and image.filename:
                        # Create directory if it doesn't exist
                        uploads_dir = os.path.join('static', 'images', 'categories')
                        os.makedirs(uploads_dir, exist_ok=True)
                        
                        # Delete old image if exists
                        if category.get('image_url'):
                            old_image_path = os.path.join(os.getcwd(), category['image_url'].lstrip('/'))
                            if os.path.exists(old_image_path):
                                os.remove(old_image_path)
                        
                        # Get file extension
                        _, ext = os.path.splitext(image.filename)
                        
                        # Create filename
                        filename = f"category_{category_id}{ext}"
                        filepath = os.path.join(uploads_dir, filename)
                        
                        # Save image
                        image.save(filepath)
                        
                        # Save image path to database
                        cursor.execute(
                            'UPDATE categories SET image_url = %s WHERE id = %s',
                            (f"/static/images/categories/{filename}", category_id)
                        )
                
                mysql.connection.commit()
                flash('Category updated successfully!')
                return redirect(url_for('admin_categories'))
            except Exception as e:
                flash(f'Error updating category: {str(e)}')
    
    return render_template('admin/edit_category.html', category=category)

# Delete category route
@app.route('/admin/delete_category/<int:category_id>')
def delete_category(category_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('You need to be logged in as admin to access this page!')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Check if category exists
    cursor.execute('SELECT * FROM categories WHERE id = %s', (category_id,))
    category = cursor.fetchone()
    
    if not category:
        flash('Category not found!')
        return redirect(url_for('admin_categories'))
    
    # Check if category has products
    cursor.execute('SELECT COUNT(*) as count FROM products WHERE category_id = %s', (category_id,))
    product_count = cursor.fetchone()['count']
    
    if product_count > 0:
        flash('Cannot delete category with associated products!')
        return redirect(url_for('admin_categories'))
    
    try:
        cursor.execute('DELETE FROM categories WHERE id = %s', (category_id,))
        mysql.connection.commit()
        flash('Category deleted successfully!')
    except Exception as e:
        flash(f'Error deleting category: {str(e)}')
    
    return redirect(url_for('admin_categories'))

# About page
@app.route('/about')
def about():
    return render_template('about.html')

# Contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Account page
@app.route('/account')
def account():
    # Check if user is logged in
    if 'loggedin' not in session:
        flash('Please login to access your account')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get user details
    cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
    user = cursor.fetchone()
    
    # Get user orders
    cursor.execute('''
        SELECT * FROM orders 
        WHERE user_id = %s 
        ORDER BY created_at DESC
    ''', (session['id'],))
    orders = cursor.fetchall()
    
    return render_template('account.html', user=user, orders=orders)

# Edit profile route
@app.route('/account/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'loggedin' not in session:
        flash('Please login to access your account')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get user details
    cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
    user = cursor.fetchone()
    
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        
        try:
            # Update user details - only name, not email
            cursor.execute('UPDATE users SET name = %s WHERE id = %s', 
                         (name, session['id']))
            
            # Change password if provided
            if 'password' in request.form and request.form['password'].strip():
                password = request.form['password']
                confirm_password = request.form.get('confirm_password', '')
                
                if password != confirm_password:
                    flash('Passwords do not match!')
                elif len(password) < 6:
                    flash('Password must be at least 6 characters long!')
                else:
                    hashed_password = generate_password_hash(password)
                    cursor.execute('UPDATE users SET password = %s WHERE id = %s', 
                                 (hashed_password, session['id']))
            
            mysql.connection.commit()
            
            # Update session name
            session['name'] = name
            
            flash('Profile updated successfully!')
            return redirect(url_for('account'))
        except Exception as e:
            flash(f'Error updating profile: {str(e)}')
    
    return render_template('edit_profile.html', user=user)

# View order details
@app.route('/account/order/<int:order_id>')
def view_order(order_id):
    if 'loggedin' not in session:
        flash('Please login to access your account')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get order details
    cursor.execute('SELECT * FROM orders WHERE id = %s AND user_id = %s', (order_id, session['id']))
    order = cursor.fetchone()
    
    if not order:
        flash('Order not found!')
        return redirect(url_for('account'))
    
    # Parse JSON address fields if present
    address = {
        'full_name': order['customer_name'],
        'phone': order.get('customer_phone', ''),
        'street': '',
        'city': '',
        'state': '',
        'zip_code': '',
        'country': ''
    }
    
    if order.get('shipping_address'):
        try:
            shipping_address = json.loads(order['shipping_address'])
            # Update address with shipping information
            address.update({
                'street': shipping_address.get('address', ''),
                'city': shipping_address.get('city', ''),
                'state': shipping_address.get('state', ''),
                'zip_code': shipping_address.get('postal_code', ''),
                'country': shipping_address.get('country', ''),
                'apartment': shipping_address.get('apartment', '')
            })
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Get order items with product details
    cursor.execute('''
        SELECT oi.*, p.name as product_name, p.price, 
               (SELECT pi.image_url FROM product_images pi WHERE pi.product_id = p.id LIMIT 1) as image_url
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = %s
    ''', (order_id,))
    order_items = cursor.fetchall()
    
    return render_template('view_order.html', order=order, address=address, order_items=order_items)

if __name__ == '__main__':
    app.run(debug=True) 