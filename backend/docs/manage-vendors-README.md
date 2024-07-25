# Vendor Management Script Documentation

This Python script allows you to manage vendors in a SQLite database (`marble_images-2.db`). It provides functionality to add, update, delete, list, and get vendor information.

## Usage

```
python manage_vendors.py <command> [arguments]
```

## Commands

### Add Vendor

Add a new vendor to the database.

```
python manage_vendors.py add <name> <location> [logo <filename>]
```

- `<name>`: The name of the vendor (required)
- `<location>`: The location of the vendor (required)
- `[logo <filename>]`: Optional logo file path

Example:
```
python manage_vendors.py add "Acme Corp" "New York" logo logo.png
```

### Update Vendor

Update an existing vendor's information.

```
python manage_vendors.py update <id> <column> <value>
```

- `<id>`: The ID of the vendor to update (required)
- `<column>`: The column to update (name, location, or logo) (required)
- `<value>`: The new value for the column (required)

Examples:
```
python manage_vendors.py update 1 name "New Acme Corp"
python manage_vendors.py update 1 location "Los Angeles"
python manage_vendors.py update 1 logo new_logo.png
```

### Delete Vendor

Delete a vendor from the database.

```
python manage_vendors.py delete <id>
```

- `<id>`: The ID of the vendor to delete (required)

Example:
```
python manage_vendors.py delete 1
```

### List Vendors

Display a list of all vendors in the database.

```
python manage_vendors.py list
```

### Get Vendor

Retrieve and display detailed information about a specific vendor.

```
python manage_vendors.py get <id>
```

- `<id>`: The ID of the vendor to retrieve (required)

Example:
```
python manage_vendors.py get 1
```

## Error Handling

The script will display usage information if the command or arguments are incorrect. It also handles database errors and provides appropriate error messages.

## Database

The script uses a SQLite database named `marble_images-2.db`. Ensure this database file is in the same directory as the script or provide the full path to the database in the `connect_to_db()` function.

## Notes

- When updating a logo, provide the file path to the new logo image.
- The script stores logo images as BLOBs (Binary Large Objects) in the database.
- Make sure you have the necessary permissions to read/write to the database and access image files when adding or updating logos.


## ASSOCIATING MARBLES

To add a new column called `associatedVendor` to the `marble_images-2` table in your SQLite database, you'll need to use SQL ALTER TABLE statement. However, since you mentioned that there could be multiple vendors selling the same marble, we need to approach this differently. In relational databases, we typically handle many-to-many relationships using a junction table.

Here's how you can modify your database structure to accommodate this relationship:

1. First, let's add the new column to the `marble_images-2` table:

```sql
ALTER TABLE marble_images-2 ADD COLUMN associatedVendor TEXT;
```

2. Then, create a new junction table to handle the many-to-many relationship between marbles and vendors:

```sql
CREATE TABLE marble_vendor_association (
    marble_id INTEGER,
    vendor_id INTEGER,
    FOREIGN KEY (marble_id) REFERENCES marble_images-2(id),
    FOREIGN KEY (vendor_id) REFERENCES vendors(id),
    PRIMARY KEY (marble_id, vendor_id)
);
```

This approach has several advantages:

1. It maintains data integrity by using foreign keys.
2. It allows for multiple vendors per marble and multiple marbles per vendor.
3. It's more flexible for future queries and data manipulation.

## To use this new structure:

1. When you want to associate a vendor with a marble, insert a row into the `marble_vendor_association` table:

```sql
INSERT INTO marble_vendor_association (marble_id, vendor_id) VALUES (1, 2);
```

2. To retrieve all vendors for a specific marble:

```sql
SELECT v.* 
FROM vendors v
JOIN marble_vendor_association mva ON v.id = mva.vendor_id
WHERE mva.marble_id = 1;
```

3. To retrieve all marbles for a specific vendor:

```sql
SELECT m.* 
FROM marble_images-2 m
JOIN marble_vendor_association mva ON m.id = mva.marble_id
WHERE mva.vendor_id = 2;
```

This solution provides a more robust and flexible way to handle the many-to-many relationship between marbles and vendors in your SQLite database.