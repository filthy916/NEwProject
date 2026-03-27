export default function ImagePreview({ image }) {
  const downloadImage = () => {
    const link = document.createElement('a');
    link.href = image;
    link.download = `generated-image-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="preview-card">
      <h2>Generated Image</h2>
      <div className="image-container">
        <img src={image} alt="Generated" />
      </div>
      <button onClick={downloadImage} className="download-btn">
        📥 Download Image
      </button>
    </div>
  );
}
