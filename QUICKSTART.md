# 🚀 Quick Start Guide

## 1. Get Your Hugging Face API Key
- Go to https://huggingface.co/settings/tokens
- Create a new token (read access is enough)
- Copy the token

## 2. Configure Environment
Edit `server/.env` and add your API key:
```
PORT=5000
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxx
```

## 3. Install Dependencies

### Backend
```bash
cd server
npm install
```

### Frontend
```bash
cd client
npm install
```

## 4. Start Development Servers

### Option A: From root directory (runs both concurrently)
```bash
npm install
npm run dev
```
- Frontend: http://localhost:3000
- Backend: http://localhost:5000

### Option B: In separate terminals

Terminal 1:
```bash
cd server && npm start
```

Terminal 2:
```bash
cd client && npm run dev
```

## 5. Use the Application

1. Open http://localhost:3000 in your browser
2. Enter a prompt (e.g., "A sunset over mountains")
3. Click "Generate Image"
4. Wait for the image to be generated
5. Optionally check for NSFW content
6. Download your generated image

## 6. Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/flux-2-media-generator.git
git branch -M main
git push -u origin main
```

## Troubleshooting

### Image generation takes long
- First call to Flux 2 API can take 30-60 seconds
- Subsequent calls are faster
- Check that your API key is valid

### API errors
- Verify `HUGGINGFACE_API_KEY` is set in `server/.env`
- Check that your HF account has API access
- Make sure the backend is running on port 5000

### Frontend not loading
- Ensure backend is running on http://localhost:5000
- Check browser console for CORS errors
- Verify vite proxy is configured correctly

## Next Steps

- [ ] Connect to your GitHub repository
- [ ] Set up CI/CD pipelines
- [ ] Deploy to production (Render, Fly.io, Azure, etc.)
- [ ] Add authentication (optional)
- [ ] Implement video generation
- [ ] Add more AI models
