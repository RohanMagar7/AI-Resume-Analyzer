import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadResume } from '../api';

function Upload() {
  const [file, setFile] = useState(null);
  const [targetRole, setTargetRole] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    validateAndSetFile(droppedFile);
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (file) => {
    setError(null);
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx'].includes(ext)) {
      setError('Please upload a PDF or DOCX file.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds 10MB limit.');
      return;
    }

    setFile(file);
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const result = await uploadResume(file, targetRole);
      navigate(`/results/${result.id}`);
    } catch (err) {
      const message = err.response?.data?.error || err.message || 'Upload failed. Please try again.';
      setError(message);
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1>Upload Resume</h1>
          <p>Upload a resume (PDF or DOCX) for AI-powered analysis</p>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      <div className="card" style={{ maxWidth: '640px', margin: '0 auto' }}>
        {/* File Upload Area */}
        {!file ? (
          <div
            className={`upload-area ${dragOver ? 'drag-over' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <span className="upload-icon">📄</span>
            <div className="upload-text">
              Drag & drop your resume here
            </div>
            <div className="upload-hint">
              or click to browse — Supports PDF and DOCX (max 10MB)
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </div>
        ) : (
          <div style={{ textAlign: 'center' }}>
            {/* File Info */}
            <div style={{
              background: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-lg)',
              padding: '28px',
              marginBottom: '24px',
              border: '1px solid var(--border-color)',
            }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>
                {file.name.endsWith('.pdf') ? '📕' : '📘'}
              </div>
              <div style={{
                fontWeight: 600,
                marginBottom: '6px',
                color: 'var(--text-primary)',
                fontSize: '1rem',
              }}>
                {file.name}
              </div>
              <div style={{
                fontSize: '0.85rem',
                color: 'var(--text-muted)',
                marginBottom: '16px',
              }}>
                {formatFileSize(file.size)}
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setFile(null)}
              >
                Choose Different File
              </button>
            </div>

            {/* Target Role (optional) */}
            <div style={{ marginBottom: '24px', textAlign: 'left' }}>
              <label style={{
                display: 'block',
                fontSize: '0.9rem',
                fontWeight: 600,
                marginBottom: '8px',
                color: 'var(--text-secondary)',
              }}>
                Target Job Role (optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Software Engineer, Data Scientist..."
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.9rem',
                  outline: 'none',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  transition: 'var(--transition)',
                }}
                onFocus={(e) => e.target.style.borderColor = 'var(--accent-1)'}
                onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
              />
            </div>

            {/* Upload Button */}
            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={uploading}
              style={{ width: '100%', padding: '14px 24px', fontSize: '1rem' }}
            >
              {uploading ? (
                <>
                  <div className="spinner" style={{
                    width: 20, height: 20,
                    borderWidth: 2,
                    borderTopColor: 'white',
                    borderColor: 'rgba(255,255,255,0.2)',
                  }}></div>
                  Analyzing Resume...
                </>
              ) : (
                <>
                  <span>🚀</span> Analyze Resume
                </>
              )}
            </button>
          </div>
        )}

        {/* Supported Formats Info */}
        <div style={{
          marginTop: '24px',
          padding: '20px',
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--radius)',
          fontSize: '0.85rem',
          color: 'var(--text-muted)',
          border: '1px solid var(--border-color)',
        }}>
          <strong style={{ color: 'var(--text-secondary)' }}>Supported Formats:</strong>
          <div style={{ marginTop: '8px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <span className="tag tag-primary">📕 PDF</span>
            <span className="tag tag-primary">📘 DOCX</span>
          </div>
          <div style={{ marginTop: '12px' }}>
            <strong style={{ color: 'var(--text-secondary)' }}>Analysis Includes:</strong>
            <ul style={{
              marginTop: '6px',
              paddingLeft: '20px',
              lineHeight: '2',
              color: 'var(--text-muted)',
            }}>
              <li>Resume parsing & text extraction</li>
              <li>NLP-based skill identification</li>
              <li>ATS score evaluation (0-100)</li>
              <li>Job role matching</li>
              <li>Keyword & format analysis</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Upload;