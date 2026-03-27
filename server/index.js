require('express-async-errors');
const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const path = require('path');
const axios = require('axios');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const HF_API_KEY = process.env.HUGGINGFACE_API_KEY;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));

// Flux 2 API endpoint
const FLUX_API_URL = 'https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev';
const FLUX_NSFW_API_URL = 'https://api-inference.huggingface.co/models/Falconsai/nsfw_image_detection';

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Generate image using Flux 2
app.post('/api/generate-image', async (req, res) => {
  try {
    const { prompt, width = 512, height = 512 } = req.body;

    if (!HF_API_KEY) {
      return res.status(500).json({ error: 'HUGGINGFACE_API_KEY not configured' });
    }

    if (!prompt) {
      return res.status(400).json({ error: 'Prompt is required' });
    }

    console.log(`Generating image with prompt: "${prompt}"`);

    const response = await axios.post(
      FLUX_API_URL,
      { inputs: prompt },
      {
        headers: {
          Authorization: `Bearer ${HF_API_KEY}`,
          'Content-Type': 'application/json',
        },
        responseType: 'arraybuffer',
        timeout: 120000, // 2 minutes
      }
    );

    // Convert buffer to base64
    const base64Image = Buffer.from(response.data).toString('base64');
    const imageUrl = `data:image/jpeg;base64,${base64Image}`;

    res.json({
      success: true,
      image: imageUrl,
      prompt,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Image generation error:', error.message);
    res.status(500).json({
      error: 'Failed to generate image',
      details: error.message,
    });
  }
});

// Check for NSFW content
app.post('/api/check-nsfw', async (req, res) => {
  try {
    const { imageBase64 } = req.body;

    if (!HF_API_KEY) {
      return res.status(500).json({ error: 'HUGGINGFACE_API_KEY not configured' });
    }

    if (!imageBase64) {
      return res.status(400).json({ error: 'Image data is required' });
    }

    console.log('Checking image for NSFW content');

    const response = await axios.post(
      FLUX_NSFW_API_URL,
      { inputs: imageBase64 },
      {
        headers: {
          Authorization: `Bearer ${HF_API_KEY}`,
          'Content-Type': 'application/json',
        },
        timeout: 30000,
      }
    );

    res.json({
      success: true,
      nsfw_check: response.data,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('NSFW check error:', error.message);
    res.status(500).json({
      error: 'Failed to check NSFW content',
      details: error.message,
    });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error',
  });
});

app.listen(PORT, () => {
  console.log(`\n🚀 Flux 2 Media Generator Backend running at http://localhost:${PORT}`);
  console.log(`📷 POST /api/generate-image - Generate images with Flux 2`);
  console.log(`🔍 POST /api/check-nsfw - Check for NSFW content`);
  console.log(`💚 GET /api/health - Health check\n`);
});
