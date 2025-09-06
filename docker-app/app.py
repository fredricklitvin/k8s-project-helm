import os
from flask import Flask, jsonify, request
import psycopg2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database connection details
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
# This must come from the environment variable set by the configmap
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_PORT = os.environ.get('DB_PORT')

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
    )

# Create the 'names' table if it doesn't exist
def setup_database():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.names (
                    id   SERIAL PRIMARY KEY,
                    name TEXT NOT NULL
                );
            """)
        conn.commit()
    print("Database setup complete.")

@app.before_request
def init_once():
    # Runs once per process (e.g., once per Gunicorn worker)
    try:
        # Basic sanity check for missing env vars
        missing = [k for k, v in {
            "POSTGRES_USER": DB_USER,
            "POSTGRES_PASSWORD": DB_PASSWORD,
            "DB_HOST": DB_HOST,
            "POSTGRES_DB": DB_NAME,
            "DB_PORT": DB_PORT,
        }.items() if not v]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

        setup_database()
    except Exception as e:
        # If startup init fails, log it clearly. Requests will still return JSON errors.
        print(f"Startup DB init failed: {e}")

@app.route('/')
def home():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                db_version = cur.fetchone()[0]
        return jsonify({"status": "success",
                        "message": "Backend is running and connected to the database!",
                        "db_version": db_version})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/names', methods=['GET'])
def list_names():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM public.names;")
                names = [row[0] for row in cur.fetchall()]
        return jsonify({"names": names})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/add_name', methods=['POST'])
def add_name():
    try:
        data = request.get_json(force=True, silent=False)
        new_name = (data or {}).get('name')
        if not new_name:
            return jsonify({"status": "error", "message": "Name is required"}), 400

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO public.names (name) VALUES (%s);", (new_name,))
            conn.commit()
        return jsonify({"status": "success", "message": f"Name '{new_name}' added successfully."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)