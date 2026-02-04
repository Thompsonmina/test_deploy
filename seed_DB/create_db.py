"""
Script 2: create_db.py
======================
Creates a populated SQLite database from the cleaned SQL file.

Usage:
    python create_db.py cleaned_data.txt db.sqlite3
"""

import sqlite3
import sys
import re


def create_database(input_file, db_file):
    """Create SQLite database from cleaned SQL file."""
    
    print(f"Reading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Creating: {db_file}")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # =========================================================================
    # EXECUTE CREATE TABLE STATEMENTS
    # =========================================================================
    print("\nCreating tables...")
    
    # Find CREATE TABLE statements (they end with );)
    create_pattern = r'CREATE TABLE IF NOT EXISTS \w+ \([^;]+\);'
    
    tables_created = 0
    for match in re.finditer(create_pattern, content, re.DOTALL):
        sql = match.group(0)
        table_name = re.search(r'CREATE TABLE IF NOT EXISTS (\w+)', sql).group(1)
        
        try:
            cursor.execute(sql)
            tables_created += 1
            print(f"  ✓ {table_name}")
        except sqlite3.Error as e:
            print(f"  ✗ {table_name}: {e}")
    
    conn.commit()
    
    # =========================================================================
    # EXECUTE INSERT STATEMENTS
    # =========================================================================
    print("\nInserting data...")
    
    # Find INSERT statements
    insert_pattern = r'INSERT INTO (\w+) \(([^)]+)\) VALUES ([^;]+);'
    
    total_rows = 0
    for match in re.finditer(insert_pattern, content, re.DOTALL):
        table_name = match.group(1)
        columns = match.group(2)
        values_section = match.group(3).strip()
        
        # Execute the full INSERT statement
        full_sql = f"INSERT INTO {table_name} ({columns}) VALUES {values_section}"
        
        try:
            cursor.executescript(full_sql + ";")
            # Count rows inserted
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  ✓ {table_name}: {count} rows")
            total_rows += count
        except sqlite3.Error as e:
            # Try inserting row by row if bulk fails
            rows_inserted = insert_rows_individually(cursor, table_name, columns, values_section)
            print(f"  ✓ {table_name}: {rows_inserted} rows (individual insert)")
            total_rows += rows_inserted
    
    conn.commit()
    
    # =========================================================================
    # VERIFY
    # =========================================================================
    print("\n" + "=" * 50)
    print("DATABASE SUMMARY")
    print("=" * 50)
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    for (table_name,) in cursor.fetchall():
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  {table_name}: {count} rows")
    
    conn.close()
    print("=" * 50)
    print(f"Database saved: {db_file}")


def insert_rows_individually(cursor, table_name, columns, values_section):
    """Insert rows one at a time if bulk insert fails."""
    
    rows_inserted = 0
    
    # Parse individual value tuples
    rows = parse_value_tuples(values_section)
    
    col_list = [c.strip() for c in columns.split(',')]
    placeholders = ','.join(['?' for _ in col_list])
    insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    for row in rows:
        try:
            values = parse_row_values(row)
            if len(values) == len(col_list):
                cursor.execute(insert_sql, values)
                rows_inserted += 1
        except:
            pass  # Skip problematic rows
    
    return rows_inserted


def parse_value_tuples(values_section):
    """Split VALUES section into individual (row) tuples."""
    
    rows = []
    current = ''
    depth = 0
    in_string = False
    escape = False
    
    for char in values_section:
        if escape:
            current += char
            escape = False
            continue
        
        if char == '\\':
            escape = True
            current += char
            continue
        
        if char == "'" and not escape:
            in_string = not in_string
            current += char
            continue
        
        if not in_string:
            if char == '(':
                depth += 1
                if depth == 1:
                    current = ''
                    continue
            elif char == ')':
                depth -= 1
                if depth == 0:
                    rows.append(current)
                    current = ''
                    continue
            elif char == ',' and depth == 0:
                continue
        
        if depth > 0:
            current += char
    
    return rows


def parse_row_values(row_str):
    """Parse a row string into Python values."""
    
    values = []
    current = ''
    in_string = False
    escape = False
    
    for char in row_str + ',':
        if escape:
            current += char
            escape = False
            continue
        
        if char == '\\':
            escape = True
            continue
        
        if char == "'" and not escape:
            in_string = not in_string
            continue
        
        if char == ',' and not in_string:
            val = current.strip()
            if val.upper() == 'NULL' or val == '':
                values.append(None)
            elif val.lstrip('-').isdigit():
                values.append(int(val))
            else:
                values.append(val)
            current = ''
        else:
            current += char
    
    return values


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python create_db.py <input.txt> <output.db>")
        print("Example: python create_db.py cleaned_data.txt db.sqlite3")
        sys.exit(1)
    
    try:
        create_database(sys.argv[1], sys.argv[2])
        print("\nDone!")
    except FileNotFoundError:
        print(f"Error: File not found")
        sys.exit(1)