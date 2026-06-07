import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import Upload from './components/Upload';
import Results from './components/Results';
import ResumeList from './components/ResumeList';

function App() {
  return (
    <Router>
      <Navbar />
      <div className="container" style={{ paddingBottom: '48px' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/results/:id" element={<Results />} />
          <Route path="/resumes" element={<ResumeList />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;