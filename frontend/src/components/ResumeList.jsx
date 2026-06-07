import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { listResumes, deleteResume } from '../api';

function ResumeList() {
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('-created_at');
  const [showDelete, setShowDelete] = useState(null);
  const navigate = useNavigate();

  const fetchResumes = useCallback(async () => {
    try {
      setLoading(true);
      const data = await listResumes({ sort: sortBy });
      setResumes(data.results || []);
    } catch (err) {
      setError('Failed to load resumes. Make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  }, [sortBy]);

  useEffect(() => {
    fetchResumes();
  }, [fetchResumes]);

  const handleDelete = async (id) => {
    try {
      await deleteResume(id);
      setResumes(prev => prev.filter(r => r.id !== id));
      setShowDelete(null);
    } catch (err) {
      setError('Failed to delete resume.');
    }
  };

  const getScoreTag = (score) => {
    if (score === null || score === undefined) return <span className="tag tag-gray">N/A</span>;
    if (score >= 80) return <span className="tag tag-success">{score.toFixed(0)}</span>;
    if (score >= 60) return <span className="tag tag-primary">{score.toFixed(0)}</span>;
    if (score >= 40) return <span className="tag tag-warning">{score.toFixed(0)}</span>;
    return <span className="tag tag-danger">{score.toFixed(0)}</span>;
  };

  const formatDate = (dateStr) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1>Resume List</h1>
          <p>{resumes.length} resume{resumes.length !== 1 ? 's' : ''} analyzed</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/upload')}>
          + Upload New
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Sort Controls */}
      <div style={{ marginBottom: '16px', display: 'flex', gap: '8px', alignItems: 'center' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--gray-500)' }}>Sort by:</span>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          style={{
            padding: '6px 12px',
            borderRadius: '6px',
            border: '1px solid var(--gray-200)',
            fontSize: '0.85rem',
            background: 'white',
          }}
        >
          <option value="-created_at">Newest First</option>
          <option value="created_at">Oldest First</option>
          <option value="-ats_score">Highest ATS Score</option>
          <option value="ats_score">Lowest ATS Score</option>
          <option value="-experience_years">Most Experience</option>
        </select>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner"></div></div>
      ) : resumes.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M9 13h6m-3-3v6m-5 4h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <h3>No Resumes Found</h3>
            <p style={{ marginBottom: '16px' }}>Upload your first resume to get started.</p>
            <button className="btn btn-primary" onClick={() => navigate('/upload')}>
              Upload Resume
            </button>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>File</th>
                  <th>Skills</th>
                  <th>Experience</th>
                  <th>ATS Score</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {resumes.map((resume) => (
                  <tr key={resume.id}>
                    <td>
                      <div style={{ fontWeight: 500 }}>{resume.candidate_name || 'Unknown'}</div>
                      {resume.email && (
                        <div style={{ fontSize: '0.8rem', color: 'var(--gray-400)' }}>{resume.email}</div>
                      )}
                    </td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--gray-500)' }}>
                      {resume.original_filename}
                    </td>
                    <td>
                      {(resume.extracted_skills || []).slice(0, 3).map(s => (
                        <span key={s} className="tag tag-primary" style={{ fontSize: '0.7rem', margin: '1px' }}>{s}</span>
                      ))}
                      {(resume.extracted_skills || []).length > 3 && (
                        <span className="tag tag-gray" style={{ fontSize: '0.7rem' }}>
                          +{resume.extracted_skills.length - 3}
                        </span>
                      )}
                    </td>
                    <td>{resume.experience_years || 0} yrs</td>
                    <td>{getScoreTag(resume.ats_score)}</td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--gray-400)' }}>
                      {formatDate(resume.created_at)}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => navigate(`/results/${resume.id}`)}
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                        >
                          View
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => setShowDelete(resume.id)}
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {showDelete && (
        <div className="modal-backdrop" onClick={() => setShowDelete(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginBottom: '12px' }}>Delete Resume</h3>
            <p style={{ color: 'var(--gray-500)', marginBottom: '20px' }}>
              Are you sure you want to delete this resume analysis?
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowDelete(null)}>Cancel</button>
              <button className="btn btn-danger" onClick={() => handleDelete(showDelete)}>Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ResumeList;