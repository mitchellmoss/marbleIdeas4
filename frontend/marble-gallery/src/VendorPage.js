import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';

const VendorPage = () => {
  const { vendorId } = useParams();
  const [vendor, setVendor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchVendor = async () => {
      try {
        const response = await axios.get(`/api/vendors/${vendorId}`);
        setVendor(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load vendor data');
        setLoading(false);
      }
    };

    fetchVendor();
  }, [vendorId]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;
  if (!vendor) return <div>Vendor not found</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <Link to="/" className="text-blue-500 hover:text-blue-700 mb-4 inline-block">&larr; Back to Gallery</Link>
      <div className="bg-white shadow-xl rounded-lg overflow-hidden">
      <img src={`/pixel.gif?event=pageview&page=${encodeURIComponent(window.location.pathname)}`} alt="" style={{ display: 'none' }} />
        <div className="p-6">
          <div className="flex items-center mb-6">
            {vendor.vendorLogo ? (
              <img 
                src={`data:image/png;base64,${vendor.vendorLogo}`} 
                alt={`${vendor.name} logo`}
                className="w-32 h-32 object-contain mr-6"
              />
            ) : (
              <div className="w-32 h-32 bg-gray-200 flex items-center justify-center text-gray-500 mr-6">
                No Logo
              </div>
            )}
            <h1 className="text-3xl font-bold">{vendor.name}</h1>
          </div>
          <div className="space-y-4">
            <p><strong>Contact:</strong> {vendor.contact}</p>
            <p><strong>Location:</strong> {vendor.location}</p>
            {/* Add more vendor details here */}
          </div>
        </div>
      </div>
      {/* You can add more sections here, such as a list of marbles this vendor offers */}
    </div>
  );
};

export default VendorPage;