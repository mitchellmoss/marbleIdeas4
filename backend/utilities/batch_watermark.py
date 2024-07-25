#USAGE: python batch_watermark.py ./database_images "Marble.Boston" 10
#USAGE: This will process all PNG images in the ./database_images directory, using the watermark text "Marble.Boston" and 10 worker threads.
import os
import sys
import concurrent.futures
import PIL.Image as Image
import numpy as np
from backend.utilities.watermarkTest import encode_lsb, decode_lsb
import sqlite3
import io

def process_image(db_path, row_id, watermark_text, action):
    try:
        # Create a new connection for each thread
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Fetch the image data
        cursor.execute("SELECT image, fileName FROM images WHERE id = ?", (row_id,))
        image_blob, file_name = cursor.fetchone()
        
        image = Image.open(io.BytesIO(image_blob))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        img_array = np.array(image, dtype=np.uint8)  # Ensure we have a writable array

        if action == 'encode':
            watermarked_array = encode_lsb(img_array.copy(), watermark_text)  # Use a copy to ensure it's writable
            watermarked_img = Image.fromarray(watermarked_array)
            img_byte_arr = io.BytesIO()
            watermarked_img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            cursor.execute("UPDATE images SET image = ? WHERE id = ?", (img_byte_arr, row_id))
            conn.commit()
            result = f"Watermarked image saved for ID: #{row_id} (File: {file_name})"
        elif action == 'decode':
            watermark = decode_lsb(img_array)
            result = f"Extracted watermark from ID: #{row_id} (File: {file_name}): {watermark}"
        
        conn.close()
        return result
    except Exception as e:
        return f"Error processing ID: #{row_id} (File: {file_name if 'file_name' in locals() else 'unknown'}): {str(e)}"

def batch_process_images(db_path, watermark_text, action, max_workers=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM images")
    image_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for row_id in image_ids:
            future = executor.submit(process_image, db_path, row_id, watermark_text, action)
            futures.append(future)
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if action == 'encode':
                print(f"Image processing result: {result}")
            elif action == 'decode':
                print(f"Watermark verification result: {result}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python batch_watermark.py [database_file] [watermark_text] [max_workers (optional)]")
        sys.exit(1)
    
    db_path = os.path.abspath(sys.argv[1])
    watermark_text = sys.argv[2]
    max_workers = int(sys.argv[3]) if len(sys.argv) > 3 else None

    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' does not exist.")
        sys.exit(1)

    print("Applying watermarks...")
    batch_process_images(db_path, watermark_text, 'encode', max_workers)

    print("\nVerifying watermarks...")
    batch_process_images(db_path, watermark_text, 'decode', max_workers)

#Key changes:
# 1. The process_image function now creates its own database connection for each thread. It takes the db_path as an argument instead of a connection object.
# 2. In batch_process_images, we now only fetch the image IDs from the main thread and pass these to the worker threads.
# 3. Each worker thread now handles its own database operations (fetching the image data, updating the image, etc.) within its own connection.
# This approach ensures that each thread has its own SQLite connection, which should resolve the thread-safety issues you were encountering.
# Also, make sure that your watermarkTest.py file (containing encode_lsb and decode_lsb functions) is in the same directory as this script or in your Python path.
# Try running this updated script. It should now handle the database operations in a thread-safe manner and avoid the SQLite thread errors you were seeing before.
