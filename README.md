# Marble Gallery

Marble Gallery is a web application showcasing a curated collection of exquisite marbles from around the world. This project combines a React frontend with a Python backend to create an interactive and visually appealing marble browsing experience.

### DATABASE SCHEMA

```
CREATE TABLE IF NOT EXISTS "images" (
        "id"    INTEGER,
        "image" BLOB,
        "marbleName"    TEXT,
        "marbleOrigin"  TEXT,
        "fileName"      TEXT,
        "stainResistance"       TEXT,
        "costRange"     DECIMAL(10, 2),
        "stoneColor"    TEXT,
        "featured"      INTEGER DEFAULT 0,
        "description"   TEXT,
        "thermalExpansion"      REAL,
        "cleaningTips"  TEXT, Rarity INTEGER CHECK(Rarity >= 1 AND Rarity <= 10), associatedVendor TEXT,
        PRIMARY KEY("id")
);
CREATE TABLE vendors (id INTEGER PRIMARY KEY AUTOINCREMENT, location TEXT NOT NULL,  INTEGER, contact TEXT, vendorLogo BLOB, name TEXT, url TEXT);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE marble_vendor_association (
    marble_id INTEGER,
    vendor_id INTEGER,
    FOREIGN KEY (marble_id) REFERENCES [marble_images-2](id),
    FOREIGN KEY (vendor_id) REFERENCES vendors(id),
    PRIMARY KEY (marble_id, vendor_id)
);
CREATE VIRTUAL TABLE images_fts USING fts5(
    id, marbleName, marbleOrigin, fileName, stainResistance, costRange, stoneColor, description, thermalExpansion,
    content='images', content_rowid='id'
)
/* images_fts(id,marbleName,marbleOrigin,fileName,stainResistance,costRange,stoneColor,description,thermalExpansion) */;
CREATE TABLE IF NOT EXISTS 'images_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'images_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'images_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'images_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TRIGGER images_ai AFTER INSERT ON images BEGIN
  INSERT INTO images_fts(id, marbleName, marbleOrigin, fileName, stainResistance, costRange, stoneColor, description, thermalExpansion)
  VALUES (new.id, new.marbleName, new.marbleOrigin, new.fileName, new.stainResistance, new.costRange, new.stoneColor, new.description, new.thermalExpansion);
END;
CREATE TRIGGER images_ad AFTER DELETE ON images BEGIN
  INSERT INTO images_fts(images_fts, id, marbleName, marbleOrigin, fileName, stainResistance, costRange, stoneColor, description, thermalExpansion)
  VALUES('delete', old.id, old.marbleName, old.marbleOrigin, old.fileName, old.stainResistance, old.costRange, old.stoneColor, old.description, old.thermalExpansion);
END;
CREATE TRIGGER images_au AFTER UPDATE ON images BEGIN
  INSERT INTO images_fts(images_fts, id, marbleName, marbleOrigin, fileName, stainResistance, costRange, stoneColor, description, thermalExpansion)
  VALUES('delete', old.id, old.marbleName, old.marbleOrigin, old.fileName, old.stainResistance, old.costRange, old.stoneColor, old.description, old.thermalExpansion);
  INSERT INTO images_fts(id, marbleName, marbleOrigin, fileName, stainResistance, costRange, stoneColor, description, thermalExpansion)
  VALUES (new.id, new.marbleName, new.marbleOrigin, new.fileName, new.stainResistance, new.costRange, new.stoneColor, new.description, new.thermalExpansion);
END;
```
## Features

- Interactive marble gallery with detailed information
- Admin dashboard for analytics and data visualization
- Responsive design for various screen sizes
- Dark mode support
- Real-time user interaction tracking

## Tech Stack

- Frontend: React, Tailwind CSS
- Backend: Python (Flask)
- Database: SQLite
- Analytics: Plotly.js
- Production Server: Gunicorn

## Getting Started

### Prerequisites

- Node.js and npm
- Python 3.x
- pip
- Gunicorn

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/marble-gallery.git
   cd marble-gallery
   ```

2. Set up the frontend:
   ```
   cd frontend/marble-gallery
   npm install
   ```

3. Set up the backend:
   ```
   cd ../../backend
   pip install -r requirements.txt
   ```

4. Install Gunicorn:
   ```
   pip install gunicorn
   ```

### Running the Application

1. Start the backend production server using Gunicorn:
   ```
   cd backend
   gunicorn --workers 4 --bind 0.0.0.0:5000 server_production:app
   ```
   This command starts Gunicorn with 4 worker processes, binding to all network interfaces on port 5000. Adjust the number of workers and port as needed.

2. In a new terminal, start the frontend development server:
   ```
   cd frontend/marble-gallery
   npm start
   ```

3. Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
marble-gallery/
├── frontend/
│   └── marble-gallery/
│       ├── public/
│       └── src/
│           ├── components/
│           ├── pages/
│           └── styles/
├── backend/
│   ├── templates/
│   └── server_production.py
└── README.md
```

## Key Components

### MarbleGallery Component

The main component for displaying the marble collection:

```javascript:frontend/marble-gallery/src/marbleGallery.js
import axios from 'axios';
import React, { useState, useEffect, useRef, useCallback } from 'react';

const Modal = ({ isOpen, onClose, children }) => {
  if (!isOpen) return null;

  const handleOutsideClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={handleOutsideClick}
    >
      <div className="bg-white p-4 rounded-lg max-w-3xl max-h-[90vh] overflow-auto">
        <button onClick={onClose} className="float-right text-2xl">&times;</button>
        {children}
      </div>
    </div>
  );
};

// ... rest of the component code ...
```

### Admin Dashboard

An analytics dashboard for administrators:

```html:backend/templates/admin_dashboard.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marble Gallery Admin Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            margin: 0;
            padding: 0;
            background-color: #121212;
            color: #0f0e0e;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .dashboard-header {
            background: linear-gradient(135deg, #4a5568, #2d3748);
            color: #e0e0e0;
            padding: 30px 0;
            text-align: center;
            border-radius: 15px;
            margin-bottom: 40px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }
        h1 {
            font-size: 2.5em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        .graph-container {
            /* ... additional styles ... */
        }
    </style>
</head>
<body>
    <!-- ... rest of the HTML content ... -->
</body>
</html>
```

## Production Deployment

For production deployment, it's recommended to use Gunicorn as the WSGI HTTP server. Here are some additional considerations:

1. Set up a reverse proxy (e.g., Nginx) to handle client requests and forward them to Gunicorn.
2. Configure your firewall to allow traffic on the necessary ports.
3. Set up SSL/TLS certificates for secure HTTPS connections.
4. Use environment variables for sensitive information like database credentials and API keys.
5. Implement proper logging and monitoring for the production environment.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
