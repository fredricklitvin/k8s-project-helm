import os
from flask import Flask, jsonify, request
import psycopg2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database connection details
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'mysecretpassword')
DB_HOST = os.environ.get('DB_HOST', 'postgres-service') # Use the Kubernetes service name
DB_NAME = os.environ.get('DB_NAME', 'postgres')
DB_PORT = os.environ.get('DB_PORT', '5432')

# Function to create the 'names' table if it doesn't exist
def setup_database():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS names (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Database setup complete.")
    except Exception as e:
        print(f"Error setting up database: {e}")

# Call the setup function when the application starts
setup_database()

@app.route('/')
def home():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()[0]
        cur.close()
        conn.close()
        return jsonify({"status": "success", "message": "Backend is running and connected to the database!", "db_version": db_version})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/names', methods=['GET'])
def list_names():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("SELECT name FROM names;")
        names = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"names": names})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/add_name', methods=['POST'])
def add_name():
    try:
        data = request.get_json()
        new_name = data.get('name')
        if not new_name:
            return jsonify({"status": "error", "message": "Name is required"}), 400

        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("INSERT INTO names (name) VALUES (%s);", (new_name,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success", "message": f"Name '{new_name}' added successfully."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # When running in Kubernetes, the host is the service name
    # The port is the container port as defined in the deployment.
    app.run(host='0.0.0.0', port=5000)
####test9

