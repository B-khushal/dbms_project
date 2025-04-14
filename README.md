# BKP Florist E-commerce Website

A feature-rich e-commerce website for BKP Florist built using Flask and MySQL. This application allows customers to browse and purchase floral arrangements online and provides an admin dashboard for managing products, orders, and users.

## Features

### Customer Features
- Browse products by category
- Product search and filtering
- User registration and login
- Shopping cart functionality
- Checkout process
- Order history

### Admin Features
- Dashboard with sales overview
- Product management (add, edit, delete)
- Order management
- User management
- Category management
- Promo code management

## Technologies Used

- **Backend**: Python, Flask
- **Database**: MySQL
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Authentication**: Flask session management
- **Payment Processing**: Simulated (not actual payment gateway)

## Setup Instructions

### Prerequisites
- Python 3.8+
- MySQL Server
- pip (Python package manager)

### Database Setup
1. Install MySQL if not already installed.
2. Create a database and import the schema:
   ```sql
   CREATE DATABASE sbdb;
   USE sbdb;
   
   -- Run the SQL schema provided in the project
   ```

### Application Setup
1. Clone the repository:
   ```
   git clone <repository-url>
   cd bkp-florist
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure the database connection in `app.py`:
   ```python
   app.config['MYSQL_HOST'] = 'localhost'
   app.config['MYSQL_USER'] = 'your_mysql_username'
   app.config['MYSQL_PASSWORD'] = 'your_mysql_password'
   app.config['MYSQL_DB'] = 'sbdb'
   ```

5. Run the application:
   ```
   python app.py
   ```

6. Access the website at `http://localhost:5000`

## Default Admin Access

A default admin user is created during database initialization:
- Email: admin@springblossoms.com
- Password: admin123

## Project Structure

```
bkp-florist/
│
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── templates/              # HTML templates
│   ├── layout.html         # Base template
│   ├── index.html          # Homepage
│   ├── products.html       # Products page
│   ├── product_detail.html # Product detail page
│   ├── cart.html           # Shopping cart
│   ├── checkout.html       # Checkout page
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── admin/              # Admin templates
│       ├── dashboard.html  # Admin dashboard
│       └── products.html   # Product management
└── static/                 # Static files (CSS, JS, images)
```

## License

[MIT License](LICENSE) 