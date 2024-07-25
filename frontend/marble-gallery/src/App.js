import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';
import MarbleGallery from './marbleGallery';
import axios from 'axios';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import { ParallaxProvider } from 'react-scroll-parallax';
import About from './About';
import VendorPage from './VendorPage';
import Contact from './Contact';
import ImageUpload from './ImageUpload';
import { MarbleGalleryProvider } from './MarbleGalleryContext';
import { debounce } from 'lodash';
import { CircularProgress, createTheme, ThemeProvider } from '@mui/material';
import { purple, pink } from '@mui/material/colors';

function App() {
  const [marbles, setMarbles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  const fetchMarbles = useCallback(async (resetMarbles = false) => {
    if (loading || (!hasMore && !resetMarbles)) return;
    setLoading(true);
    if (resetMarbles) setIsSearching(true);
    try {
      const response = await axios.get('/api/images', {
        params: { page: resetMarbles ? 1 : page, per_page: 20, search: searchTerm }
      });
      setMarbles(prevMarbles => {
        if (resetMarbles) {
          return response.data.marbles;
        }
        return [...prevMarbles, ...response.data.marbles];
      });
      setHasMore(response.data.page < response.data.totalPages);
      setPage(prevPage => resetMarbles ? 2 : prevPage + 1);
    } catch (error) {
      console.error('Error fetching marbles:', error);
    } finally {
      setLoading(false);
      if (resetMarbles) setIsSearching(false);
    }
  }, [page, loading, hasMore, searchTerm]);

  useEffect(() => {
    fetchMarbles();
  }, []);

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
  };
  
  const handleSearchClick = () => {
    setPage(1);
    setHasMore(true);
    fetchMarbles(true);
  };

  const loadMore = useCallback(() => {
    fetchMarbles();
  }, [fetchMarbles]);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const theme = createTheme({
    palette: {
      primary: {
        main: pink[500],
      },
      secondary: {
        main: purple[500],
      },
    },
  });

  return (
    <ThemeProvider theme={theme}>
      <ParallaxProvider>
        <Router>
          <div className="flex flex-col min-h-screen bg-gradient-to-br from-purple-400 via-pink-500 to-red-500">
            {/* Construction banner */}
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 text-black text-xs py-1 text-center fixed top-0 left-0 right-0 z-50">
            This site is still under construction. We appreciate your patience! Features may or may not work as expected.            </div>
            
            {/* Header */}
            <header className="fixed top-5 left-0 right-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 shadow-lg z-40">              <div className="container mx-auto px-4 py-2 flex justify-between items-center">
                <div className="flex items-center">
                  <img src="/IP-Logo.svg" alt="Marble Logo" className="h-8 w-auto mr-2" />
                  <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-yellow-300">
                    Marble Gallery
                  </h1>
                </div>
                <nav className="hidden md:block">
                  <ul className="flex space-x-4">
                    <li><Link to="/" className="text-white hover:text-yellow-300 transition-colors duration-300 text-sm">Home</Link></li>
                    <li><Link to="/about" className="text-white hover:text-yellow-300 transition-colors duration-300 text-sm">About</Link></li>
                    <li><Link to="/contact" className="text-white hover:text-yellow-300 transition-colors duration-300 text-sm">Contact</Link></li>
                    <li><Link to="/upload" className="text-white hover:text-yellow-300 transition-colors duration-300 text-sm">Upload Image</Link></li>
                  </ul>
                </nav>
                <button onClick={toggleMenu} className="md:hidden text-white focus:outline-none">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7"></path>
                  </svg>
                </button>
              </div>
              {isMenuOpen && (
                <div className="md:hidden">
                  <ul className="bg-gradient-to-r from-pink-500 to-yellow-300 bg-opacity-10 backdrop-filter rounded-lg m-2 shadow-lg">
                    <li><Link to="/" className="block py-2 px-4 text-white hover:text-indigo-900 transition-colors duration-300" onClick={toggleMenu}>Home</Link></li>
                    <li><Link to="/about" className="block py-2 px-4 text-white hover:text-indigo-900 transition-colors duration-300" onClick={toggleMenu}>About</Link></li>
                    <li><Link to="/contact" className="block py-2 px-4 text-white hover:text-indigo-900 transition-colors duration-300" onClick={toggleMenu}>Contact</Link></li>
                    <li><Link to="/upload" className="block py-2 px-4 text-white hover:text-indigo-900 transition-colors duration-300" onClick={toggleMenu}>Upload Image</Link></li>
                  </ul>
                </div>
              )}
            </header>
            
                           {/* Search bar */}
              <div className="fixed top-20 left-0 right-0 z-30 px-4">              
                <div className="container mx-auto">
                <div className="flex bg-white bg-opacity-50 backdrop-filter backdrop-blur-md rounded-lg shadow-md">
                  <input
                    type="text"
                    placeholder="Search marbles..."
                    value={searchTerm}
                    onChange={handleSearchChange}
                    className="w-full px-4 py-2 rounded-l-lg bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={handleSearchClick}
                    className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-r-lg hover:from-purple-600 hover:to-pink-600 transition-colors duration-300 flex items-center justify-center min-w-[100px]"
                    disabled={isSearching}
                  >
                    {isSearching ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : (
                      'Search'
                    )}
                  </button>
                </div>
              </div>
            </div>
            
            {/* Main content */}
            <main className="flex-grow pt-40 px-4">
              <MarbleGalleryProvider>
                <Routes>
                  <Route path="/" element={
                    <div className="container mx-auto px-4 py-8">
                      <MarbleGallery 
                        marbles={marbles} 
                        loading={loading}
                        hasMore={hasMore}
                        loadMore={loadMore}
                        searchTerm={searchTerm}
                        onSearch={handleSearchClick}
                        isSearching={isSearching}
                      />
                    </div>
                  } />
                  <Route path="/about" element={<About />} />
                  <Route path="/vendor/:vendorId" element={<VendorPage />} />
                  <Route path="/contact" element={<Contact />} />
                  <Route path="/upload" element={<ImageUpload />} />
                </Routes>
              </MarbleGalleryProvider>
            </main>
            
            <footer className="bg-white bg-opacity-90 py-6">
              <div className="container mx-auto px-4 text-center text-gray-600">
                <p>&copy; 2024 Marble.Boston</p>
                <div className="mt-4 flex justify-center space-x-4">
                  {/* Social media icons remain unchanged */}
                </div>
              </div>
            </footer>
          </div>
        </Router>
      </ParallaxProvider>
    </ThemeProvider>
  );
}

export default App;