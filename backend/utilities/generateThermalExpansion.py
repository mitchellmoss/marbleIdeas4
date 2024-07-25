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

def generate_thermal_expansion(marble_name, marble_origin):
    """Generates thermal expansion information for a marble using Claude-3 Sonnet."""
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=10,
                system="You are an expert in material science, specializing in the thermal properties of marble. Your task is to provide concise, accurate information about the thermal expansion characteristics of different types of marble. Include the coefficient of thermal expansion in mm/m/°C",
                messages=[
                    {
                        "role": "user",
                        "content": f"Provide the thermal expansion properties for '{marble_name}' marble from {marble_origin}. Include the coefficient of thermal expansion if known, and any specific behaviors when exposed to heat. ///ONLY RETURN THE SCIENTIFIC VALUE IN mm/m/°C IN FORMAT 0.0000. ///OMIT mm/m/°C AS IT IS HARD CODED INTO THE FRONTEND. ///DO NOT INCLUDE ANY WORDS, ONLY THE NUMBERS"
                    }
                ]
            )
            return message.content[0].text
        except RequestException as e:
            logger.warning(f"Request failed for {marble_name}: {str(e)}. Attempt {attempt + 1} of {max_retries}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to generate thermal expansion info for {marble_name} after {max_retries} attempts")
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Unexpected error generating thermal expansion info for {marble_name}: {str(e)}")
            raise

def process_marble(data):
    marble_name, _, marble_origin = data
    try:
        new_thermal_expansion = generate_thermal_expansion(marble_name, marble_origin)
        return (marble_name, new_thermal_expansion)
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
        marble_name, new_thermal_expansion = item
        try:
            cursor.execute("UPDATE images SET thermalExpansion = ? WHERE marbleName = ?", (new_thermal_expansion, marble_name))
            conn.commit()
            logger.info(f"Updated thermal expansion for {marble_name}: {new_thermal_expansion}")
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
        cursor.execute("SELECT marbleName, thermalExpansion, marbleOrigin FROM images")
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