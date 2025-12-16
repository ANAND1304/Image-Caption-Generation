import React, { useState } from 'react';
import './styles/App.css';
import Header from './components/Header';
import ImageUploader from './components/ImageUploader';
import CaptionDisplay from './components/CaptionDisplay';
import Features from './components/Features';
import Footer from './components/Footer';

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [caption, setCaption] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleImageUpload = async (imageFile) => {
    setLoading(true);
    setError('');
    setCaption('');
    try {
      const imageUrl = URL.createObjectURL(imageFile);
      setUploadedImage(imageUrl);

      // TODO: Replace with your backend API
      // const formData = new FormData();
      // formData.append('image', imageFile);
      // const response = await axios.post('YOUR_API/generate-caption', formData);
      // setCaption(response.data.caption);

      await new Promise(resolve => setTimeout(resolve, 2000));
      const captions = [
        "A beautiful landscape with mountains and a lake.",
        "A group of people enjoying a sunny day at the beach.",
        "A cat sitting on a windowsill looking outside.",
        "A colorful sunset over the ocean with warm clouds.",
        "A modern building with glass facades."
      ];
      setCaption(captions[Math.floor(Math.random() * captions.length)]);
    } catch (err) {
      setError('Failed to generate caption. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <Header />
      <main className="main-content">
        <section className="hero-section">
          <div className="container">
            <div className="hero-content">
              <h1 className="hero-title">AI-Powered Image Caption Generator</h1>
              <p className="hero-subtitle">Deep Learning with CNN and LSTM</p>
            </div>
            <div className="upload-section">
              {!uploadedImage ? (
                <ImageUploader onImageUpload={handleImageUpload} />
              ) : (
                <CaptionDisplay
                  image={uploadedImage}
                  caption={caption}
                  loading={loading}
                  error={error}
                  onReset={() => setUploadedImage(null)}
                />
              )}
            </div>
          </div>
        </section>
        <Features />
      </main>
      <Footer />
    </div>
  );
}

export default App;