import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadResume = async (file, targetRole = '') => {
  const formData = new FormData();
  formData.append('file', file);
  if (targetRole) {
    formData.append('target_role', targetRole);
  }
  const response = await api.post('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const listResumes = async (params = {}) => {
  const query = new URLSearchParams(params).toString();
  const response = await api.get(`/resumes/?${query}`);
  return response.data;
};

export const getResumeDetail = async (id) => {
  const response = await api.get(`/resumes/${id}/`);
  return response.data;
};

export const deleteResume = async (id) => {
  const response = await api.delete(`/resumes/${id}/delete/`);
  return response.data;
};

export const getDashboardStats = async () => {
  const response = await api.get('/dashboard/');
  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get('/health/');
  return response.data;
};

export default api;