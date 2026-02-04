
import sqlite3
import os
import datetime

def clean_database(db_path):
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables_to_check = [
        'lga',
        'ward',
        'polling_unit',
        'announced_lga_results',
        'announced_pu_results',
        'announced_state_results',
        'announced_ward_results'
    ]

    invalid_date = '0000-00-00 00:00:00'
    
    # Calculate valid default: Today minus 5 hours
    # Format: YYYY-MM-DD HH:MM:SS
    valid_default_dt = datetime.datetime.now() - datetime.timedelta(hours=5)
    valid_default = valid_default_dt.strftime('%Y-%m-%d %H:%M:%S')
    print(f"Using replacement date: {valid_default}")

    for table in tables_to_check:
        try:
            print(f"Checking table: {table}...")
            
            # Count invalid dates
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE date_entered = ?", (invalid_date,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"  Found {count} invalid dates in '{table}'. fixing...")
                # Update to a valid default date because of NOT NULL constraint
                cursor.execute(f"UPDATE {table} SET date_entered = ? WHERE date_entered = ?", (valid_default, invalid_date))
                print(f"  Fixed.")
            else:
                print(f"  No invalid dates found.")
                
        except sqlite3.OperationalError as e:
            print(f"  Skipping table '{table}' (might not exist or no date_entered column): {e}")

    conn.commit()
    conn.close()
    print("Database cleaning complete.")

if __name__ == "__main__":
    db_file = 'db.sqlite3'
    if os.path.exists(db_file):
        clean_database(db_file)
    else:
        print(f"Error: {db_file} not found in current directory.")
