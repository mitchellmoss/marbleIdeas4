import sqlite3
import io
from PIL import Image
import torch
import torchvision.transforms as transforms
import torchvision.models as models
import faiss
import numpy as np

# Connect to the SQLite database
conn = sqlite3.connect('marble_images-2.db')
cursor = conn.cursor()

# Load a pre-trained ResNet model
model = models.resnet50(pretrained=True)
model = torch.nn.Sequential(*list(model.children())[:-1])  # Remove the last fully connected layer
model.eval()

# Define image transformation for ResNet
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def extract_features(img_data):
    # Extract color histogram features
    img = Image.open(io.BytesIO(img_data)).convert('RGB')
    img_color = img.resize((64, 64))  # Resize for color histogram
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
    img_resnet = img.resize((224, 224))
    img_tensor = transform(img_resnet).unsqueeze(0)
    with torch.no_grad():
        resnet_features = model(img_tensor).squeeze().numpy()
    
    # Combine features with emphasis on color
    color_weight = 0.7  # Adjust this weight to change the emphasis on color
    resnet_weight = 1 - color_weight
    
    # Resize color_features to match resnet_features size
    color_features_resized = np.zeros(2048)
    color_features_resized[:96] = color_features
    
    combined_features = (color_weight * color_features_resized) + (resnet_weight * resnet_features)
    
    # Normalize the combined features
    combined_features = combined_features / np.linalg.norm(combined_features)
    
    return combined_features

# Fetch all images and marble names from the database
cursor.execute("SELECT marbleName, image FROM images")
rows = cursor.fetchall()

# Lists to store embeddings and corresponding marble names
embeddings = []
marble_names = []

# Process each image and compute its embedding
for marble_name, img_data in rows:
    try:
        combined_features = extract_features(img_data)
        embeddings.append(combined_features)
        marble_names.append(marble_name)
    except Exception as e:
        print(f"Error processing image for {marble_name}: {str(e)}")

# Convert embeddings list to a numpy array
embeddings_array = np.array(embeddings).astype('float32')

# Create a FAISS index
dimension = embeddings_array.shape[1]  # Dimension of the embedding vectors
index = faiss.IndexFlatL2(dimension)  # Using L2 distance for similarity

# Add vectors to the index
index.add(embeddings_array)

# Save the index to a file
faiss.write_index(index, "marble_image_index.faiss")

# Save marble names to a separate file
with open("marble_names.txt", "w") as f:
    for name in marble_names:
        f.write(f"{name}\n")

print(f"Vector database created with {len(marble_names)} images.")

# Close the database connection
conn.close()