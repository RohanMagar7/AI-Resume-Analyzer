import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDashboardStats } from '../api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

const SCORE_COLORS = {
  excellent: '#00b894',
  good: '#6c5ce7',
  average: '#fdcb6e',
  poor: '#e17055',
};

const chartTooltipStyle = {
  background: '#1e1e36',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: '8px',
  color: '#f0f0ff',
};

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: '#1e1e36',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: '8px',
        padding: '10px 14px',
        color: '#f0f0ff',
        fontSize: '0.85rem',
        boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
      }}>
        <p style={{ margin: 0, fontWeight: 600 }}>{`${label}`}</p>
        <p style={{ margin: '4px 0 0', color: '#a29bfe' }}>{`${payload[0].value}`}</p>
      </div>
    );
  }
  return null;
}

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await getDashboardStats();
      setStats(data);
    } catch (err) {
      setError('Failed to load dashboard stats. Is the backend server running?');
    } finally {
      setLoading(false);
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
        <div className="page-header">
          <div>
            <h1>Dashboard</h1>
            <p>AI Resume Analyzer — Analytics Overview</p>
          </div>
        </div>
        <div className="alert alert-error">{error}</div>
        <div className="card" style={{ textAlign: 'center', padding: '60px' }}>
          <p style={{ marginBottom: '16px', color: 'var(--text-muted)' }}>
            Make sure the Django backend is running on port 8000.
          </p>
          <button className="btn btn-primary" onClick={fetchStats}>
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const hasData = stats && stats.total_resumes > 0;
  const scoreDist = stats?.score_distribution || {};
  const pieData = hasData ? [
    { name: 'Excellent (80-100)', value: scoreDist.excellent, color: '#00b894' },
    { name: 'Good (60-79)', value: scoreDist.good, color: '#6c5ce7' },
    { name: 'Average (40-59)', value: scoreDist.average, color: '#fdcb6e' },
    { name: 'Poor (0-39)', value: scoreDist.poor, color: '#e17055' },
  ].filter(item => item.value > 0) : [];

  const roleData = stats?.role_distribution
    ? Object.entries(stats.role_distribution).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>AI Resume Analyzer — Analytics Overview</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-icon">📄</span>
          <div className="stat-value">{stats?.total_resumes || 0}</div>
          <div className="stat-label">Resumes Analyzed</div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">⭐</span>
          <div className="stat-value">{stats?.avg_ats_score || 0}</div>
          <div className="stat-label">Average ATS Score</div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">💼</span>
          <div className="stat-value">{stats?.avg_experience_years || 0} yrs</div>
          <div className="stat-label">Avg Experience</div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">🏆</span>
          <div className="stat-value">{stats?.top_skills?.length || 0}</div>
          <div className="stat-label">Unique Skills Found</div>
        </div>
      </div>

      {!hasData ? (
        <div className="card" style={{ textAlign: 'center', padding: '80px 24px' }}>
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M9 12h6M12 9v6M3 12a9 9 0 1 1 18 0 9 9 0 0 1-18 0z" />
            </svg>
            <h3>No Resumes Analyzed Yet</h3>
            <p style={{ marginBottom: '20px' }}>
              Upload your first resume to see analytics and insights.
            </p>
            <button className="btn btn-primary" onClick={() => navigate('/upload')}>
              Upload Resume
            </button>
          </div>
        </div>
      ) : (
        <div className="grid-2">
          {/* Score Distribution Pie */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">📊 ATS Score Distribution</h3>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={65}
                  outerRadius={110}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ value }) => `${value}`}
                  labelLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  formatter={(value) => <span style={{ color: '#a0a0c0', fontSize: '0.8rem' }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Top Skills */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">🏆 Top Skills Across Resumes</h3>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', padding: '12px 0' }}>
              {stats?.top_skills?.map((skill, index) => (
                <span key={skill} className={`tag ${index < 5 ? 'tag-primary' : 'tag-gray'}`}>
                  {skill}
                </span>
              ))}
            </div>
            {stats?.top_skills?.length === 0 && (
              <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>
                No skills extracted yet
              </p>
            )}
          </div>

          {/* Role Distribution Bar Chart */}
          {roleData.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">🎯 Job Role Matching Distribution</h3>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={roleData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis
                    dataKey="name"
                    fontSize={11}
                    angle={-20}
                    textAnchor="end"
                    height={60}
                    tick={{ fill: '#a0a0c0' }}
                  />
                  <YAxis tick={{ fill: '#a0a0c0' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar
                    dataKey="value"
                    fill="#6c5ce7"
                    radius={[4, 4, 0, 0]}
                    barSize={30}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Recent Analyses */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">📋 Recent Analyses</h3>
            </div>
            {stats?.recent_analyses?.length > 0 ? (
              <div>
                {stats.recent_analyses.map((resume) => (
                  <div
                    key={resume.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '14px 0',
                      borderBottom: '1px solid rgba(255,255,255,0.04)',
                      cursor: 'pointer',
                      transition: 'var(--transition)',
                    }}
                    className="hover-row"
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    onClick={() => navigate(`/results/${resume.id}`)}
                  >
                    <div>
                      <div style={{ fontWeight: 500, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                        {resume.candidate_name || 'Unknown'}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {resume.original_filename}
                      </div>
                    </div>
                    <div>
                      <span className={`tag ${resume.ats_score >= 80 ? 'tag-success' : resume.ats_score >= 60 ? 'tag-primary' : resume.ats_score >= 40 ? 'tag-warning' : 'tag-danger'}`}>
                        {resume.ats_score?.toFixed(0) || 'N/A'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>
                No recent analyses
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;