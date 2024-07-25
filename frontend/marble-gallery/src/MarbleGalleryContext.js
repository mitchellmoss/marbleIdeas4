import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

const MarbleGalleryContext = createContext();

export const useMarbleGallery = () => useContext(MarbleGalleryContext);

export const MarbleGalleryProvider = ({ children }) => {
  const [selectedMarble, setSelectedMarble] = useState(() => {
    const saved = localStorage.getItem('selectedMarble');
    return saved ? JSON.parse(saved) : null;
  });

  useEffect(() => {
    if (selectedMarble) {
      localStorage.setItem('selectedMarble', JSON.stringify(selectedMarble));
    } else {
      localStorage.removeItem('selectedMarble');
    }
  }, [selectedMarble]);

  const openMarbleModal = useCallback((marble) => {
    console.log('Opening modal for marble:', marble);
    setSelectedMarble(marble);
  }, []);

  const closeMarbleModal = useCallback(() => {
    console.log('Closing marble modal');
    setSelectedMarble(null);
  }, []);

  return (
    <MarbleGalleryContext.Provider value={{ openMarbleModal, closeMarbleModal, selectedMarble }}>
      {children}
    </MarbleGalleryContext.Provider>
  );
};