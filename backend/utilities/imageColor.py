import sqlite3
import logging
import time
from PIL import Image, UnidentifiedImageError
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import io
import threading
import functools
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Thread-local storage for database connections
local_data = threading.local()

def get_db_connection():
    if not hasattr(local_data, "connection"):
        local_data.connection = sqlite3.connect('marble_images-2.db', timeout=30)
    return local_data.connection

def retry_on_db_lock(max_attempts=5, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        attempts += 1
                        if attempts == max_attempts:
                            logger.error(f"Max attempts reached. Failed to execute {func.__name__}")
                            raise
                        sleep_time = delay * (2 ** attempts) + random.uniform(0, 1)
                        logger.warning(f"Database locked. Retrying in {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
                    else:
                        raise
        return wrapper
    return decorator

def is_color_valid(color):
    r, g, b = color
    # Check if the color is not pure white (255, 255, 255) or pure black (0, 0, 0)
    return not ((r == g == b == 255) or (r == g == b == 0))

def get_dominant_color(image_blob, marble_name):
    try:
        image = Image.open(io.BytesIO(image_blob))
        image = image.convert('RGB')
        width, height = image.size
        pixels = image.getcolors(width * height)

        # Sort pixels by count and filter out pure white and pure black
        sorted_pixels = sorted(
            [p for p in pixels if is_color_valid(p[1])],
            key=lambda t: t[0],
            reverse=True
        )

        if not sorted_pixels:
            logger.warning(f"No valid colors found for {marble_name}")
            return None

        dominant_color = sorted_pixels[0][1]
        hex_color = '#{:02x}{:02x}{:02x}'.format(*dominant_color)
        return hex_color
    except UnidentifiedImageError:
        logger.error(f"Unable to identify image format for {marble_name}")
    except Exception as e:
        logger.error(f"Error processing image for {marble_name}: {str(e)}")
    return None

def get_brightest_color(image_blob, marble_name):
    try:
        image = Image.open(io.BytesIO(image_blob))
        image = image.convert('RGB')
        width, height = image.size
        pixels = image.getcolors(width * height)

        # Find the brightest color
        brightest_color = None
        max_brightness = -1

        for count, color in pixels:
            if is_color_valid(color):
                # Calculate brightness
                brightness = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
                if brightness > max_brightness:
                    max_brightness = brightness
                    brightest_color = color

        if brightest_color is None:
            logger.warning(f"No valid colors found for {marble_name}")
            return None

        hex_color = '#{:02x}{:02x}{:02x}'.format(*brightest_color)
        return hex_color
    except UnidentifiedImageError:
        logger.error(f"Unable to identify image format for {marble_name}")
    except Exception as e:
        logger.error(f"Error processing image for {marble_name}: {str(e)}")
    return None

@retry_on_db_lock()
def update_marble_color(marble_name, new_color):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE images SET stoneColor = ? WHERE marbleName = ?", (new_color, marble_name))
    conn.commit()
    logger.info(f"Updated color for {marble_name} in database")

def process_marble(data, color_algorithm):
    marble_name, image_blob, stone_color = data
    logger.info(f"Processing marble: {marble_name}")
    if not stone_color:
        try:
            if color_algorithm == 'dominant':
                new_color = get_dominant_color(image_blob, marble_name)
            else:
                new_color = get_brightest_color(image_blob, marble_name)

            if new_color:
                logger.info(f"Determined color for {marble_name}: {new_color}")
                update_marble_color(marble_name, new_color)
                return (marble_name, new_color)
            else:
                logger.warning(f"Could not determine color for {marble_name}")
        except Exception as e:
            logger.error(f"Failed to process marble {marble_name}: {str(e)}")
    return None

def main():
    try:
        conn = sqlite3.connect('marble_images-2.db', timeout=30)
        cursor = conn.cursor()

        cursor.execute("SELECT marbleName, image, stoneColor FROM images WHERE stoneColor IS NULL OR stoneColor = '' OR stoneColor IN ('#FFFFFF', '#000000')")
        marble_data = cursor.fetchall()

        logger.info(f"Found {len(marble_data)} marbles without valid stoneColor")

        # Ask user for color algorithm choice
        color_algorithm = input("Choose color algorithm (dominant/brightest): ").strip().lower()
        if color_algorithm not in ['dominant', 'brightest']:
            logger.error("Invalid choice. Defaulting to 'dominant'.")
            color_algorithm = 'dominant'

        results = []
        with ThreadPoolExecutor(max_workers=128) as executor:
            future_to_marble = {executor.submit(process_marble, data, color_algorithm): data for data in marble_data}
            for future in as_completed(future_to_marble):
                try:
                    result = future.result(timeout=60)
                    if result:
                        results.append(result)
                except TimeoutError:
                    marble_name = future_to_marble[future][0]
                    logger.error(f"Processing timed out for {marble_name}")
                except Exception as e:
                    marble_name = future_to_marble[future][0]
                    logger.error(f"Error processing {marble_name}: {str(e)}")

        cursor.execute("SELECT COUNT(*) FROM images WHERE stoneColor IS NOT NULL AND stoneColor != ''")
        updated_count = cursor.fetchone()[0]
        logger.info(f"Total marbles with stoneColor after update: {updated_count}")

        conn.close()
        logger.info("Processing completed")

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()