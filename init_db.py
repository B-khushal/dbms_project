import mysql.connector
from mysql.connector import Error
import os

def init_database():
    try:
        # Connect to MySQL server without specifying a database
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="khushal893"  # Use your actual MySQL root password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS spring_blossoms")
            cursor.execute("USE spring_blossoms")
            
            print("Connected to MySQL, creating tables...")
            
            # Read SQL script
            with open('database.sql', 'r') as sql_file:
                sql_script = sql_file.read()
            
            # Split SQL script into individual commands
            sql_commands = sql_script.split(';')
            
            # Execute each command
            for command in sql_commands:
                if command.strip():
                    # Skip the database creation/use commands as we've already done them
                    # Also skip the INSERT commands for users and categories as we'll handle them separately
                    if (not command.strip().startswith('CREATE DATABASE') and 
                        not command.strip().startswith('USE') and
                        not command.strip().startswith('INSERT INTO users') and
                        not command.strip().startswith('INSERT INTO categories')):
                        try:
                            cursor.execute(command)
                        except Error as e:
                            print(f"Error executing command: {e}")
                            print(f"Command: {command}")
            
            # Handle admin user separately
            try:
                # First check if admin user already exists
                cursor.execute("SELECT * FROM users WHERE email = 'admin@springblossoms.com'")
                admin_exists = cursor.fetchone()
                
                if not admin_exists:
                    # Add admin user
                    cursor.execute("""
                        INSERT INTO users (name, email, password, role) VALUES 
                        ('Admin User', 'admin@springblossoms.com', '$2y$12$9qwnm4lMZVK0GFXJxAdSzOYiJBLqNCrOCLGHRbvOXZt.sI0g7VeQ.', 'admin')
                    """)
                    print("Added admin user")
            except Error as e:
                print(f"Error adding admin user: {e}")
            
            # Handle categories separately
            categories = [
                ('Birthday', 'birthday', 'Beautiful flower arrangements for birthdays'),
                ('Anniversary', 'anniversary', 'Celebrate your special day with our anniversary flowers'),
                ('Sympathy', 'sympathy', 'Express your condolences with our sympathy arrangements'),
                ('Get Well', 'get-well', 'Brighten someone\'s day with our get well flowers'),
                ('Congratulations', 'congratulations', 'Say congratulations with our special arrangements'),
                ('Just Because', 'just-because', 'Send flowers just because'),
                ('Seasonal', 'seasonal', 'Seasonal flower arrangements')
            ]
            
            for category in categories:
                try:
                    # Check if category exists
                    cursor.execute(f"SELECT * FROM categories WHERE slug = '{category[1]}'")
                    category_exists = cursor.fetchone()
                    
                    if not category_exists:
                        cursor.execute("""
                            INSERT INTO categories (name, slug, description) VALUES
                            (%s, %s, %s)
                        """, category)
                        print(f"Added category: {category[0]}")
                except Error as e:
                    print(f"Error adding category {category[0]}: {e}")
            
            # Add sample product for each category
            for i, category in enumerate(categories, start=1):
                try:
                    # Check if sample product already exists
                    cursor.execute(f"SELECT * FROM products WHERE name = 'Sample {category[0]} Arrangement'")
                    product_exists = cursor.fetchone()
                    
                    if not product_exists:
                        # Get the category ID
                        cursor.execute(f"SELECT id FROM categories WHERE slug = '{category[1]}'")
                        category_id = cursor.fetchone()
                        if category_id:
                            # Add product
                            cursor.execute("""
                                INSERT INTO products (name, sku, price, category_id, description, short_description, is_featured, is_active, in_stock)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                f"Sample {category[0]} Arrangement",
                                f"SKU-{i:03d}",
                                49.99 + (i * 5),
                                category_id[0],
                                f"This is a beautiful {category[0].lower()} flower arrangement perfect for any occasion.",
                                f"Beautiful {category[0].lower()} arrangement",
                                1 if i <= 4 else 0,  # Feature first 4 products
                                1,
                                1
                            ))
                            
                            # Get the product ID
                            product_id = cursor.lastrowid
                            
                            # Add product image
                            cursor.execute("""
                                INSERT INTO product_images (product_id, image_url, sort_order)
                                VALUES (%s, %s, %s)
                            """, (
                                product_id,
                                f"https://source.unsplash.com/400x300/?flowers,{category[1]}",
                                1
                            ))
                            print(f"Added sample product for category: {category[0]}")
                except Error as e:
                    print(f"Error adding sample product for {category[0]}: {e}")
            
            connection.commit()
            print("Database initialized successfully!")
            
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")

if __name__ == "__main__":
    init_database() 