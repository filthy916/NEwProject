import { useState } from 'react';

export default function NSFWChecker({ image, onCheck }) {
  const [checking, setChecking] = useState(false);

  const handleCheck = async () => {
    setChecking(true);
    try {
      await onCheck(image);
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="nsfw-checker-card">
      <h2>Content Safety</h2>
      <p>Check if the generated image contains NSFW content</p>
      <button onClick={handleCheck} disabled={checking}>
        {checking ? '🔍 Checking...' : '🛡️ Check for NSFW'}
      </button>
    </div>
  );
}
