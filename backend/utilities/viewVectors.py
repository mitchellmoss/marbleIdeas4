import faiss
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import random
import os

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (backend)
backend_dir = os.path.dirname(current_dir)

# Construct absolute paths for the required files
index_path = os.path.join(backend_dir, "marble_image_index.faiss")
names_path = os.path.join(backend_dir, "marble_names.txt")

# Load the FAISS index
try:
    index = faiss.read_index(index_path)
except RuntimeError as e:
    print(f"Error: Unable to read the FAISS index file at {index_path}")
    print(f"Make sure the file exists and you have the necessary permissions.")
    print(f"Original error: {str(e)}")
    exit(1)

# Load marble names
try:
    with open(names_path, "r") as f:
        marble_names = [line.strip() for line in f]
except FileNotFoundError:
    print(f"Error: Unable to find the marble names file at {names_path}")
    print("Make sure the file exists and you have the necessary permissions.")
    exit(1)

# Extract vectors from the index
num_vectors = index.ntotal
dimension = index.d
vectors = np.empty((num_vectors, dimension), dtype=np.float32)
index.reconstruct_n(0, num_vectors, vectors)

# Perform t-SNE
tsne = TSNE(n_components=2, random_state=42)
vectors_2d = tsne.fit_transform(vectors)

# Create a color map
unique_marbles = list(set(marble_names))
color_map = plt.cm.get_cmap('tab20')
color_indices = [unique_marbles.index(name) for name in marble_names]

# Create the plot
plt.figure(figsize=(20, 16))
scatter = plt.scatter(vectors_2d[:, 0], vectors_2d[:, 1], c=color_indices, cmap=color_map, alpha=0.6)

# Add labels for a random subset of points
num_labels = min(50, num_vectors)  # Adjust this number to show more or fewer labels
random_indices = random.sample(range(num_vectors), num_labels)
for idx in random_indices:
    plt.annotate(marble_names[idx], (vectors_2d[idx, 0], vectors_2d[idx, 1]), fontsize=8)

# Add a color bar
plt.colorbar(scatter, label='Marble Types', ticks=range(len(unique_marbles)))
plt.clim(-0.5, len(unique_marbles) - 0.5)

# Set labels and title
plt.xlabel('t-SNE feature 1')
plt.ylabel('t-SNE feature 2')
plt.title('2D Visualization of Marble Image Embeddings')

# Save the plot
plt.savefig('marble_embeddings_visualization.png', dpi=300, bbox_inches='tight')
plt.close()

print("Visualization saved as 'marble_embeddings_visualization.png'")