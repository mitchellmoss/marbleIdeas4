import sqlite3
import os
import logging
import time
from anthropic import Anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from requests.exceptions import RequestException

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_description(marble_name, marble_origin):
    """Generates a description for a marble using Claude-3 Sonnet."""
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=300,
                system="You are a creative writer specializing in concise, engaging descriptions of marbles. Your task is to create short, appealing descriptions for marble names, suitable for a website catalog. Each description should be unique, highlighting the marble's potential appearance and physical characteristics. Include the location where it is quarried and how rare it is. Do not use flowery or fancy language.",
                messages=[
                    {
                        "role": "user",
                        "content": f"Write a short, engaging description for a marble named '{marble_name}' from {marble_origin}. The description should be suitable for a website catalog, about 2-3 sentences long."
                    }
                ]
            )
            return message.content[0].text
        except RequestException as e:
            logger.warning(f"Request failed for {marble_name}: {str(e)}. Attempt {attempt + 1} of {max_retries}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to generate description for {marble_name} after {max_retries} attempts")
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Unexpected error generating description for {marble_name}: {str(e)}")
            raise

def process_marble(data):
    marble_name, description, marble_origin = data
    if not description:
        try:
            new_description = generate_description(marble_name, marble_origin)
            return (marble_name, new_description)
        except Exception as e:
            logger.error(f"Failed to process marble {marble_name}: {str(e)}")
            return None
    return None

def update_database(queue):
    conn = sqlite3.connect('marble_images-2.db')
    cursor = conn.cursor()
    while True:
        item = queue.get()
        if item is None:
            break
        marble_name, new_description = item
        try:
            cursor.execute("UPDATE images SET description = ? WHERE marbleName = ?", (new_description, marble_name))
            conn.commit()
            logger.info(f"Updated description for {marble_name}: {new_description}")
        except sqlite3.Error as e:
            logger.error(f"Database error updating {marble_name}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error updating {marble_name}: {str(e)}")
    conn.close()

def main():
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('marble_images-2.db')
        cursor = conn.cursor()

        # Fetch marble names, descriptions, and origins from the database
        cursor.execute("SELECT marbleName, description, marbleOrigin FROM images WHERE description IS NULL OR description = ''")
        marble_data = cursor.fetchall()
        conn.close()

        logger.info(f"Found {len(marble_data)} marbles without descriptions")

        # Create a queue for database updates
        update_queue = Queue()

        # Start a separate thread for database updates
        update_thread = ThreadPoolExecutor(max_workers=1)
        update_future = update_thread.submit(update_database, update_queue)

        # Process marbles using multithreading
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_marble = {executor.submit(process_marble, data): data for data in marble_data}
            for future in as_completed(future_to_marble):
                try:
                    result = future.result()
                    if result:
                        update_queue.put(result)
                    else:
                        marble_name = future_to_marble[future][0]
                        logger.info(f"Skipped {marble_name} as it already has a description or failed to process")
                except Exception as e:
                    marble_name = future_to_marble[future][0]
                    logger.error(f"Error processing {marble_name}: {str(e)}")

        # Signal the update thread to finish
        update_queue.put(None)
        update_future.result()

        # Shutdown the update thread
        update_thread.shutdown()

        logger.info("Processing completed")

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()