import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Parallax } from 'react-scroll-parallax';
import { Link } from 'react-router-dom';


const FeaturedMarble = ({ name, origin, cost, description, imageUrl }) => (
  <motion.div
    className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden transform transition duration-300 hover:scale-105"
    whileHover={{ y: -5 }}
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
  >
    <div className="relative">
      <img src={imageUrl} alt={name} className="w-full h-64 object-cover" />
      <div className="absolute top-0 right-0 bg-green-500 text-white px-3 py-1 rounded-bl-lg">
        ${cost}
      </div>
    </div>
    <div className="p-6">
      <h3 className="text-2xl font-bold mb-2 dark:text-white">{name}</h3>
      <p className="text-gray-600 dark:text-gray-300 mb-3">Origin: {origin}</p>
      <p className="text-gray-700 dark:text-gray-200 line-clamp-3">{description}</p>
    </div>
  </motion.div>
);

const SkeletonMarble = () => (
  <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-xl h-64"></div>
);

const About = () => {
  const [featuredMarbles, setFeaturedMarbles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    fetchFeaturedMarbles();
  }, []);

  useEffect(() => {
    // Tracking pixel
    const img = new Image();
    img.src = `/pixel.gif?event=pageview&page=${encodeURIComponent(window.location.pathname)}&sr=${window.screen.width}x${window.screen.height}&cd=${window.screen.colorDepth}&plugins=${encodeURIComponent(Array.from(navigator.plugins).map(p => p.name).join(','))}&time=${Date.now()}`;
  }, []);

  const fetchFeaturedMarbles = async () => {
    try {
      const response = await axios.get('/api/featured-marbles');
      setFeaturedMarbles(response.data);
    } catch (error) {
      console.error('Error fetching featured marbles:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };


  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900 text-white' : 'bg-white text-gray-900'}`}>
      
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
              <li><a href="#" className="text-white hover:text-yellow-300 transition-colors duration-300">Contact</a></li>
            </ul>
          </nav>

          <nav className="hidden md:block">
            <ul className="flex space-x-6">
              <li><Link to="/" className="text-white hover:text-yellow-300 transition-colors duration-300">Home</Link></li>
              <li><Link to="/upload" className="text-white hover:text-yellow-300 transition-colors duration-300">Upload Image</Link></li>              <li><a href="#" className="text-white hover:text-yellow-300 transition-colors duration-300">Contact</a></li>
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
              <li><a href="#" className="block py-2 px-4 text-white hover:text-indigo-900 transition-colors duration-300" onClick={toggleMenu}>Contact</a></li>
            </ul>
          </div>
          
        )}
      </header>
      <Parallax speed={-10}>
        <div className="relative">
          <div
            className="absolutenset-0 bg-cover bg-center z-0 opacity-50"
            style={{ backgroundImage: 'ur(/IP-Logo.svg)' }}
            />
            <div className="relative z-10 container mx-auto px-4 py-16">
            <motion.h1
            className="text-5xl font-extrabold mb-12 text-center bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-pink-600"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            >
            About Marble.Boston
            </motion.h1>
            <motion.div
  className="mb-16 max-w-3xl mx-auto bg-gradient-to-r from-purple-100 to-pink-100 dark:from-purple-900 dark:to-pink-900 rounded-xl shadow-lg p-8"
  initial={{ opacity: 0, scale: 0.9 }}
  animate={{ opacity: 1, scale: 1 }}
  transition={{ delay: 0.3, duration: 0.8 }}
>
  <motion.h2
    className="text-3xl font-bold mb-6 text-center text-purple-600 dark:text-purple-300"
    initial={{ y: -20, opacity: 0 }}
    animate={{ y: 0, opacity: 1 }}
    transition={{ delay: 0.5, duration: 0.5 }}
  >
    Our Story
  </motion.h2>
  <motion.p
    className="text-xl text-gray-700 dark:text-gray-300 mb-6 leading-relaxed"
    initial={{ x: -20, opacity: 0 }}
    animate={{ x: 0, opacity: 1 }}
    transition={{ delay: 0.7, duration: 0.5 }}
  >
    Welcome to Marble.Boston, your premier destination for exquisite marble selections. Our gallery showcases a curated collection of the finest marbles from around the world, each piece telling its own unique story of natural beauty and geological wonder.
  </motion.p>
  <motion.p
    className="text-xl text-gray-700 dark:text-gray-300 mb-6 leading-relaxed"
    initial={{ x: 20, opacity: 0 }}
    animate={{ x: 0, opacity: 1 }}
    transition={{ delay: 0.9, duration: 0.5 }}
  >
    At Marble.Boston, we pride ourselves on offering not just products, but experiences. Our team of experts is passionate about helping you find the perfect marble for your project, whether it's for a luxurious kitchen countertop, an elegant bathroom vanity, or a stunning piece of art.
  </motion.p>
  <motion.div
    className="flex justify-center"
    initial={{ y: 20, opacity: 0 }}
    animate={{ y: 0, opacity: 1 }}
    transition={{ delay: 1.1, duration: 0.5 }}
  >
    <Link
      to="/contact"
      className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-full transition duration-300 ease-in-out transform hover:scale-105"
    >
      Get in Touch
    </Link>
  </motion.div>
</motion.div>
            <h2 className="text-3xl font-bold mb-8 text-center">Featured Marbles</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {isLoading
                ? Array(3).fill().map((_, index) => <SkeletonMarble key={index} />)
                : featuredMarbles.slice(0, 3).map((marble) => (
                    <FeaturedMarble
                      key={marble.id}
                      name={marble.name}
                      origin={marble.origin}
                      cost={marble.cost}
                      description={marble.description}
                      imageUrl={marble.imageUrl}
                    />
                  ))}
            </div>
          </div>
        </div>
      </Parallax>
    </div>
  );
};

export default About;
            