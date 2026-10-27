import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT access token to requests if present in localStorage
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Video Analysis endpoints
export const analyzeVideo = async (url, maxComments = 100) => {
  const response = await api.post('/videos/analyze/', {
    url,
    max_comments: maxComments,
  });
  return response.data;
};

export const getJobStatus = async (jobId) => {
  const response = await api.get(`/jobs/${jobId}/status/`);
  return response.data;
};

export const getReport = async (jobId) => {
  const response = await api.get(`/reports/${jobId}/`);
  return response.data;
};

export const getRecentReports = async () => {
  const response = await api.get('/reports/recent/');
  return response.data;
};

export const getMyAnalyses = async () => {
  const response = await api.get('/analyses/my/');
  return response.data;
};

export const compareVideos = async (job1Id, job2Id) => {
  const response = await api.get(`/analyses/compare/?job1=${job1Id}&job2=${job2Id}`);
  return response.data;
};

export const draftCommentReply = async (commentId) => {
  const response = await api.post(`/comments/${commentId}/draft-reply/`);
  return response.data;
};

export const getVideoComments = async (videoId, params = {}) => {
  const response = await api.get(`/videos/${videoId}/comments/`, { params });
  return response.data;
};

export const getExportUrl = (jobId, format = 'csv') => {
  return `${API_BASE_URL}/reports/${jobId}/export/?format=${format}`;
};

// Authentication helpers
export const registerUser = async (username, email, password) => {
  const response = await api.post('/auth/register/', { username, email, password });
  if (response.data.tokens?.access) {
    localStorage.setItem('access_token', response.data.tokens.access);
    localStorage.setItem('refresh_token', response.data.tokens.refresh);
    localStorage.setItem('user', JSON.stringify(response.data.user));
  }
  return response.data;
};

export const loginUser = async (username, password) => {
  const response = await api.post('/auth/token/', { username, password });
  if (response.data.access) {
    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);
    const meResponse = await api.get('/auth/me/');
    localStorage.setItem('user', JSON.stringify(meResponse.data));
    return { tokens: response.data, user: meResponse.data };
  }
  return response.data;
};

export const getCurrentUser = async () => {
  const token = localStorage.getItem('access_token');
  if (!token) return null;
  try {
    const response = await api.get('/auth/me/');
    localStorage.setItem('user', JSON.stringify(response.data));
    return response.data;
  } catch (err) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    return null;
  }
};

export const logoutUser = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

export const getStoredUser = () => {
  try {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  } catch (e) {
    return null;
  }
};

export default api;
