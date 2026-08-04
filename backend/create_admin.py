from db import users
from werkzeug.security import generate_password_hash

# Default Admin User
admin_user = {
    "username": "admin",
    "password": generate_password_hash("Admin@123"),
    "role": "Admin",
    "name": "System Administrator",
    "email": "admin@frauddesk.com",
    "status": "Active"
}

# Check if admin already exists
existing = users.find_one({"username": "admin"})

if existing:
    print("⚠️ Admin user already exists.")
else:
    users.insert_one(admin_user)
    print("✅ Admin user created successfully!")
    print("Username : admin")
    print("Password : Admin@123")