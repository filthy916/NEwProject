# 🎨 Flux 2 Media Generator

Generate stunning images and video content powered by Flux 2 AI model with NSFW content detection.

## Features

- ✨ **Flux 2 Image Generation** - Create high-quality images from text prompts
- 🛡️ **NSFW Content Detection** - Built-in content safety checking via Hugging Face models
- 🎬 **Video Support** - Ready for video generation integration
- 🚀 **Fast & Responsive** - Built with React + Vite + Express
- 🎨 **Modern UI** - Beautiful dark-mode interface with Tailwind styling

## Tech Stack

**Backend:**
- Node.js + Express.js
- Hugging Face API integration
- Axios for API calls

**Frontend:**
- React 18
- Vite
- Modern CSS with gradients and animations

## Setup

### Prerequisites

- Node.js 16+
- Hugging Face API key (free at [huggingface.co](https://huggingface.co))

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd flux-2-media-generator
```

2. Set up backend:
```bash
cd server
npm install
cp .env.example .env
# Edit .env and add your HUGGINGFACE_API_KEY
```

3. Set up frontend:
```bash
cd ../client
npm install
```

## Running Locally

### Option 1: Run both servers concurrently (from root)
```bash
npm install
npm run dev
```

### Option 2: Run separately

Terminal 1 - Backend:
```bash
cd server
npm start
# Runs on http://localhost:5000
```

Terminal 2 - Frontend:
```bash
cd client
npm run dev
# Runs on http://localhost:3000
```

## API Endpoints

### Generate Image
```
POST /api/generate-image
Body: { "prompt": "A beautiful sunset", "width": 512, "height": 512 }
```

### Check NSFW Content
```
POST /api/check-nsfw
Body: { "imageBase64": "data:image/jpeg;base64,..." }
```

### Health Check
```
GET /api/health
```

## Getting Your Hugging Face API Key

1. Sign up at [huggingface.co](https://huggingface.co)
2. Go to Settings → Access Tokens
3. Create a new token with read access
4. Copy it to your `.env` file as `HUGGINGFACE_API_KEY`

## Building for Production

### Building the frontend:
```bash
cd client
npm run build
# Output in client/dist
```

### Deploy backend to production:
```bash
cd server
npm install --production
npm start
```

## Environment Variables

Create a `.env` file in the `server` directory:

```
PORT=5000
HUGGINGFACE_API_KEY=your_key_here
```

## Project Structure

```
flux-2-media-generator/
├── server/
│   ├── index.js          # Express server & API routes
│   ├── package.json
│   └── .env.example
├── client/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── App.jsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── package.json          # Root package with dev script
└── .gitignore
```

## Future Enhancements

- [ ] Video generation support
- [ ] Image batch processing
- [ ] Advanced filtering options
- [ ] User accounts & history
- [ ] Rate limiting and quota management
- [ ] Image editing tools
- [ ] Export presets

## License

MIT

## Support

For issues or questions, create a GitHub issue or reach out.

## Disclaimer

This tool uses AI models for content generation. Always review generated content and respect copyright laws and community guidelines. The NSFW detection is not foolproof and should not be the only content moderation mechanism.
