import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getResumeDetail, deleteResume } from '../api';

function ScoreGauge({ score, label }) {
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const colors = {
    stroke: score >= 80 ? '#00b894' : score >= 60 ? '#6c5ce7' : score >= 40 ? '#fdcb6e' : '#e17055',
    glow: score >= 80 ? 'rgba(0,184,148,0.3)' : score >= 60 ? 'rgba(108,92,231,0.3)' : score >= 40 ? 'rgba(253,203,110,0.3)' : 'rgba(225,112,85,0.3)',
  };

  return (
    <div className="score-gauge">
      <svg viewBox="0 0 180 180">
        <circle className="score-gauge-bg" cx="90" cy="90" r={radius} />
        <circle
          className="score-gauge-fill"
          cx="90"
          cy="90"
          r={radius}
          stroke={colors.stroke}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ filter: `drop-shadow(0 0 8px ${colors.glow})` }}
        />
      </svg>
      <div className="score-value">
        <div className="number" style={{
          background: `linear-gradient(135deg, ${colors.stroke}, ${colors.stroke}cc)`,
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>{score.toFixed(0)}</div>
        <div className="label">{label}</div>
      </div>
    </div>
  );
}

function ScoreBar({ label, value, max = 100 }) {
  const pct = Math.min(100, (value / max) * 100);
  const level = pct >= 80 ? 'excellent' : pct >= 60 ? 'good' : pct >= 40 ? 'average' : 'poor';

  return (
    <div className="score-bar-group">
      <div className="score-bar-header">
        <span className="score-bar-label">{label}</span>
        <span className="score-bar-value">{value.toFixed(1)}</span>
      </div>
      <div className="score-bar">
        <div className={`score-bar-fill ${level}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function SuggestionCard({ suggestion }) {
  const priorityColors = {
    high: { bg: 'rgba(225, 112, 85, 0.1)', border: '#e17055', text: '#e17055', dot: '#e17055' },
    medium: { bg: 'rgba(253, 203, 110, 0.1)', border: '#fdcb6e', text: '#fdcb6e', dot: '#fdcb6e' },
    low: { bg: 'rgba(0, 184, 148, 0.1)', border: '#00b894', text: '#00b894', dot: '#00b894' },
  };
  const colors = priorityColors[suggestion.priority] || priorityColors.medium;

  return (
    <div className="suggestion-card" style={{
      background: colors.bg,
      borderLeft: `4px solid ${colors.border}`,
      borderRadius: 'var(--radius)',
      padding: '16px 20px',
      marginBottom: '12px',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
        <span style={{ fontSize: '1.3rem', flexShrink: 0 }}>{suggestion.icon || '💡'}</span>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{
              fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)',
            }}>{suggestion.title}</span>
            <span className="tag" style={{
              fontSize: '0.7rem',
              background: colors.dot,
              color: '#fff',
              padding: '1px 10px',
              borderRadius: '10px',
              fontWeight: 500,
              textTransform: 'capitalize',
            }}>{suggestion.priority}</span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
            {suggestion.recommendation}
          </p>
        </div>
      </div>
    </div>
  );
}

function Results() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDelete, setShowDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchResumeDetail();
  }, [id]);

  const fetchResumeDetail = async () => {
    try {
      setLoading(true);
      const data = await getResumeDetail(id);
      setResume(data);
    } catch (err) {
      setError('Failed to load resume analysis. It may have been deleted or the ID is invalid.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    try {
      setDeleting(true);
      await deleteResume(id);
      navigate('/resumes', { replace: true });
    } catch (err) {
      setError('Failed to delete resume.');
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fade-in">
        <div className="alert alert-error">{error}</div>
        <button className="btn btn-primary" onClick={() => navigate('/resumes')}>
          ← Back to Resume List
        </button>
      </div>
    );
  }

  if (!resume) return null;

  const atsScore = resume.ats_score || 0;
  const skills = resume.extracted_skills || [];
  const education = resume.education || [];
  const experienceList = resume.experience_list || [];
  const matchScores = resume.match_scores || [];
  const projectsList = resume.projects_list || [];
  const suggestions = resume.improvement_suggestions || [];

  return (
    <div className="fade-in">
      {/* Delete Confirmation Modal */}
      {showDelete && (
        <div className="modal-backdrop" onClick={() => setShowDelete(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginBottom: '12px', color: 'var(--text-primary)' }}>Delete Resume Analysis</h3>
            <p style={{ color: 'var(--text-muted)', marginBottom: '20px' }}>
              Are you sure you want to delete the analysis for "{resume.original_filename}"? This action cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowDelete(false)}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={handleDelete} disabled={deleting}>
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="page-header">
        <div>
          <h1>{resume.candidate_name || 'Resume Analysis'}</h1>
          <p style={{ color: 'var(--text-muted)' }}>{resume.original_filename}</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary" onClick={() => navigate('/resumes')}>
            ← All Resumes
          </button>
          <button className="btn btn-danger btn-sm" onClick={() => setShowDelete(true)}>
            🗑 Delete
          </button>
        </div>
      </div>

      {/* Improvement Suggestions Section */}
      {suggestions.length > 0 && (
        <div className="card suggestion-section" style={{ marginBottom: '24px' }}>
          <div className="card-header">
            <h3 className="card-title">
              <span style={{ marginRight: '8px' }}>💡</span>
              Improvement Suggestions ({suggestions.length})
            </h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Actionable tips to improve your resume
            </span>
          </div>
          <div style={{ maxHeight: '400px', overflowY: 'auto', paddingRight: '4px' }}>
            {suggestions.map((s, i) => (
              <SuggestionCard key={i} suggestion={s} />
            ))}
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="tabs" style={{ marginBottom: '20px' }}>
        <button
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button
          className={`tab-btn ${activeTab === 'skills' ? 'active' : ''}`}
          onClick={() => setActiveTab('skills')}
        >
          🛠️ Skills {skills.length > 0 && `(${skills.length})`}
        </button>
        <button
          className={`tab-btn ${activeTab === 'experience' ? 'active' : ''}`}
          onClick={() => setActiveTab('experience')}
        >
          💼 Experience {experienceList.length > 0 && `(${experienceList.length})`}
        </button>
        <button
          className={`tab-btn ${activeTab === 'education' ? 'active' : ''}`}
          onClick={() => setActiveTab('education')}
        >
          🎓 Education {education.length > 0 && `(${education.length})`}
        </button>
        <button
          className={`tab-btn ${activeTab === 'projects' ? 'active' : ''}`}
          onClick={() => setActiveTab('projects')}
        >
          📁 Projects {projectsList.length > 0 && `(${projectsList.length})`}
        </button>
        {suggestions.length > 0 && (
          <button
            className={`tab-btn ${activeTab === 'suggestions' ? 'active' : ''}`}
            onClick={() => setActiveTab('suggestions')}
          >
            💡 Suggestions ({suggestions.length})
          </button>
        )}
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Main Overview Grid */}
          <div className="grid-2" style={{ marginBottom: '24px' }}>
            <div className="card" style={{ textAlign: 'center' }}>
              <div className="card-header" style={{ justifyContent: 'center' }}>
                <h3 className="card-title">🎯 ATS Score</h3>
              </div>
              <ScoreGauge score={atsScore} label="Overall Score" />
              <div style={{ marginTop: '16px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {atsScore >= 80 ? '🌟 Excellent — Well optimized for ATS' :
                 atsScore >= 60 ? '👍 Good — Minor improvements recommended' :
                 atsScore >= 40 ? '⚠️ Average — Needs improvements' :
                 '❌ Poor — Significant changes needed'}
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="card-title">📊 Score Breakdown</h3>
              </div>
              <ScoreBar label="Format Score" value={resume.format_score || 0} />
              <ScoreBar label="Keyword Score" value={resume.keyword_score || 0} />
              <ScoreBar label="Experience Score" value={resume.experience_score || 0} />
              <ScoreBar label="Education Score" value={resume.education_score || 0} />
              <ScoreBar label="Skills Match Score" value={resume.skills_match_score || 0} />
            </div>
          </div>

          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-header">
              <h3 className="card-title">👤 Candidate Information</h3>
            </div>
            <div className="grid-2">
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '2px' }}>Name</div>
                <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{resume.candidate_name || 'Not detected'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '2px' }}>Email</div>
                <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{resume.email || 'Not detected'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '2px' }}>Phone</div>
                <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{resume.phone || 'Not detected'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '2px' }}>Experience</div>
                <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{resume.experience_years || 0} years</div>
              </div>
            </div>
          </div>

          {matchScores.length > 0 && (
            <div className="card" style={{ marginBottom: '24px' }}>
              <div className="card-header">
                <h3 className="card-title">🎯 Job Role Matching</h3>
              </div>
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Role</th>
                      <th>Match Score</th>
                      <th>Matched Skills</th>
                      <th>Missing Skills</th>
                      <th>Exp. Gap (yrs)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {matchScores.map((match, i) => (
                      <tr key={i}>
                        <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{match.role}</td>
                        <td>
                          <span className={`tag ${
                            match.score >= 70 ? 'tag-success' :
                            match.score >= 50 ? 'tag-warning' :
                            'tag-danger'
                          }`}>
                            {match.score.toFixed(0)}%
                          </span>
                        </td>
                        <td>
                          {(match.matched_skills || []).slice(0, 4).map(s => (
                            <span key={s} className="tag tag-success" style={{ fontSize: '0.75rem' }}>{s}</span>
                          ))}
                        </td>
                        <td>
                          {(match.missing_skills || []).slice(0, 4).map(s => (
                            <span key={s} className="tag tag-gray" style={{ fontSize: '0.75rem' }}>{s}</span>
                          ))}
                        </td>
                        <td style={{ color: 'var(--text-secondary)' }}>{match.experience_gap || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {resume.suggested_roles?.length > 0 && (
            <div className="card" style={{ marginBottom: '24px' }}>
              <div className="card-header">
                <h3 className="card-title">⭐ Top Suggested Roles</h3>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {resume.suggested_roles.map((role, i) => (
                  <span key={role} className={`tag ${i === 0 ? 'tag-primary' : 'tag-gray'}`}>
                    {i === 0 ? '⭐ ' : ''}{role}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {activeTab === 'skills' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <span style={{ marginRight: '8px' }}>🛠️</span>
              Extracted Skills ({skills.length})
            </h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Skills and technologies detected in the resume
            </span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {skills.length > 0 ? skills.map(skill => (
              <span key={skill} className="tag tag-primary" style={{ fontSize: '0.85rem', padding: '6px 14px' }}>
                {skill}
              </span>
            )) : (
              <div style={{ textAlign: 'center', padding: '40px 20px', width: '100%', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: '3rem', marginBottom: '12px' }}>🛠️</div>
                <p style={{ fontWeight: 500, margin: '0 0 6px 0', color: 'var(--text-secondary)' }}>No Skills Detected</p>
                <p style={{ fontSize: '0.85rem', margin: 0 }}>
                  No skills were extracted from this resume. Consider adding a dedicated skills section.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'experience' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <span style={{ marginRight: '8px' }}>💼</span>
              Work Experience {experienceList.length > 0 && `(${experienceList.length})`}
            </h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Professional experience entries extracted from resume
            </span>
          </div>

          {experienceList.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {experienceList.map((exp, i) => (
                <div key={i} style={{
                  padding: '16px',
                  borderBottom: i < experienceList.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                  transition: 'var(--transition)',
                  borderRadius: i === experienceList.length - 1 ? '0 0 var(--radius) var(--radius)' : '0',
                }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                      {exp.title || 'Position'}
                    </div>
                    {exp.dates && (
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', marginLeft: '12px' }}>
                        📅 {exp.dates}
                      </span>
                    )}
                  </div>
                  {exp.company && (
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      🏢 {exp.company}
                    </div>
                  )}
                  {exp.description && (
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '8px 0 0 0' }}>
                      {exp.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '3rem', marginBottom: '12px' }}>💼</div>
              <p style={{ fontWeight: 500, margin: '0 0 6px 0', color: 'var(--text-secondary)' }}>No Work Experience Detected</p>
              <p style={{ fontSize: '0.85rem', margin: 0 }}>
                No experience entries were found. Adding detailed work experience can improve your ATS score.
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'education' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <span style={{ marginRight: '8px' }}>🎓</span>
              Education {education.length > 0 && `(${education.length})`}
            </h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Educational qualifications extracted from resume
            </span>
          </div>

          {education.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {education.map((edu, i) => (
                <div key={i} style={{
                  padding: '16px',
                  borderBottom: i < education.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                  transition: 'var(--transition)',
                }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.95rem', marginBottom: '4px' }}>
                    {edu.degree}
                  </div>
                  {edu.institution && (
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '2px' }}>
                      🏛️ {edu.institution}
                    </div>
                  )}
                  {edu.year && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      📅 {edu.year}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '3rem', marginBottom: '12px' }}>🎓</div>
              <p style={{ fontWeight: 500, margin: '0 0 6px 0', color: 'var(--text-secondary)' }}>No Education Detected</p>
              <p style={{ fontSize: '0.85rem', margin: 0 }}>
                No education details were extracted. Consider adding your educational qualifications.
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'suggestions' && (
        <div className="card suggestion-section">
          <div className="card-header">
            <h3 className="card-title">
              <span style={{ marginRight: '8px' }}>💡</span>
              Improvement Suggestions ({suggestions.length})
            </h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Actionable tips to improve your resume
            </span>
          </div>
          <div style={{ maxHeight: '600px', overflowY: 'auto', paddingRight: '4px' }}>
            {suggestions.length > 0 ? suggestions.map((s, i) => (
              <SuggestionCard key={i} suggestion={s} />
            )) : (
              <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: '3rem', marginBottom: '12px' }}>💡</div>
                <p style={{ fontWeight: 500, margin: 0, color: 'var(--text-secondary)' }}>No suggestions available</p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'projects' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <span style={{ marginRight: '8px' }}>📁</span>
              Projects {projectsList.length > 0 && `(${projectsList.length})`}
            </h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Extracted project entries from resume
            </span>
          </div>

          {projectsList.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {projectsList.map((project, i) => (
                <div key={i} className="project-card" style={{
                  padding: '20px',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-secondary)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <h4 style={{ margin: 0, color: 'var(--text-primary)', fontSize: '1rem', fontWeight: 600 }}>
                      {project.title}
                    </h4>
                    {project.dates && (
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', marginLeft: '12px' }}>
                        📅 {project.dates}
                      </span>
                    )}
                  </div>

                  {project.description && (
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 10px 0' }}>
                      {project.description}
                    </p>
                  )}

                  {project.technologies && project.technologies.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '8px' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginRight: '4px', alignSelf: 'center' }}>
                        🛠️
                      </span>
                      {project.technologies.map((tech, j) => (
                        <span key={j} className="tag tag-info" style={{ fontSize: '0.75rem' }}>
                          {tech}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '3rem', marginBottom: '12px' }}>📁</div>
              <p style={{ fontWeight: 500, margin: '0 0 6px 0', color: 'var(--text-secondary)' }}>No Projects Detected</p>
              <p style={{ fontSize: '0.85rem', margin: 0 }}>
                A dedicated Projects section was not found in this resume. Adding one can improve your ATS score.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Results;