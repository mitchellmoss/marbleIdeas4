import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
import io
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Import the functions from imageColor.py using direct imports
from backend.utilities.imageColor import (
    get_dominant_color,
    get_brightest_color,
    process_marble,
    update_marble_color,
    get_db_connection,
    retry_on_db_lock,
    is_color_valid
)

class TestImageColor(unittest.TestCase):

    def setUp(self):
        self.marble_name = "test_marble"
        self.html_file = open("test_colors.html", "w")
        self.html_file.write("<html><body><h1>Test Colors</h1><ul>")
        self.colors = self.fetch_colors_from_db()
        logging.debug(f"Fetched colors: {self.colors}")

    def tearDown(self):
        self.html_file.write("</ul></body></html>")
        self.html_file.close()

    def fetch_colors_from_db(self):
        conn = sqlite3.connect('/Users/mitchellmoss/Documents/marbleIdeas/backend/marble_images-2.db')
        cursor = conn.cursor()
        cursor.execute("SELECT stoneColor FROM images")
        colors = cursor.fetchall()
        conn.close()
        return [color[0] for color in colors]

    def create_sample_image_blob(self, color):
        # Create a simple RGB image for testing
        image = Image.new('RGB', (10, 10), color=color)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()

    def log_color(self, color_hex):
        self.html_file.write(f"<li style='background-color:{color_hex};'>{color_hex}</li>")

    def test_get_dominant_color(self):
        for color_hex in self.colors:
            if color_hex is None:
                logging.error("Encountered None value in test_get_dominant_color")
                continue
            color = self.hex_to_rgb(color_hex)
            image_blob = self.create_sample_image_blob(color)
            logging.debug(f"Testing get_dominant_color with color: {color_hex}")
            dominant_color = get_dominant_color(image_blob, self.marble_name)
            logging.debug(f"Result from get_dominant_color: {dominant_color}")
            self.assertEqual(dominant_color, color_hex, f"The dominant color should be {color_hex}")
            self.log_color(color_hex)

    def test_get_brightest_color(self):
        for color_hex in self.colors:
            if color_hex is None:
                logging.error("Encountered None value in test_get_brightest_color")
                continue
            color = self.hex_to_rgb(color_hex)
            image_blob = self.create_sample_image_blob(color)
            logging.debug(f"Testing get_brightest_color with color: {color_hex}")
            brightest_color = get_brightest_color(image_blob, self.marble_name)
            logging.debug(f"Result from get_brightest_color: {brightest_color}")
            self.assertEqual(brightest_color, color_hex, f"The brightest color should be {color_hex}")
            self.log_color(color_hex)

    @patch('imageColor.update_marble_color')
    def test_process_marble_dominant(self, mock_update_marble_color):
        for color_hex in self.colors:
            if color_hex is None:
                logging.error("Encountered None value in test_process_marble_dominant")
                continue
            color = self.hex_to_rgb(color_hex)
            image_blob = self.create_sample_image_blob(color)
            data = (self.marble_name, image_blob, None)
            logging.debug(f"Testing process_marble with color: {color_hex} for dominant color")
            result = process_marble(data, 'dominant')
            logging.debug(f"Result from process_marble (dominant): {result}")
            self.assertIsNotNone(result, "The result should not be None")
            self.assertEqual(result[1], color_hex, f"The dominant color should be {color_hex}")
            mock_update_marble_color.assert_called_with(self.marble_name, color_hex)
            self.log_color(color_hex)

    @patch('imageColor.update_marble_color')
    def test_process_marble_brightest(self, mock_update_marble_color):
        for color_hex in self.colors:
            if color_hex is None:
                logging.error("Encountered None value in test_process_marble_brightest")
                continue
            color = self.hex_to_rgb(color_hex)
            image_blob = self.create_sample_image_blob(color)
            data = (self.marble_name, image_blob, None)
            logging.debug(f"Testing process_marble with color: {color_hex} for brightest color")
            result = process_marble(data, 'brightest')
            logging.debug(f"Result from process_marble (brightest): {result}")
            self.assertIsNotNone(result, "The result should not be None")
            self.assertEqual(result[1], color_hex, f"The brightest color should be {color_hex}")
            mock_update_marble_color.assert_called_with(self.marble_name, color_hex)
            self.log_color(color_hex)

    @patch('imageColor.get_db_connection')
    def test_update_marble_color(self, mock_get_db_connection):
        for color_hex in self.colors:
            if color_hex is None:
                logging.error("Encountered None value in test_update_marble_color")
                continue
            color = self.hex_to_rgb(color_hex)
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_get_db_connection.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            logging.debug(f"Testing update_marble_color with color: {color_hex}")
            update_marble_color(self.marble_name, color_hex)

            mock_cursor.execute.assert_called_with(
                "UPDATE images SET stoneColor = ? WHERE marbleName = ?", (color_hex, self.marble_name)
            )
            mock_conn.commit.assert_called()
            self.log_color(color_hex)

    def hex_to_rgb(self, hex_color):
        if hex_color is None:
            return (0, 0, 0)  # Default to black if color is None
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

if __name__ == '__main__':
    unittest.main()