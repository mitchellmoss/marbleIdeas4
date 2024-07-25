import React, { useState, useCallback, useEffect } from 'react';
import { Box, Button, Typography, CircularProgress, Grid, Fade, Container, Card, CardContent, CardMedia } from '@mui/material';
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { useDropzone } from 'react-dropzone';
import { useMarbleGallery } from './MarbleGalleryContext';
import { useNavigate } from 'react-router-dom';

const UploadBox = styled(Box)(({ theme }) => ({
  border: `2px dashed ${theme.palette.primary.main}`,
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(4),
  textAlign: 'center',
  cursor: 'pointer',
  transition: 'all 0.3s ease-in-out',
  backgroundColor: theme.palette.background.paper,
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
    transform: 'translateY(-5px)',
    boxShadow: theme.shadows[4],
  },
}));

const StyledButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(2, 0),
  transition: 'all 0.3s ease-in-out',
  '&:hover': {
    transform: 'translateY(-3px)',
    boxShadow: theme.shadows[4],
  },
}));

const FancyTitle = styled(Typography)(({ theme }) => ({
  fontWeight: 'bold',
  color: theme.palette.primary.main,
  textShadow: '2px 2px 4px rgba(0,0,0,0.1)',
  position: 'relative',
  marginBottom: theme.spacing(4),
  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: '-10px',
    left: '50%',
    transform: 'translateX(-50%)',
    width: '80px',
    height: '4px',
    background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
    borderRadius: '2px',
  },
  '& span': {
    color: theme.palette.secondary.main,
  },
}));

const ResultCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'all 0.3s ease-in-out',
  '&:hover': {
    transform: 'translateY(-5px)',
    boxShadow: theme.shadows[8],
  },
}));

const ImageUpload = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [similarMarbles, setSimilarMarbles] = useState([]);
  const [error, setError] = useState(null);
  const { openMarbleModal } = useMarbleGallery();
  const navigate = useNavigate();

  useEffect(() => {
    // Load saved data from localStorage when component mounts
    const savedPreview = localStorage.getItem('marblePreview');
    const savedSimilarMarbles = localStorage.getItem('similarMarbles');

    if (savedPreview) {
      setPreview(savedPreview);
    }

    if (savedSimilarMarbles) {
      setSimilarMarbles(JSON.parse(savedSimilarMarbles));
    }
  }, []);

  useEffect(() => {
    // Save preview to localStorage whenever it changes
    if (preview) {
      localStorage.setItem('marblePreview', preview);
    } else {
      localStorage.removeItem('marblePreview');
    }
  }, [preview]);

  useEffect(() => {
    // Save similarMarbles to localStorage whenever it changes
    if (similarMarbles.length > 0) {
      localStorage.setItem('similarMarbles', JSON.stringify(similarMarbles));
    } else {
      localStorage.removeItem('similarMarbles');
    }
  }, [similarMarbles]);

  useEffect(() => {
    console.log('openMarbleModal available:', !!openMarbleModal);
  }, [openMarbleModal]);

  const handleMarbleClick = (marble) => {
    console.log('Marble clicked:', marble);
    if (openMarbleModal) {
      openMarbleModal(marble);
      navigate('/');
    } else {
      console.error('openMarbleModal is not available');
    }
  };

  const onDrop = useCallback((acceptedFiles) => {
    const selectedFile = acceptedFiles[0];
    setFile(selectedFile);
    const previewUrl = URL.createObjectURL(selectedFile);
    setPreview(previewUrl);
    setError(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await fetch('/api/upload-image', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Upload failed: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      setSimilarMarbles(data);
    } catch (error) {
      console.error('Error uploading image:', error);
      setError('Failed to upload image. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setPreview(null);
    setSimilarMarbles([]);
    setError(null);
    localStorage.removeItem('marblePreview');
    localStorage.removeItem('similarMarbles');
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <FancyTitle variant="h2" align="center">
        Match <span>Your</span> Marble!
      </FancyTitle>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom align="center">
        Upload your marble image and find its perfect matches!
      </Typography>

      <Box sx={{ mt: 4 }}>
        <UploadBox {...getRootProps()}>
          <input {...getInputProps()} />
          {preview ? (
            <Box
              component="img"
              src={preview}
              alt="Uploaded marble"
              sx={{ maxWidth: '100%', maxHeight: 300, objectFit: 'contain' }}
            />
          ) : (
            <>
              <CloudUploadIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6">
                {isDragActive ? 'Drop the image here...' : 'Drag & drop an image here, or click to select'}
              </Typography>
            </>
          )}
        </UploadBox>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
          <StyledButton
            variant="contained"
            color="primary"
            onClick={handleUpload}
            disabled={!file || loading}
            sx={{ flex: 1, mr: 1 }}
          >
            {loading ? 'Processing...' : 'Find Similar Marbles'}
          </StyledButton>
          <StyledButton
            variant="outlined"
            color="secondary"
            onClick={handleClear}
            sx={{ flex: 0.3, ml: 1 }}
          >
            Clear
          </StyledButton>
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Typography color="error" align="center" sx={{ mt: 2 }}>
            {error}
          </Typography>
        )}
      </Box>

      {similarMarbles.length > 0 && (
        <Box sx={{ mt: 6 }}>
          <Typography variant="h4" gutterBottom color="secondary" align="center">
            Marble Matches
          </Typography>
          <Grid container spacing={3}>
            {similarMarbles.map((marble, index) => (
              <Grid item xs={12} sm={6} md={4} key={marble.id}>
                <Fade in={true} style={{ transitionDelay: `${index * 100}ms` }}>
                  <ResultCard onClick={() => handleMarbleClick(marble)}>
                    <CardMedia
                      component="img"
                      height="200"
                      image={marble.imageUrl}
                      alt={marble.marbleName}
                    />
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {marble.marbleName}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Origin: {marble.marbleOrigin}
                      </Typography>
                      <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
                        Similarity: {(marble.similarity * 100).toFixed(1)}%
                      </Typography>
                    </CardContent>
                  </ResultCard>
                </Fade>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </Container>
  );
};

export default ImageUpload;