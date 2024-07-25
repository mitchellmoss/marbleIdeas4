import numpy as np
from PIL import Image
import io

def to_bin(data):
    """Convert data to binary format as string"""
    if isinstance(data, str):
        return ''.join(format(ord(i), '08b') for i in data)
    elif isinstance(data, bytes) or isinstance(data, np.ndarray):
        return [format(i, '08b') for i in data]
    elif isinstance(data, int) or isinstance(data, np.uint8):
        return format(data, '08b')
    else:
        raise TypeError("Type not supported.")

def encode_lsb(image, secret_data):
    """Encode data into least significant bits of image"""
    n_bytes = image.shape[0] * image.shape[1] * 3 // 8
    if len(secret_data) > n_bytes:
        raise ValueError("Error: Insufficient bytes, need bigger image or less data.")

    secret_data += "====="  # Adding delimiter
    data_index = 0
    binary_secret_data = to_bin(secret_data)
    data_len = len(binary_secret_data)

    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            for k in range(3):
                if data_index < data_len:
                    image[i, j, k] = int(bin(image[i, j, k])[2:9] + binary_secret_data[data_index], 2)
                    data_index += 1
                if data_index >= data_len:
                    return image
    return image

def decode_lsb(image):
    """Decode the hidden data in the image"""
    binary_data = ""
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            for k in range(3):
                binary_data += bin(image[i, j, k])[-1]

    all_bytes = [binary_data[i: i+8] for i in range(0, len(binary_data), 8)]
    decoded_data = ""
    for byte in all_bytes:
        decoded_data += chr(int(byte, 2))
        if decoded_data[-5:] == "=====":
            return decoded_data[:-5]
    return ""

def apply_watermark(image_path, watermark_text):
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img_array = np.array(img)
        watermarked_array = encode_lsb(img_array, watermark_text)
        watermarked_img = Image.fromarray(watermarked_array)
        output_path = f"watermarked_{image_path}"
        watermarked_img.save(output_path, format='png')
        print(f"Watermarked image saved as {output_path}")

def extract_watermark(image_path):
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img_array = np.array(img)
        watermark = decode_lsb(img_array)
        if watermark:
            print(f"Extracted watermark: {watermark}")
        else:
            print("No valid watermark found or watermark is empty.")
        return watermark

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python watermarkTest.py [encode/decode] [image_path] [watermark_text (for encode only)]")
        sys.exit(1)
    
    action = sys.argv[1]
    image_path = sys.argv[2]
    
    if action == "encode":
        if len(sys.argv) < 4:
            print("Please provide a watermark text for encoding.")
            sys.exit(1)
        watermark_text = sys.argv[3]
        apply_watermark(image_path, watermark_text)
    elif action == "decode":
        extract_watermark(image_path)
    else:
        print("Invalid action. Use 'encode' or 'decode'.")
        sys.exit(1)