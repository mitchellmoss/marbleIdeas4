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

# Define image transformation
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Fetch all images and marble names from the database
cursor.execute("SELECT marbleName, image FROM images")
rows = cursor.fetchall()

# Lists to store embeddings and corresponding marble names
embeddings = []
marble_names = []

# Process each image and compute its embedding
for marble_name, img_data in rows:
    try:
        # Convert binary data to PIL Image
        img = Image.open(io.BytesIO(img_data))
        
        # Convert grayscale images to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Apply transformations and compute embedding
        img_tensor = transform(img).unsqueeze(0)
        with torch.no_grad():
            embedding = model(img_tensor).squeeze().numpy()
        
        embeddings.append(embedding)
        marble_names.append(marble_name)
    except Exception as e:
        print(f"Error processing image for {marble_name}: {str(e)}")

# Convert embeddings list to a numpy array
embeddings_array = np.array(embeddings).astype('float32')

# Normalize the vectors
faiss.normalize_L2(embeddings_array)

# Create a FAISS index
dimension = embeddings_array.shape[1]  # Dimension of the embedding vectors
index = faiss.IndexFlatIP(dimension)  # Using Inner Product similarity

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