import sqlite3
import sys
import os
from fuzzywuzzy import fuzz, process

def connect_to_db():
    return sqlite3.connect('marble_images-2.db')

def execute_query(query, params=None):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

def add_vendor(name, location, logo_path=None):
    query = 'INSERT INTO vendors (name, location) VALUES (?, ?)'
    vendor_id = execute_query(query, (name, location))
    
    if logo_path:
        update_logo(vendor_id, logo_path)
    
    print(f"Vendor '{name}' added successfully with ID: {vendor_id}")

def update_vendor(vendor_id, column, value):
    if column.lower() == 'logo':
        update_logo(vendor_id, value)
    else:
        query = f'UPDATE vendors SET {column} = ? WHERE id = ?'
        execute_query(query, (value, vendor_id))
        print(f"Vendor ID {vendor_id} updated successfully. Column '{column}' set to '{value}'")

def update_logo(vendor_id, logo_path):
    with open(logo_path, 'rb') as file:
        blob_data = file.read()
    query = 'UPDATE vendors SET vendorLogo = ? WHERE id = ?'
    execute_query(query, (blob_data, vendor_id))
    print(f"Logo updated for Vendor ID {vendor_id}")

def delete_vendor(vendor_id):
    query = 'DELETE FROM vendors WHERE id = ?'
    execute_query(query, (vendor_id,))
    print(f"Vendor ID {vendor_id} deleted successfully")

def list_vendors():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, location FROM vendors')
    vendors = cursor.fetchall()
    conn.close()
    
    print("ID | Name | Location")
    print("-" * 30)
    for vendor in vendors:
        print(f"{vendor[0]} | {vendor[1]} | {vendor[2]}")

def get_vendor(search_term):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, location FROM vendors')
    vendors = cursor.fetchall()

    if search_term.isdigit():
        # If the search term is a number, assume it's an ID
        vendor_id = int(search_term)
        matching_vendors = [v for v in vendors if v[0] == vendor_id]
    else:
        # Use fuzzy matching for name search
        name_matches = process.extract(search_term, [v[1] for v in vendors], limit=None, scorer=fuzz.partial_ratio)
        matching_vendors = [v for v in vendors if v[1] in [m[0] for m in name_matches if m[1] >= 70]]

    if matching_vendors:
        print(f"Found {len(matching_vendors)} matching vendor(s):")
        for vendor in matching_vendors:
            print("\nVendor Details:")
            print(f"ID: {vendor[0]}")
            print(f"Name: {vendor[1]}")
            print(f"Location: {vendor[2]}")
            
            # Check if logo is present
            cursor.execute('SELECT vendorLogo FROM vendors WHERE id = ?', (vendor[0],))
            logo_data = cursor.fetchone()[0]
            print(f"Logo: {'Present' if logo_data else 'Not present'}")
    else:
        print(f"No vendors found matching '{search_term}'")

    conn.close()

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Add vendor:    python manage_vendors.py add <name> <location> [logo <filename>]")
        print("  Update vendor: python manage_vendors.py update <id> <column> <value>")
        print("  Delete vendor: python manage_vendors.py delete <id>")
        print("  List vendors:  python manage_vendors.py list")
        print("  Get vendor:    python manage_vendors.py get <id or name>")
        return

    command = sys.argv[1].lower()
    if command == 'add':
        if len(sys.argv) < 4:
            print("Usage: python manage_vendors.py add <name> <location> [logo <filename>]")
            return
        name = sys.argv[2]
        location = sys.argv[3]
        logo_path = None
        if len(sys.argv) > 5 and sys.argv[4].lower() == 'logo':
            logo_path = sys.argv[5]
        add_vendor(name, location, logo_path)

    elif command == 'update':
        if len(sys.argv) < 5:
            print("Usage: python manage_vendors.py update <id> <column> <value>")
            return
        vendor_id = int(sys.argv[2])
        column = sys.argv[3]
        value = sys.argv[4]
        update_vendor(vendor_id, column, value)

    elif command == 'delete':
        if len(sys.argv) < 3:
            print("Usage: python manage_vendors.py delete <id>")
            return
        vendor_id = int(sys.argv[2])
        delete_vendor(vendor_id)

    elif command == 'list':
        list_vendors()

    elif command == 'get':
        if len(sys.argv) < 3:
            print("Usage: python manage_vendors.py get <id or name>")
            return
        search_term = " ".join(sys.argv[2:])
        get_vendor(search_term)

    else:
        print("Invalid command. Use 'add', 'update', 'delete', 'list', or 'get'.")

if __name__ == "__main__":
    main()