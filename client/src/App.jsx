import { useState } from 'react';
import axios from 'axios';
import './App.css';
import ImageGenerator from './components/ImageGenerator';
import ImagePreview from './components/ImagePreview';
import NSFWChecker from './components/NSFWChecker';

function App() {
  const [generatedImage, setGeneratedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [nsfw_result, setNsfwResult] = useState(null);

  const handleGenerateImage = async (prompt) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('/api/generate-image', { prompt });
      setGeneratedImage(response.data.image);
      setNsfwResult(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate image');
      console.error('Generation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckNsfw = async (imageBase64) => {
    try {
      const response = await axios.post('/api/check-nsfw', { imageBase64 });
      setNsfwResult(response.data.nsfw_check);
    } catch (err) {
      setError('Failed to check NSFW content');
      console.error('NSFW check error:', err);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎨 Flux 2 Media Generator</h1>
        <p>Generate stunning images and video content with AI</p>
      </header>

      <div className="container">
        <div className="main-content">
          <ImageGenerator onGenerate={handleGenerateImage} loading={loading} />
          
          {error && (
            <div className="error-message">
              ❌ {error}
            </div>
          )}

          {generatedImage && (
            <>
              <ImagePreview image={generatedImage} />
              <NSFWChecker image={generatedImage} onCheck={handleCheckNsfw} />
            </>
          )}

          {nsfw_result && (
            <div className="nsfw-result">
              <h3>Content Safety Check</h3>
              <pre>{JSON.stringify(nsfw_result, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
