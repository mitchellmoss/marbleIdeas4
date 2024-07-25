import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('marble_images-2.db')
cursor = conn.cursor()

# Fetch all rows from the images table
cursor.execute("SELECT id, fileName FROM images")
rows = cursor.fetchall()

# Update the file extensions
for row in rows:
    id, fileName = row
    if fileName.lower().endswith('.jpeg'):
        new_fileName = fileName[:-5] + '.png'
        cursor.execute("UPDATE images SET fileName = ? WHERE id = ?", (new_fileName, id))

# Commit the changes and close the connection
conn.commit()
conn.close()

print("File extensions updated successfully.")