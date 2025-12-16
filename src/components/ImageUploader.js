import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import '../styles/ImageUploader.css';

function ImageUploader({ onImageUpload }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      onImageUpload(acceptedFiles[0]);
    }
  }, [onImageUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.webp']},
    multiple: false,
    maxSize: 10485760
  });

  return (
    <div className="image-uploader">
      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
        <input {...getInputProps()} />
        <div className="upload-text">
          <h3>{isDragActive ? 'Drop here!' : 'Upload Image'}</h3>
          <p>Drag and drop or click to browse</p>
          <span className="file-types">JPG, PNG, GIF, WEBP (Max 10MB)</span>
        </div>
        <button type="button" className="upload-button">Choose File</button>
      </div>
    </div>
  );
}

export default ImageUploader;