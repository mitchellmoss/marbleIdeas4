import faiss
import numpy as np
from sklearn.manifold import TSNE
import plotly.graph_objects as go
import os
import sqlite3
import json
import trace


# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (backend)
backend_dir = os.path.dirname(current_dir)

# Construct absolute paths for the required files
index_path = os.path.join(backend_dir, "marble_image_index.faiss")
db_path = os.path.join(backend_dir, "marble_images-2.db")

# Load the FAISS index
try:
    index = faiss.read_index(index_path)
except RuntimeError as e:
    print(f"Error: Unable to read the FAISS index file at {index_path}")
    print(f"Make sure the file exists and you have the necessary permissions.")
    print(f"Original error: {str(e)}")
    exit(1)

# Connect to the SQLite database
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
except sqlite3.Error as e:
    print(f"Error connecting to the database: {e}")
    exit(1)

# Fetch marble data from the database (without images)
try:
    cursor.execute("SELECT id, marbleName FROM images")
    marble_data = cursor.fetchall()
except sqlite3.Error as e:
    print(f"Error fetching data from the database: {e}")
    exit(1)

# Prepare hover text, marble names, and IDs
hover_texts = []
marble_names = []
marble_ids = []

for id, name in marble_data:
    hover_texts.append(f"Marble: {name}")
    marble_names.append(name)
    marble_ids.append(id)

# Extract vectors from the index
num_vectors = index.ntotal
dimension = index.d
vectors = np.empty((num_vectors, dimension), dtype=np.float32)
index.reconstruct_n(0, num_vectors, vectors)

# Perform t-SNE for 3D visualization
tsne = TSNE(n_components=3, random_state=42)
vectors_3d = tsne.fit_transform(vectors)

# Create a color map
unique_marbles = list(set(marble_names))
color_indices = [unique_marbles.index(name) for name in marble_names]

# Create an empty trace for highlighted points
highlight_trace = go.Scatter3d(
    x=[],
    y=[],
    z=[],
    mode='markers',
    marker=dict(
        size=8,
        color='red',
        symbol='circle',
        line=dict(color='rgb(204, 204, 204)', width=1),
        opacity=1
    ),
    hoverinfo='skip',
    showlegend=False
)

# Create the layout
layout = go.Layout(
    scene=dict(
        xaxis_title='t-SNE feature 1',
        yaxis_title='t-SNE feature 2',
        zaxis_title='t-SNE feature 3'
    ),
    title='3D Visualization of Marble Image Embeddings',
    hovermode='closest'
)


# Create the 3D scatter plot
trace = go.Scatter3d(
    x=vectors_3d[:, 0],
    y=vectors_3d[:, 1],
    z=vectors_3d[:, 2],
    mode='markers',
    marker=dict(
        size=5,
        color=color_indices,
        colorscale='Viridis',
        opacity=0.8
    ),
    text=hover_texts,
    hoverinfo='text',
    customdata=marble_ids
)

# Create the layout
layout = go.Layout(
    scene=dict(
        xaxis_title='t-SNE feature 1',
        yaxis_title='t-SNE feature 2',
        zaxis_title='t-SNE feature 3'
    ),
    title='3D Visualization of Marble Image Embeddings',
    hovermode='closest'
)



# Create the figure with both traces
fig = go.Figure(data=[trace, highlight_trace], layout=layout)

# Convert the figure to JSON
plot_json = fig.to_json()

# Create a dictionary mapping marble names to their IDs and vector indices
marble_name_to_id = {name: id for name, id in zip(marble_names, marble_ids)}
marble_name_to_index = {name: idx for idx, name in enumerate(marble_names)}

# Create JSON data for marble names, their mappings, and vectors
marble_data_json = json.dumps({
    "marbleNames": marble_names,
    "marbleNameToId": marble_name_to_id,
    "marbleNameToIndex": marble_name_to_index,
    "vectors": vectors.tolist()  # Add this line to include the vectors
})

# HTML template
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Visualization of Marble Image Embeddings</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
    <style>
        #plotly-div {{
            width: 100%;
            height: 800px;
            position: relative;
        }}
        #custom-hover {{
            display: none;
            position: fixed;
            background: white;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            pointer-events: none;
            z-index: 1000;
        }}
        #search-container {{
            margin-bottom: 20px;
        }}
        #search-results {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .result-item {{
            text-align: center;
        }}
        .result-item img {{
            width: 100px;
            height: 100px;
            object-fit: cover;
        }}
    </style>
</head>
<body>
    <div id="search-container">
        <input type="text" id="search-input" placeholder="Search for marble names">
        <button id="search-button">Search</button>
    </div>
    <div id="search-results"></div>
    <div id="plotly-div"></div>
    <div id="custom-hover">
        <p id="hover-text"></p>
        <img id="hover-image" src="" alt="Marble Image" style="width:100px;height:100px;object-fit:cover;">
    </div>
    <script>
        var plotlyDiv = document.getElementById('plotly-div');
        var customHover = document.getElementById('custom-hover');
        var hoverText = document.getElementById('hover-text');
        var hoverImage = document.getElementById('hover-image');
        var plotData = {plot_json};
        var marbleData = {marble_data_json};
        
        Plotly.newPlot(plotlyDiv, plotData.data, plotData.layout);

        var imageCache = {{}};
        var loadingImage = 'data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=='; // 1x1 transparent GIF

        plotlyDiv.on('plotly_hover', function(data) {{
            var point = data.points[0];
            var marbleId = point.customdata;
            
            hoverText.textContent = point.text;
            hoverImage.src = loadingImage;
            hoverImage.setAttribute('data-id', marbleId);
            
            if (imageCache[marbleId]) {{
                hoverImage.src = imageCache[marbleId];
            }} else {{
                fetch('http://127.0.0.1:8000/api/image/' + marbleId)
                    .then(response => response.blob())
                    .then(blob => {{
                        var url = URL.createObjectURL(blob);
                        imageCache[marbleId] = url;
                        if (hoverImage.getAttribute('data-id') === marbleId) {{
                            hoverImage.src = url;
                        }}
                    }})
                    .catch(error => console.error('Error:', error));
            }}
            
            customHover.style.display = 'block';
            customHover.style.left = (point.x + 10) + 'px';
            customHover.style.top = (point.y + 10) + 'px';
        }});

        plotlyDiv.on('plotly_unhover', function() {{
            customHover.style.display = 'none';
        }});

        // Clear image cache when it gets too large
        setInterval(function() {{
            var cacheSize = Object.keys(imageCache).length;
            if (cacheSize > 100) {{
                imageCache = {{}};
            }}
        }}, 60000); // Check every minute

        // Search functionality
        document.getElementById('search-button').addEventListener('click', performSearch);
        document.getElementById('search-input').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                performSearch();
            }}
        }});

         async function performSearch() {{
            var searchTerm = document.getElementById('search-input').value.toLowerCase();
            var searchVector = await getSearchVector(searchTerm);
            var results = findSimilarMarbles(searchVector, 5);
            displaySearchResults(results);
            highlightPoints(results);
        }}

        async function getSearchVector(searchTerm) {{
            // This is a placeholder function. In a real-world scenario, you would send the search term to your backend
            // and get the corresponding vector. For now, we'll just use the vector of the first matching marble.
            var matchingMarble = marbleData.marbleNames.find(name => name.toLowerCase().includes(searchTerm));
            if (matchingMarble) {{
                return tf.tensor(marbleData.vectors[marbleData.marbleNameToIndex[matchingMarble]]);
            }}
            return tf.zeros([{dimension}]);
        }}

        function findSimilarMarbles(searchVector, numResults) {{
            var allVectors = tf.tensor2d(marbleData.vectors);
            var similarities = tf.matMul(allVectors, searchVector.reshape([{dimension}, 1])).squeeze();
            var topIndices = tf.topk(similarities, numResults).indices.arraySync();
            return topIndices.map(index => marbleData.marbleNames[index]);
        }}

         function highlightPoints(results) {{
            var indices = results.map(name => marbleData.marbleNameToIndex[name]);
            var x = indices.map(i => plotData.data[0].x[i]);
            var y = indices.map(i => plotData.data[0].y[i]);
            var z = indices.map(i => plotData.data[0].z[i]);

            Plotly.restyle(plotlyDiv, {{
                x: [x],
                y: [y],
                z: [z]
            }}, 1);
        }}

        function displaySearchResults(results) {{
            var searchResults = document.getElementById('search-results');
            searchResults.innerHTML = '';
            results.forEach(name => {{
                var marbleId = marbleData.marbleNameToId[name];
                var resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                var img = document.createElement('img');
                img.src = loadingImage;
                img.alt = name;
                var nameElem = document.createElement('p');
                nameElem.textContent = name;
                resultItem.appendChild(img);
                resultItem.appendChild(nameElem);
                searchResults.appendChild(resultItem);

                if (imageCache[marbleId]) {{
                    img.src = imageCache[marbleId];
                }} else {{
                    fetch('http://127.0.0.1:8000/api/image/' + marbleId)
                        .then(response => response.blob())
                        .then(blob => {{
                            var url = URL.createObjectURL(blob);
                            imageCache[marbleId] = url;
                            img.src = url;
                        }})
                        .catch(error => console.error('Error:', error));
                }}
            }});
        }}
    </script>
</body>
</html>
"""

# Save the interactive plot as an HTML file
output_path = os.path.join(backend_dir, 'marble_embeddings_visualization_3d.html')
with open(output_path, 'w') as f:
    f.write(html_template.format(plot_json=plot_json, marble_data_json=marble_data_json, dimension=dimension))

print(f"Interactive 3D visualization saved as '{output_path}'")

# Close the database connection
conn.close()