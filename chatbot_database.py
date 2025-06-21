import sqlite3

# Connect to the database (creates the file if it doesn't exist)
conn = sqlite3.connect("chat_history.db")
cursor = conn.cursor()

# Create a table for storing chat messages with a timestamp
cursor.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    chat_id TEXT,
    role TEXT,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Add a timestamp column if it doesn't already exist
try:
    cursor.execute("""
    ALTER TABLE conversations ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    """)
    conn.commit()
    print("Timestamp column added successfully!")
except sqlite3.OperationalError:
    # Ignore the error if the column already exists
    print("Timestamp column already exists.")

# Verify the schema of the conversations table
cursor.execute("PRAGMA table_info(conversations)")
columns = cursor.fetchall()
print("Table schema:")
for column in columns:
    print(column)

# Commit and close connection
conn.commit()
conn.close()

print("Database and table created successfully!")