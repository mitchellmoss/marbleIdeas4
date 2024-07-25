import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Parallax } from 'react-scroll-parallax';
import { Link } from 'react-router-dom';

const SkeletonExpert = () => (
  <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-xl h-64"></div>
);

const Contact = () => {
  const [expertInfo, setExpertInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    fetchExpertInfo();
  }, []);

  useEffect(() => {
    // Tracking pixel
    const img = new Image();
    img.src = `/pixel.gif?event=pageview&page=${encodeURIComponent(window.location.pathname)}&sr=${window.screen.width}x${window.screen.height}&cd=${window.screen.colorDepth}&plugins=${encodeURIComponent(Array.from(navigator.plugins).map(p => p.name).join(','))}&time=${Date.now()}`;
  }, []);

  const fetchExpertInfo = async () => {
    try {
      const response = await axios.get('/api/expert');
      setExpertInfo(response.data);
    } catch (error) {
      console.error('Error fetching expert info:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-500 to-red-500">
      <header className="fixed top-0 left-0 right-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 shadow-lg z-10" style={{ backdropFilter: 'blur(10px)' }}>
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center">
            <img src="/IP-Logo.svg" alt="Marble Logo" className="h-12 w-auto mr-4" />
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-yellow-300">
              Marble Gallery
            </h1>
          </div>

          <nav className="hidden md:block">
            <ul className="flex space-x-6">
              <li><Link to="/" className="text-white hover:text-yellow-300 transition-colors duration-300">Home</Link></li>
              <li><Link to="/about" className="text-white hover:text-yellow-300 transition-colors duration-300">About</Link></li>
              <li><Link to="/contact" className="text-white hover:text-yellow-300 transition-colors duration-300">Contact</Link></li>
            </ul>
          </nav>

          <nav className="hidden md:block">
            <ul className="flex space-x-6">
              <li><Link to="/" className="text-white hover:text-yellow-300 transition-colors duration-300">Home</Link></li>
              <li><Link to="/about" className="text-white hover:text-yellow-300 transition-colors duration-300">About</Link></li>
              <li><Link to="/contact" className="text-white hover:text-yellow-300 transition-colors duration-300">Contact</Link></li>
              <li><Link to="/upload" className="text-white hover:text-yellow-300 transition-colors duration-300">Upload Image</Link></li>
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
            </ul>
          </div>
        )}
      </header>

      <Parallax className="h-screen" y={[-20, 20]} tagOuter="figure">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-400 via-pink-500 to-red-500 opacity-50"></div>
        <div className="relative z-10 container mx-auto px-4 py-24">
          <motion.div
            className="max-w-4xl mx-auto bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="pt-16 pb-8">
              <motion.h1
                className="text-5xl font-extrabold text-center bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-pink-600"
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
              >
                Contact Our Stone Expert
              </motion.h1>
            </div>
            {isLoading ? (
              <SkeletonExpert />
            ) : (
              <div className="md:flex p-8">
                <motion.div
                  className="md:flex-shrink-0"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5, duration: 0.5 }}
                >
                  <img
                    className="h-48 w-full object-cover md:w-48 rounded-lg"
                    src={expertInfo.image_url}
                    alt={expertInfo.name}
                  />
                </motion.div>
                <div className="mt-4 md:mt-0 md:ml-6">
                  <motion.div
                    className="uppercase tracking-wide text-sm text-indigo-500 font-semibold"
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.7, duration: 0.5 }}
                  >
                    {expertInfo.title}
                  </motion.div>
                  <motion.h2
                    className="block mt-1 text-lg leading-tight font-medium text-black dark:text-white"
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.9, duration: 0.5 }}
                  >
                    {expertInfo.name}
                  </motion.h2>
                  <motion.p
                    className="mt-2 text-gray-500 dark:text-gray-300"
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 1.1, duration: 0.5 }}
                  >
                    {expertInfo.bio}
                  </motion.p>
                </div>
              </div>
            )}
            <motion.div
              className="bg-gray-100 dark:bg-gray-700 p-8"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 1.3, duration: 0.5 }}
            >
              <h2 className="text-2xl font-bold mb-4 text-gray-800 dark:text-gray-200">Get in Touch</h2>
              <p className="mb-4 text-gray-600 dark:text-gray-300">
                If you have any questions about our marble selection or need expert advice, please don't hesitate to contact Carlo Baraglia.
              </p>
              <a
                href="mailto:carlo@marble.boston"
                className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-full transition duration-300 ease-in-out transform hover:scale-105 inline-block"
              >
                Email Carlo
              </a>
            </motion.div>
          </motion.div>
        </div>
      </Parallax>
    </div>
  );
};

export default Contact;