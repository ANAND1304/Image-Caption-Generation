
import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Image as ImageIcon } from 'lucide-react'
import './ImageDropzone.css'

const ACCEPT = { 'image/jpeg': [], 'image/png': [], 'image/webp': [], 'image/gif': [] }
const MAX_SIZE = 10 * 1024 * 1024

export default function ImageDropzone({ onFile, disabled }) {
  const onDrop = useCallback((accepted, rejected) => {
    if (rejected.length > 0) {
      const err = rejected[0].errors[0]
      alert(err.code === 'file-too-large'
        ? 'Image must be under 10MB.'
        : err.code === 'file-invalid-type'
        ? 'Please upload a JPEG, PNG, WEBP, or GIF image.'
        : err.message)
      return
    }
    if (accepted.length > 0) onFile(accepted[0])
  }, [onFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT,
    maxSize: MAX_SIZE,
    multiple: false,
    disabled,
  })

  return (
    <div
      {...getRootProps()}
      className={`dropzone ${isDragActive ? 'drag-active' : ''} ${disabled ? 'disabled' : ''}`}
    >
      <input {...getInputProps()} />
      <div className="dropzone-content">
        <div className={`drop-icon ${isDragActive ? 'bouncing' : ''}`}>
          {isDragActive ? <ImageIcon size={36} /> : <Upload size={36} />}
        </div>
        <p className="drop-title">
          {isDragActive ? 'Release to upload' : 'Drag & drop your image here'}
        </p>
        <p className="drop-sub">or click to browse — JPEG, PNG, WEBP, GIF up to 10MB</p>
        <div className="drop-badge">Upload Image</div>
      </div>
    </div>
  )
}
