import mysql.connector as mc

db = mc.connect(
    host="127.0.0.1",
    user="root",
    password="Y@shpal123",
    database="business_db",
    port=3306
)
print("✅ Database connected successfully")

