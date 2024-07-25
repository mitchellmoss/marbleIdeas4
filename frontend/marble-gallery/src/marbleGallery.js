import axios from 'axios';
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useMarbleGallery } from './MarbleGalleryContext';
import { useNavigate } from 'react-router-dom';
import { debounce } from 'lodash';
import CircularProgress from '@mui/material/CircularProgress';

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

// THIS IS FOR THE ONLICK MODAL IMAGE
const WatermarkedImage = ({ src, alt, className }) => {
  const canvasRef = useRef(null);
  const imgRef = useRef(null);

  const drawImageOnCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = imgRef.current;

    canvas.width = img.width;
    canvas.height = img.height;

    // Draw the original image
    ctx.drawImage(img, 0, 0, img.width, img.height);

    // Apply watermark
    ctx.font = '16px Arial';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.02)'; // Semi-transparent white
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    const watermarkText = 'Marble.Boston';
    const tileSize = 150; // Size of each watermark tile

    // Tile the watermark across the image
    for (let x = 0; x < canvas.width; x += tileSize) {
      for (let y = 0; y < canvas.height; y += tileSize) {
        ctx.save();
        ctx.translate(x + tileSize / 2, y + tileSize / 2);
        ctx.rotate(-Math.PI / 4); // Rotate 45 degrees
        ctx.fillText(watermarkText, 0, 0);
        ctx.restore();
      }
    }

    // Apply a simple obfuscation effect (you can customize this)
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;
    for (let i = 0; i < data.length; i += 4) {
      data[i] = data[i] ^ 1; // XOR operation on red channel
    }
    ctx.putImageData(imageData, 0, 0);
  }, []);

  const handleImageLoad = () => {
    drawImageOnCanvas();
  };

  return (
    <>
      <canvas
        ref={canvasRef}
        className={className}
      />
      <img
        ref={imgRef}
        src={src}
        alt={alt}
        className="hidden"
        onLoad={handleImageLoad}
      />
    </>
  );
};

  const MarbleCard = ({ marble, onImageClick }) => {
    const [isVisible, setIsVisible] = useState(false);
    const [imageLoaded, setImageLoaded] = useState(false);
    const [imageDataUrl, setImageDataUrl] = useState('');
    const canvasRef = useRef(null);
    const imgRef = useRef(null);
    const observerRef = useRef(null);
  
    const fetchImageAsDataUrl = useCallback(async () => {
      if (imageDataUrl) return; // Prevent refetching if we already have the data URL
      try {
        const response = await fetch(marble.imageUrl);
        const blob = await response.blob();
        const dataUrl = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.readAsDataURL(blob);
        });
        setImageDataUrl(dataUrl);
      } catch (error) {
        console.error('Error fetching image:', error);
      }
    }, [marble.imageUrl, imageDataUrl]);
  
    // THIS IS FOR THE MAIN GALLERY ONLY
    const drawImageOnCanvas = useCallback(() => {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const img = imgRef.current;
    
      canvas.width = img.width;
      canvas.height = img.height;
    
      // Draw the original image
      ctx.drawImage(img, 0, 0, img.width, img.height);
    
      // Apply watermark
      ctx.font = '16px Arial';
      ctx.fillStyle = 'rgba(255, 255, 255, 0.02)'; // Semi-transparent white
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
    
      const watermarkText = 'Marble.Boston';
      const tileSize = 150; // Size of each watermark tile
    
      // Tile the watermark across the image
      for (let x = 0; x < canvas.width; x += tileSize) {
        for (let y = 0; y < canvas.height; y += tileSize) {
          ctx.save();
          ctx.translate(x + tileSize / 2, y + tileSize / 2);
          ctx.rotate(-Math.PI / 4); // Rotate 45 degrees
          ctx.fillText(watermarkText, 0, 0);
          ctx.restore();
        }
      }

      
    
      // Apply a simple obfuscation effect (you can customize this)
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;
      for (let i = 0; i < data.length; i += 4) {
        data[i] = data[i] ^ 1; // XOR operation on red channel
      }
      ctx.putImageData(imageData, 0, 0);
    }, []);
  
    useEffect(() => {
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            fetchImageAsDataUrl();
            observer.unobserve(entry.target);
          }
        },
        { threshold: 0.1 }
      );
  
      observerRef.current = observer;
  
      if (canvasRef.current) {
        observer.observe(canvasRef.current);
      }
  
      return () => {
        if (observerRef.current && canvasRef.current) {
          observerRef.current.unobserve(canvasRef.current);
        }
      };
    }, [marble.id, fetchImageAsDataUrl]);
  
    const handleImageLoad = () => {
      setImageLoaded(true);
      drawImageOnCanvas();
    };
  
    const handleMarbleClick = () => {
      // Tracking pixel for marble click
      const trackingData = new URLSearchParams({
        event: 'marble_click',
        marble_id: marble.id.toString(),
        marble_name: marble.marbleName,
        page: window.location.pathname,
        sr: `${window.screen.width}x${window.screen.height}`,
        cd: window.screen.colorDepth.toString(),
        plugins: Array.from(navigator.plugins).map(p => p.name).join(','),
        time: Date.now().toString()
      }).toString();

      const img = new Image();
      img.src = `/pixel.gif?${trackingData}`;
      
      onImageClick(marble);
    };
  
    return (
      
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div
          className="w-full h-48 bg-gray-200 relative cursor-pointer"
          onClick={handleMarbleClick}
        >
          <canvas
            ref={canvasRef}
            className="w-full h-full object-cover"
          />
          {isVisible && imageDataUrl && (
            <img
              ref={imgRef}
              src={imageDataUrl}
              alt={marble.marbleName}
              className="hidden"
              onLoad={handleImageLoad}
            />
          )}
          {isVisible && !imageLoaded && (
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-gray-400">Loading...</span>
            </div>
          )}
        </div>
        <div className="p-4">
          <h2 className="text-xl font-semibold mb-2">{marble.marbleName}</h2>
          <p className="text-gray-600">Type / Origin: {marble.marbleOrigin}</p>
        </div>
      </div>
    );
  };

  const ExpandableDescription = React.memo(({ description }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const previewLength = 100;
  
    const toggleExpand = useCallback(() => {
      setIsExpanded(prevState => !prevState);
    }, []);
  
    if (!description) {
      return (
        <div className="mt-4">
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Description</h3>
          <p className="text-gray-700">No description available.</p>
        </div>
      );
    }
  
    return (
      <div className="mt-4">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Description</h3>
        <p className="text-gray-700">
          {isExpanded ? description : `${description.slice(0, previewLength)}...`}
        </p>
        {description.length > previewLength && (
          <button
            onClick={toggleExpand}
            className="mt-2 text-indigo-600 hover:text-indigo-800 focus:outline-none"
          >
            {isExpanded ? 'Show less' : 'Read more'}
          </button>
        )}
      </div>
      
    );
  });
  
  const ColorSquare = ({ color, onClick }) => {
    // Function to convert RGB to LAB
    const rgbToLab = (r, g, b) => {
      let [x, y, z] = rgbToXyz(r, g, b);
      return xyzToLab(x, y, z);
    };
  
    const rgbToXyz = (r, g, b) => {
      r = r / 255;
      g = g / 255;
      b = b / 255;
  
      r = r > 0.04045 ? Math.pow((r + 0.055) / 1.055, 2.4) : r / 12.92;
      g = g > 0.04045 ? Math.pow((g + 0.055) / 1.055, 2.4) : g / 12.92;
      b = b > 0.04045 ? Math.pow((b + 0.055) / 1.055, 2.4) : b / 12.92;
  
      r = r * 100;
      g = g * 100;
      b = b * 100;
  
      const x = r * 0.4124 + g * 0.3576 + b * 0.1805;
      const y = r * 0.2126 + g * 0.7152 + b * 0.0722;
      const z = r * 0.0193 + g * 0.1192 + b * 0.9505;
  
      return [x, y, z];
    };
  
    const xyzToLab = (x, y, z) => {
      x = x / 95.047;
      y = y / 100.0;
      z = z / 108.883;
  
      x = x > 0.008856 ? Math.pow(x, 1 / 3) : (7.787 * x) + (16 / 116);
      y = y > 0.008856 ? Math.pow(y, 1 / 3) : (7.787 * y) + (16 / 116);
      z = z > 0.008856 ? Math.pow(z, 1 / 3) : (7.787 * z) + (16 / 116);
  
      const l = (116 * y) - 16;
      const a = 500 * (x - y);
      const b = 200 * (y - z);
  
      return [l, a, b];
    };
  
    // CIEDE2000 Color Difference formula with weights
    const ciede2000 = (lab1, lab2, weights) => {
      const [L1, a1, b1] = lab1;
      const [L2, a2, b2] = lab2;
  
      const kL = 1;
      const kC = 1;
      const kH = 1;
  
      const deltaL = L2 - L1;
      const L_ = (L1 + L2) / 2;
  
      const C1 = Math.sqrt(a1 * a1 + b1 * b1);
      const C2 = Math.sqrt(a2 * a2 + b2 * b2);
      const C_ = (C1 + C2) / 2;
  
      const G = 0.5 * (1 - Math.sqrt(Math.pow(C_, 7) / (Math.pow(C_, 7) + Math.pow(25, 7))));
  
      const a1_ = a1 * (1 + G);
      const a2_ = a2 * (1 + G);
  
      const C1_ = Math.sqrt(a1_ * a1_ + b1 * b1);
      const C2_ = Math.sqrt(a2_ * a2_ + b2 * b2);
      const deltaC = C2_ - C1_;
  
      const h1_ = Math.atan2(b1, a1_);
      const h2_ = Math.atan2(b2, a2_);
  
      const deltaH = 2 * Math.sqrt(C1_ * C2_) * Math.sin((h2_ - h1_) / 2);
  
      const L_50 = Math.pow(L_ - 50, 2);
      const SL = 1 + (0.015 * L_50) / Math.sqrt(20 + L_50);
      const SC = 1 + 0.045 * C_;
      const SH = 1 + 0.015 * C_ * (1 - 0.17 * Math.cos(h1_ - Math.PI / 6) + 0.24 * Math.cos(2 * h1_) + 0.32 * Math.cos(3 * h1_ + Math.PI / 30) - 0.20 * Math.cos(4 * h1_ - 63 * Math.PI / 180));
  
      const deltaTheta = 30 * Math.exp(-Math.pow((h1_ - 275) / 25, 2));
      const RC = 2 * Math.sqrt(Math.pow(C_, 7) / (Math.pow(C_, 7) + Math.pow(25, 7)));
      const RT = -RC * Math.sin(2 * deltaTheta);
  
      const deltaE = Math.sqrt(Math.pow(deltaL / (kL * SL), 2) + Math.pow(deltaC / (kC * SC), 2) + Math.pow(deltaH / (kH * SH), 2) + RT * (deltaC / (kC * SC)) * (deltaH / (kH * SH)));
  
      // Apply weights
      const weightedDeltaE = deltaE * weights;
  
      return weightedDeltaE;
    };
  
    const getApproximateColor = (hexColor) => {
      const r = parseInt(hexColor.slice(1, 3), 16);
      const g = parseInt(hexColor.slice(3, 5), 16);
      const b = parseInt(hexColor.slice(5, 7), 16);
  
      //lower is more sensitive
      const colors = [
        { name: 'Red', letter: 'R', rgb: [255, 0, 0], weight: 1.5 },
        { name: 'Green', letter: 'G', rgb: [0, 255, 0], weight: 1.3 },
        { name: 'Blue', letter: 'B', rgb: [0, 0, 255], weight: 1.3 },
        { name: 'Yellow', letter: 'Y', rgb: [255, 255, 0], weight: 1.4 },
        { name: 'Black', letter: 'Bk', rgb: [0, 0, 0], weight: 10.0 },
        { name: 'White', letter: 'W', rgb: [255, 255, 255], weight: 2.5 },
      ];
  
      const lab1 = rgbToLab(r, g, b);
  
      let closestColor = colors[0];
      let minDistance = Infinity;
  
      colors.forEach((c) => {
        const lab2 = rgbToLab(...c.rgb);
        const distance = ciede2000(lab1, lab2, c.weight);
        if (distance < minDistance) {
          minDistance = distance;
          closestColor = c;
        }
      });
  
      return closestColor;
    };
  
    const approximateColor = getApproximateColor(color);
  
    return (
      <div
        className="w-6 h-6 inline-flex items-center justify-center mr-2 text-xs font-bold text-white cursor-pointer"
        style={{ backgroundColor: color }}
        onClick={() => onClick(color)}
      >
        {approximateColor.letter}
      </div>
    );
  };
  
      
    
  
  const InfoItem = ({ label, value, isColor = false }) => {
    let displayValue = value;
  
    if (label === "Thermal Expansion") {
      if (typeof value === 'number' && !isNaN(value)) {
        displayValue = `${value.toFixed(6)} mm/m/°C`;
      } else if (value === null || value === undefined) {
        displayValue = 'N/A';
      } else {
        displayValue = String(value); // Convert to string if it's neither a number nor null/undefined
      }
    }
  
    const handleColorClick = (color) => {
      const hexColor = color.replace('#', '');
      window.open(`https://www.color-hex.com/color/${hexColor}`, '_blank');
    };
  
    return (
      <div className="flex items-center">
        <span className="w-1/3 text-gray-500">{label}:</span>
        <span className="w-2/3 font-medium text-gray-900 flex items-center">
          {isColor && value ? (
            <>
              <ColorSquare color={value} onClick={handleColorClick} />
              <span className="ml-2 cursor-pointer" onClick={() => handleColorClick(value)}>
                {value}
              </span>
            </>
          ) : (
            displayValue
          )}
        </span>
      </div>
    );
  };
  
  const SimilarMarbles = ({ marbleId, onMarbleClick }) => {
    const [similarMarbles, setSimilarMarbles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
  
    useEffect(() => {
      const fetchSimilarMarbles = async () => {
        setLoading(true);
        setError(null);
        try {
          console.log(`Fetching similar marbles for ID: ${marbleId}`);
          const response = await axios.post('/api/similar-marbles', { marbleId });
          console.log('Similar marbles response:', response.data);
          setSimilarMarbles(response.data);
        } catch (error) {
          console.error('Error fetching similar marbles:', error);
          setError(error.response?.data?.error || 'Failed to load similar marbles');
        } finally {
          setLoading(false);
        }
      };
  
      fetchSimilarMarbles();
    }, [marbleId]);
  
    if (loading) {
      return <p>Loading similar marbles...</p>;
    }
  
    if (error) {
      return <p className="text-red-500">{error}</p>;
    }
  
    return (
      <div className="mt-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Similar Marbles</h3>
        {similarMarbles.length > 0 ? (
          <div className="grid grid-cols-2 gap-4">
            {similarMarbles.map((marble) => (
              <div
                key={marble.id}
                className="cursor-pointer"
                onClick={() => onMarbleClick(marble)}
              >
                <img
                  src={marble.imageUrl}
                  alt={marble.marbleName}
                  className="w-full h-32 object-cover rounded"
                />
                <p className="mt-1 text-sm font-medium">{marble.marbleName}</p>
              </div>
            ))}
          </div>
        ) : (
          <p>No similar marbles found.</p>
        )}
      </div>
    );
  };
  
  const MarbleGallery = ({ marbles, loading, hasMore, loadMore, searchTerm, onSearch, isSearching }) => {
    const { selectedMarble, openMarbleModal, closeMarbleModal } = useMarbleGallery();
    const observer = useRef();
    const [showSimilarMarbles, setShowSimilarMarbles] = useState(false);

    const lastMarbleElementRef = useCallback(node => {
      if (loading) return;
      if (observer.current) observer.current.disconnect();
      observer.current = new IntersectionObserver(entries => {
        if (entries[0].isIntersecting && hasMore) {
          console.log("Last marble in view, loading more...");
          loadMore();
        }
      });
      if (node) observer.current.observe(node);
    }, [loading, hasMore, loadMore]);
    const navigate = useNavigate();

    const handleImageClick = useCallback((marble) => {
      console.log('Marble clicked in gallery:', marble);
      openMarbleModal(marble);
    }, [openMarbleModal]);

    const handleShowSimilarMarbles = () => {
      setShowSimilarMarbles(prevState => !prevState);
    };

    const debouncedLogEvent = useCallback(
      debounce((eventType, data) => {
        fetch('/log_event', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ event_type: eventType, data: data }),
        })
          .then(response => {
            if (!response.ok) {
              throw new Error('Network response was not ok');
            }
            return response.json();
          })
          .then(data => console.log('Event logged:', data))
          .catch((error) => console.error('Error logging event:', error));
      }, 1000),
      []
    );

    useEffect(() => {
      const handleRouteChange = () => {
        debouncedLogEvent('route_travel', { route: window.location.pathname });
      };

      window.addEventListener('popstate', handleRouteChange);
      debouncedLogEvent('route_travel', { route: window.location.pathname });

      return () => {
        window.removeEventListener('popstate', handleRouteChange);
      };
    }, [debouncedLogEvent]);

    return (
      <div className="container mx-auto px-4 py-8">
        {isSearching ? (
          <div className="flex justify-center items-center h-64">
            <CircularProgress size={48} className="text-gradient-to-r from-purple-500 to-pink-500" />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {marbles.map((marble, index) => (
                <div
                  key={marble.id}
                  ref={index === marbles.length - 1 ? lastMarbleElementRef : null}
                >
                  <MarbleCard marble={marble} onImageClick={handleImageClick} />
                </div>
              ))}
            </div>
            {loading && !isSearching && <p className="text-center mt-4">Loading more marbles...</p>}
            {!hasMore && <p className="text-center mt-4">No more marbles to load</p>}
          </>
        )}
        <Modal isOpen={!!selectedMarble} onClose={closeMarbleModal}>
          {selectedMarble && (
            <div className="max-w-4xl mx-auto bg-white rounded-xl overflow-hidden shadow-2xl">
              <div className="md:flex">
                <div className="md:flex-shrink-0 md:w-1/2">
                  <WatermarkedImage 
                    src={selectedMarble.imageUrl} 
                    alt={selectedMarble.marbleName} 
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="p-8 md:w-1/2">
                  <div className="uppercase tracking-wide text-sm text-indigo-500 font-semibold mb-1">
                    {selectedMarble.marbleOrigin}
                  </div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-4">{selectedMarble.marbleName}</h2>
                  <div className="space-y-4">
                  <InfoItem label="Color" value={selectedMarble.stoneColor} isColor={true} />
                    <InfoItem 
                      label="Cost Range" 
                      value={selectedMarble.costRange != null ? `$${selectedMarble.costRange.toFixed(2)}` : 'Price on request'} 
                    />
                    <InfoItem label="Stain Resistance" value={selectedMarble.stainResistance} />
                    <InfoItem 
                      label="Thermal Expansion" 
                      value={selectedMarble.thermalExpansion}
                    />
                  </div>
                  <ExpandableDescription description={selectedMarble.description} />
                  <button
                onClick={handleShowSimilarMarbles}
                className="mt-4 bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
              >
                {showSimilarMarbles ? "Hide Similar Marbles" : "See Similar Marbles"}
              </button>
              {showSimilarMarbles && (
                <SimilarMarbles
                  marbleId={selectedMarble.id}
                  onMarbleClick={handleImageClick}
                />
              )}
                </div>
              </div>
            </div>
          )}
        </Modal>
      </div>
    );
  };

  export default MarbleGallery;