from torchvision.models import ResNet50_Weights
from flask import Flask, jsonify, send_file, send_from_directory, make_response, abort, request
import time, logging, sqlite3, os, math, io, base64, faiss, numpy as np, traceback
from logging.handlers import RotatingFileHandler
from sklearn.preprocessing import normalize
from werkzeug.utils import secure_filename
from PIL import Image, ImageEnhance, ImageFilter
import torch
from torchvision import transforms, models
from collections import Counter
from flask_cors import CORS

current_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(current_dir, 'marble_images-2.db')
index_path = os.path.join(current_dir, "marble_image_index.faiss")

try:
    index = faiss.read_index(index_path)
    print(f"FAISS index loaded successfully from {index_path}")
    print(f"FAISS index dimension: {index.d}")
    print(f"Total vectors in FAISS index: {index.ntotal}")
except RuntimeError as e:
    print(f"Error: Unable to read the FAISS index file at {index_path}")
    print(f"Make sure the file exists and you have the necessary permissions.")
    print(f"Original error: {str(e)}")
    index = None

BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'marble-gallery', 'build'))

def get_marble_id_from_index(index_position):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM images ORDER BY id LIMIT 1 OFFSET ?", (int(index_position),))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def generate_pixel():
    return base64.b64decode('R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==')

app = Flask(__name__, static_folder=BUILD_DIR, static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "https://marble.boston"}})
if not app.debug:
    file_handler = RotatingFileHandler('marble_gallery.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Marble Gallery startup')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    app.logger.info(f"Received request for path: {path}")
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        app.logger.info(f"Serving static file: {path}")
        allowed_extensions = {'.html', '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.json'}
        file_ext = os.path.splitext(path)[1].lower()
        if file_ext in allowed_extensions:
            if file_ext == '.js' and not path.startswith('static/js/'):
                abort(404)
            return send_from_directory(app.static_folder, path)
    if path in ['', 'about', 'contact', 'upload'] or not os.path.splitext(path)[1]:
        app.logger.info(f"Serving index.html for path: {path}")
        return send_from_directory(app.static_folder, 'index.html')
    app.logger.warning(f"404 - File not found: {path}")
    abort(404)

@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f"404 - Not Found: {request.url}")
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/images', methods=['GET'])
def get_images():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search_term = request.args.get('search', '')
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    offset = (page - 1) * per_page
    
    if search_term:
        # Use FTS5 for efficient full-text search
        c.execute("""
            SELECT COUNT(*) 
            FROM images_fts 
            WHERE images_fts MATCH ? 
        """, (search_term,))
        total_images = c.fetchone()[0]
        
        c.execute("""
            SELECT id, marbleName, marbleOrigin, fileName, stainResistance, costRange, stoneColor, description, thermalExpansion 
            FROM images_fts 
            WHERE images_fts MATCH ? 
            ORDER BY rank
            LIMIT ? OFFSET ?
        """, (search_term, per_page, offset))
    else:
        c.execute("SELECT COUNT(*) FROM images")
        total_images = c.fetchone()[0]
        
        c.execute("""
            SELECT id, marbleName, marbleOrigin, fileName, stainResistance, costRange, stoneColor, description, thermalExpansion 
            FROM images 
            ORDER BY id
            LIMIT ? OFFSET ?
        """, (per_page, offset))
    
    images = [dict(row) for row in c.fetchall()]
    for image in images:
        image['imageUrl'] = f'/api/image/{image["id"]}'
    
    conn.close()
    
    total_pages = math.ceil(total_images / per_page)
    
    response_data = {
        'marbles': images,
        'page': page,
        'perPage': per_page,
        'totalMarbles': total_images,
        'totalPages': total_pages
    }
    
    app.logger.info(f"Sending response for page {page}: {len(images)} marbles")
    return jsonify(response_data)

@app.route('/api/image/<int:image_id>')
def serve_image(image_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT image FROM images WHERE id = ?", (image_id,))
    result = c.fetchone()
    conn.close()

    if result:
        image_data = result[0]
        response = make_response(send_file(io.BytesIO(image_data), mimetype='image/png'))
        response.headers['Cache-Control'] = 'public, max-age=86400'
        return response
    else:
        return "Image not found", 404

@app.route('/api/featured-marbles', methods=['GET'])
def get_featured_marbles():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, marbleName, marbleOrigin, fileName, costRange, description FROM images WHERE featured = 1 LIMIT 3")
    marbles = []
    for row in c.fetchall():
        id, marble_name, marble_origin, file_name, costRange, description = row
        marbles.append({
            'id': id,
            'name': marble_name,
            'origin': marble_origin,
            'costRange': costRange if costRange else 'Price on request',
            'description': description if description else f'Beautiful {marble_name} from {marble_origin}',
            'imageUrl': f'/api/image/{id}'
        })
    conn.close()
    return jsonify(marbles)

@app.route('/api/marble/<int:marble_id>/vendors', methods=['GET'])
def get_marble_vendors(marble_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT v.id, v.name, v.contact, v.location, v.vendorLogo, v.url
        FROM vendors v
        JOIN marble_vendor_association mva ON v.id = mva.vendor_id
        WHERE mva.marble_id = ?
    """, (marble_id,))
    vendors = []
    for row in c.fetchall():
        vendor = {
            'id': row[0],
            'name': row[1],
            'contact': row[2],
            'location': row[3],
            'url': row[5]
        }
        if row[4]:
            vendor['vendorLogo'] = base64.b64encode(row[4]).decode('utf-8')
        else:
            vendor['vendorLogo'] = None
        vendors.append(vendor)
    conn.close()
    return jsonify(vendors)

@app.route('/3d')
def serve_3d_visualization():
    visualization_path = os.path.join(os.path.dirname(__file__), 'marble_embeddings_visualization_3d.html')
    if os.path.exists(visualization_path):
        response = make_response(send_file(visualization_path))
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' http://127.0.0.1:8000;"
        )
        return response
    else:
        return "3D visualization not found", 404

@app.after_request
def add_security_headers(response):
    if 'Content-Security-Policy' not in response.headers:
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' http://127.0.0.1:8000;"
        )
    return response

@app.route('/pixel.gif')
def tracking_pixel():
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    referrer = request.referrer
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    event = request.args.get('event', 'pageview')
    page = request.args.get('page', '')
    marble_id = request.args.get('marble_id', '')
    marble_name = request.args.get('marble_name', '')
    screen_resolution = request.args.get('sr', '')
    color_depth = request.args.get('cd', '')
    plugins = request.args.get('plugins', '')
    time_on_page = request.args.get('time', '')
    scroll_depth = request.args.get('scroll', '')

    log_entry = f"{timestamp} - IP: {ip_address}, User-Agent: {user_agent}, Referrer: {referrer}, Event: {event}, Page: {page}, Marble ID: {marble_id}, Marble Name: {marble_name}"
    app.logger.info(log_entry)

    detailed_log_entry = f"{timestamp} - IP: {ip_address}, User-Agent: {user_agent}, Referrer: {referrer}, Event: {event}, Page: {page}, Marble ID: {marble_id}, Marble Name: {marble_name}, Screen: {screen_resolution}, Color Depth: {color_depth}, Plugins: {plugins}, Time on Page: {time_on_page}, Scroll Depth: {scroll_depth}"
    app.logger.info(detailed_log_entry)

    response = make_response(generate_pixel())
    response.headers.set('Content-Type', 'image/gif')
    response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.headers.set('Pragma', 'no-cache')
    response.headers.set('Expires', '0')
    return response

if index is not None:
    num_vectors = index.ntotal
    dimension = index.d
    all_vectors = np.empty((num_vectors, dimension), dtype=np.float32)
    index.reconstruct_n(0, num_vectors, all_vectors)
    all_vectors_normalized = normalize(all_vectors)
else:
    print("FAISS index is not loaded. Similar marbles functionality will not work.")

@app.route('/api/expert', methods=['GET'])
def get_expert_info():
    expert_info = {
        "name": "Carlo Baraglia",
        "title": "Stone Expert",
        "bio": "Carlo Baraglia is a renowned stone expert with over 20 years of experience in the marble industry. His passion for natural stone and deep knowledge of various marble types have made him a sought-after consultant for architects, designers, and homeowners alike. Carlo's expertise spans from identifying rare marble varieties to advising on the best applications for different stone types.",
        "image_url": "/api/expert_image"
    }
    return jsonify(expert_info)

@app.route('/api/expert_image')
def serve_expert_image():
    image_path = os.path.join(current_dir, 'expert_image.jpg')
    return send_file(image_path, mimetype='image/jpeg')

def check_faiss_db_alignment():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM images")
    db_count = c.fetchone()[0]
    conn.close()

    faiss_count = index.ntotal if index is not None else 0

    print(f"Number of entries in FAISS index: {faiss_count}")
    print(f"Number of entries in SQLite database: {db_count}")

    if faiss_count == db_count:
        print("FAISS index and SQLite database are aligned.")
    else:
        print("WARNING: FAISS index and SQLite database are not aligned!")

check_faiss_db_alignment()

@app.route('/api/similar-marbles', methods=['POST'])
def get_similar_marbles():
    marble_id = request.json.get('marbleId')
    if marble_id is None:
        return jsonify({"error": "marbleId is required"}), 400

    try:
        marble_id = int(marble_id)
    except ValueError:
        return jsonify({"error": "Invalid marbleId"}), 400

    if index is None:
        return jsonify({"error": "FAISS index is not loaded"}), 500

    # Fetch the vector for the given marble_id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM images ORDER BY id")
    all_ids = [row[0] for row in c.fetchall()]
    conn.close()

    try:
        vector_index = all_ids.index(marble_id)
    except ValueError:
        return jsonify({"error": "Marble not found"}), 404

    vector = all_vectors_normalized[vector_index]

    # Search for similar marbles
    k = 5  # Number of similar marbles to return
    distances, indices = index.search(vector.reshape(1, -1), k + 1)

    similar_marbles = []
    for i in indices[0]:
        if i != vector_index:  # Exclude the query marble itself
            marble_id = get_marble_id_from_index(int(i))  # Ensure i is an integer
            if marble_id:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT id, marbleName, marbleOrigin, fileName FROM images WHERE id = ?", (marble_id,))
                result = c.fetchone()
                conn.close()
                if result:
                    similar_marbles.append({
                        "id": result[0],
                        "marbleName": result[1],
                        "marbleOrigin": result[2],
                        "imageUrl": f"/api/image/{result[0]}"
                    })

    return jsonify(similar_marbles)

# Load the pre-trained ResNet model

model = models.resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
model.eval()

# Global variables
model = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def initialize_model():
    global model
    model = models.resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
    model = torch.nn.Sequential(*list(model.children())[:-1])
    model.eval()
    model.to(device)


# Call this function when your app starts
initialize_model()

# Define image transformation
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def preprocess_image(image):
    # Convert to RGB if not already
    image = image.convert('RGB')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.0)  # Adjust this value as needed
    
    # Sharpen the image
    image = image.filter(ImageFilter.SHARPEN)
    
    # Apply a slight Gaussian blur to reduce noise
    image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # Convert to numpy array
    img_array = np.array(image)
    
    # Normalize pixel values
    img_array = img_array / 255.0
    
    # Clip values to ensure they're in [0, 1] range
    img_array = np.clip(img_array, 0, 1)
    
    # Convert back to PIL Image
    processed = Image.fromarray((img_array * 255).astype(np.uint8))
    
    return processed

def extract_features(image_data):
    # Open the image
    img = Image.open(io.BytesIO(image_data)).convert('RGB')
    # Preprocess the image
    preprocessed_img = preprocess_image(img)
    
    # Extract color histogram features
    img_color = preprocessed_img.resize((256, 256))
    img_array = np.array(img_color)
    # Calculate color histogram
    hist_r = np.histogram(img_array[:,:,0], bins=32, range=(0, 256))[0]
    hist_g = np.histogram(img_array[:,:,1], bins=32, range=(0, 256))[0]
    hist_b = np.histogram(img_array[:,:,2], bins=32, range=(0, 256))[0]
    
    # Concatenate histograms
    color_features = np.concatenate([hist_r, hist_g, hist_b])
    
    # Normalize the color features
    color_features = color_features / np.sum(color_features)
    
    # Extract ResNet features
    img_resnet = preprocessed_img.resize((224, 224))
    img_tensor = transform(img_resnet).unsqueeze(0).to(device)
    with torch.no_grad():
        resnet_features = model(img_tensor).squeeze().cpu().numpy()
    
    # Combine features with emphasis on color
    color_weight = 0.8 # Adjust this weight to change the emphasis on color
    resnet_weight = 1 - color_weight
    
    # Resize color_features to match resnet_features size
    color_features_resized = np.zeros(2048)
    color_features_resized[:96] = color_features
    
    combined_features = (color_weight * color_features_resized) + (resnet_weight * resnet_features)
    
    # Normalize the combined features
    combined_features = combined_features / np.linalg.norm(combined_features)
    
    return combined_features

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    try:
        app.logger.info("Received upload-image request")

        if index is None:
            app.logger.error("FAISS index is not loaded")
            return jsonify({"error": "FAISS index not loaded"}), 500

        if 'image' not in request.files:
            app.logger.error("No image file in request")
            return jsonify({"error": "No image file provided"}), 400

        file = request.files['image']
        if file.filename == '':
            app.logger.error("Empty filename")
            return jsonify({"error": "No selected file"}), 400

        if file:
            # Read the image file
            image_data = file.read()

            # Extract combined features
            combined_features = extract_features(image_data)

            # Ensure the features have the correct dimension
            if len(combined_features) != index.d:
                app.logger.error(
                    f"Feature dimension mismatch. Expected {index.d}, got {len(combined_features)}")
                return jsonify({"error": "Feature dimension mismatch"}), 500

            # Compare the combined features with the FAISS index
            D, I = index.search(np.array([combined_features]).astype('float32'), 20)

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            similar_marbles = []
            for i, idx in enumerate(I[0]):
                c.execute(
                    "SELECT id FROM images ORDER BY id LIMIT 1 OFFSET ?", (int(idx),))
                result = c.fetchone()
                if result:
                    db_id = result[0]
                    c.execute(
                        "SELECT id, marbleName, marbleOrigin, fileName, stoneColor, stainResistance, costRange, description, thermalExpansion FROM images WHERE id = ?",
                        (db_id,))
                    marble = c.fetchone()
                    if marble:
                        # Calculate similarity (using cosine similarity)
                        marble_vector = all_vectors_normalized[idx]
                        similarity = np.dot(combined_features, marble_vector) / (np.linalg.norm(combined_features) * np.linalg.norm(marble_vector))

                        similar_marbles.append({
                            'id': marble[0],
                            'marbleName': marble[1],
                            'marbleOrigin': marble[2],
                            'fileName': marble[3],
                            'stoneColor': marble[4],
                            'stainResistance': marble[5],
                            'costRange': marble[6],
                            'description': marble[7],
                            'thermalExpansion': marble[8],
                            'imageUrl': f'/api/image/{marble[0]}',
                            'similarity': float(similarity)
                        })

            conn.close()

            # Sort by similarity and get top 6
            similar_marbles = sorted(
                similar_marbles,
                key=lambda x: x['similarity'],
                reverse=True)[:6]

            app.logger.info(f"Returning {len(similar_marbles)} similar marbles")
            return jsonify(similar_marbles)

    except Exception as e:
        app.logger.error(f"Error in upload_image: {str(e)}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Add this function at the top of your file or in a utils module


def normalize_l2(x):
    x = np.array(x)
    if x.ndim == 1:
        norm = np.linalg.norm(x)
        if norm == 0:
            return x
        return x / norm
    else:
        norm = np.linalg.norm(x, 2, axis=1, keepdims=True)
        return np.where(norm == 0, x, x / norm)


def rebuild_combined_index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, image FROM images")
    
    combined_features = []
    for id, image_data in c.fetchall():
        features = extract_features(image_data)
        combined_features.append(features)
    
    combined_features = np.array(combined_features)
    
    global index, all_vectors_normalized
    index = faiss.IndexFlatL2(2048)  # Use 2048 dimensions for combined features
    index.add(combined_features.astype('float32'))
    all_vectors_normalized = normalize(combined_features)
    
    faiss.write_index(index, index_path)
    
    conn.close()

   

@app.route('/log_event', methods=['POST'])
def log_event():
    event_data = request.json
    # Log the event (you can customize this part based on your logging needs)
    app.logger.info(f"Event logged: {event_data}")
    return jsonify({"status": "success", "message": "Event logged successfully"})