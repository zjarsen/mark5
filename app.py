from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
DB_PATH = 'patient_bp.db'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'bp_windowed_view.html')

@app.route('/edit')
def edit():
    return send_from_directory(BASE_DIR, 'edit_data.html')

@app.route('/api/data/all', methods=['GET'])
def get_all_data():
    """Get all BP readings and medications"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch all BP readings
    cursor.execute('''
        SELECT datetime, systolic_bp, diastolic_bp, heart_rate
        FROM blood_pressure_readings
        ORDER BY datetime
    ''')
    bp_records = cursor.fetchall()

    # Fetch all medications
    cursor.execute('''
        SELECT datetime, medication_name, dosage
        FROM medications
        ORDER BY datetime
    ''')
    med_records = cursor.fetchall()

    conn.close()

    return jsonify({
        'bp_readings': bp_records,
        'medications': med_records
    })

@app.route('/api/data/<date>', methods=['GET'])
def get_data(date):
    """Get all records for a specific date"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch BP readings
    cursor.execute('''
        SELECT datetime, systolic_bp, diastolic_bp, heart_rate
        FROM blood_pressure_readings
        WHERE date(datetime) = ?
        ORDER BY datetime
    ''', (date,))
    bp_records = cursor.fetchall()

    # Fetch medications
    cursor.execute('''
        SELECT datetime, medication_name, dosage
        FROM medications
        WHERE date(datetime) = ?
        ORDER BY datetime
    ''', (date,))
    med_records = cursor.fetchall()

    conn.close()

    return jsonify({
        'bp_readings': bp_records,
        'medications': med_records
    })

@app.route('/api/data/<date>', methods=['POST'])
def save_data(date):
    """Save/update records for a specific date"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Delete existing records for this date
    cursor.execute('DELETE FROM blood_pressure_readings WHERE date(datetime) = ?', (date,))
    cursor.execute('DELETE FROM medications WHERE date(datetime) = ?', (date,))

    # Insert new BP readings
    for record in data.get('bp_readings', []):
        # Only insert if at least one field is not null
        if record.get('systolic') or record.get('diastolic') or record.get('heart_rate'):
            cursor.execute('''
                INSERT INTO blood_pressure_readings (datetime, systolic_bp, diastolic_bp, heart_rate)
                VALUES (?, ?, ?, ?)
            ''', (
                record['datetime'],
                record.get('systolic') or None,
                record.get('diastolic') or None,
                record.get('heart_rate') or None
            ))

    # Insert new medications
    for record in data.get('medications', []):
        if record.get('dosage'):  # Only insert if dosage is provided
            cursor.execute('''
                INSERT INTO medications (datetime, medication_name, dosage)
                VALUES (?, ?, ?)
            ''', (record['datetime'], record['medication'], record['dosage']))

    conn.commit()
    conn.close()

    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
