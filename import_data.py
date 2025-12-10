import pandas as pd
import sqlite3
from datetime import datetime, time

# Read the Excel file
df = pd.read_excel('source.xlsx')

# Create SQLite database connection
conn = sqlite3.connect('patient_bp.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS blood_pressure_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    heart_rate INTEGER,
    UNIQUE(datetime)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL,
    medication_name TEXT NOT NULL,
    dosage REAL
)
''')

# Parse the data
# First row contains the metric names
metric_row = df.iloc[0]

# Get column names (dates)
columns = df.columns.tolist()

# Time column is the first one
time_column = columns[0]

# Process data
for row_idx in range(1, len(df)):
    time_str = str(df.iloc[row_idx, 0])

    # Skip if time is NaN
    if pd.isna(df.iloc[row_idx, 0]):
        continue

    # Process each date
    for col_idx in range(1, len(columns), 6):  # Step by 6 (6 metrics per date)
        # Get the base date
        base_date = columns[col_idx]

        # Convert to date string
        if isinstance(base_date, datetime):
            date_str = base_date.strftime('%Y-%m-%d')
        else:
            date_str = str(base_date).split()[0]

        # Combine date and time
        datetime_str = f"{date_str} {time_str}"

        # Get values for this datetime
        systolic = df.iloc[row_idx, col_idx]
        diastolic = df.iloc[row_idx, col_idx + 1]
        heart_rate = df.iloc[row_idx, col_idx + 2]
        med1 = df.iloc[row_idx, col_idx + 3]  # 坎地沙坦 (Candesartan)
        med2 = df.iloc[row_idx, col_idx + 4]  # 乐卡地平 (Lercanidipine)
        med3 = df.iloc[row_idx, col_idx + 5]  # 美托洛尔 (Metoprolol)

        # Insert blood pressure reading if any value exists
        if not all(pd.isna([systolic, diastolic, heart_rate])):
            systolic_val = None if pd.isna(systolic) else int(systolic)
            diastolic_val = None if pd.isna(diastolic) else int(diastolic)
            heart_rate_val = None if pd.isna(heart_rate) else int(heart_rate)

            cursor.execute('''
                INSERT OR IGNORE INTO blood_pressure_readings
                (datetime, systolic_bp, diastolic_bp, heart_rate)
                VALUES (?, ?, ?, ?)
            ''', (datetime_str, systolic_val, diastolic_val, heart_rate_val))

        # Insert medication records
        if not pd.isna(med1):
            cursor.execute('''
                INSERT INTO medications (datetime, medication_name, dosage)
                VALUES (?, ?, ?)
            ''', (datetime_str, '坎地沙坦 (Candesartan)', float(med1)))

        if not pd.isna(med2):
            cursor.execute('''
                INSERT INTO medications (datetime, medication_name, dosage)
                VALUES (?, ?, ?)
            ''', (datetime_str, '乐卡地平 (Lercanidipine)', float(med2)))

        if not pd.isna(med3):
            cursor.execute('''
                INSERT INTO medications (datetime, medication_name, dosage)
                VALUES (?, ?, ?)
            ''', (datetime_str, '美托洛尔 (Metoprolol)', float(med3)))

# Commit and close
conn.commit()

# Print summary statistics
cursor.execute('SELECT COUNT(*) FROM blood_pressure_readings')
bp_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM medications')
med_count = cursor.fetchone()[0]

cursor.execute('SELECT medication_name, COUNT(*) FROM medications GROUP BY medication_name')
med_breakdown = cursor.fetchall()

print(f"✓ Database created: patient_bp.db")
print(f"✓ Blood pressure readings imported: {bp_count}")
print(f"✓ Medication records imported: {med_count}")
print("\nMedication breakdown:")
for med_name, count in med_breakdown:
    print(f"  - {med_name}: {count} records")

# Show sample data
print("\n--- Sample Blood Pressure Readings ---")
cursor.execute('SELECT * FROM blood_pressure_readings LIMIT 5')
for row in cursor.fetchall():
    print(row)

print("\n--- Sample Medication Records ---")
cursor.execute('SELECT * FROM medications LIMIT 5')
for row in cursor.fetchall():
    print(row)

conn.close()
