import { useState } from 'react';

export default function ImageGenerator({ onGenerate, loading }) {
  const [prompt, setPrompt] = useState('');
  const [suggestions] = useState([
    'A serene landscape with mountains and lakes',
    'A futuristic city at night with neon lights',
    'A portrait of a woman with ethereal features',
    'An abstract colorful geometric pattern',
    'A cozy cabin surrounded by autumn trees',
  ]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (prompt.trim()) {
      onGenerate(prompt);
      setPrompt('');
    }
  };

  return (
    <div className="generator-card">
      <h2>Create Image</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the image you want to generate..."
          rows="4"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !prompt.trim()}>
          {loading ? '⏳ Generating...' : '🚀 Generate Image'}
        </button>
      </form>

      <div className="suggestions">
        <h3>Try these prompts:</h3>
        <ul>
          {suggestions.map((suggestion, idx) => (
            <li
              key={idx}
              onClick={() => {
                setPrompt(suggestion);
              }}
              className="suggestion-item"
            >
              {suggestion}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
