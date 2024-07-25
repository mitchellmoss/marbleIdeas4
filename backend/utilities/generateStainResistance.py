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

def generate_stain_resistance(marble_name, marble_origin):
    """Generates stain resistance information for a marble using Claude-3 Sonnet."""
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=10,
                system="You are an expert in material science, specializing in the stain resistance properties of marble. Your task is to provide concise, accurate information about the stain resistance characteristics of different types of marble. Rate the stain resistance on a scale of 1 to 10, where 1 is very poor and 10 is excellent.",
                messages=[
                    {
                        "role": "user",
                        "content": f"Provide the stain resistance rating for '{marble_name}' marble from {marble_origin}. ///ONLY RETURN THE NUMERICAL RATING FROM 1 TO 10. ///DO NOT INCLUDE ANY WORDS, ONLY THE NUMBER"
                    }
                ]
            )
            return message.content[0].text
        except RequestException as e:
            logger.warning(f"Request failed for {marble_name}: {str(e)}. Attempt {attempt + 1} of {max_retries}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to generate stain resistance info for {marble_name} after {max_retries} attempts")
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Unexpected error generating stain resistance info for {marble_name}: {str(e)}")
            raise

def process_marble(data):
    marble_name, _, marble_origin = data
    try:
        new_stain_resistance = generate_stain_resistance(marble_name, marble_origin)
        return (marble_name, new_stain_resistance)
    except Exception as e:
        logger.error(f"Failed to process marble {marble_name}: {str(e)}")
        return None

def update_database(queue):
    conn = sqlite3.connect('marble_images-2.db')
    cursor = conn.cursor()
    while True:
        item = queue.get()
        if item is None:
            break
        marble_name, new_stain_resistance = item
        try:
            cursor.execute("UPDATE images SET stainResistance = ? WHERE marbleName = ?", (new_stain_resistance, marble_name))
            conn.commit()
            logger.info(f"Updated stain resistance for {marble_name}: {new_stain_resistance}")
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

        # Fetch all marble names and origins from the database
        cursor.execute("SELECT marbleName, stainResistance, marbleOrigin FROM images")
        marble_data = cursor.fetchall()
        conn.close()

        logger.info(f"Found {len(marble_data)} marbles to process")

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
                        logger.info(f"Failed to process {marble_name}")
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