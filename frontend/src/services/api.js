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

// Response interceptor: on 401, perform one silent refresh, retry request once
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Check if error is 401 and hasn't been retried yet
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      // Never attempt refresh on auth endpoints (login, register, token refresh itself)
      if (
        originalRequest.url.includes('/auth/token/') ||
        originalRequest.url.includes('/auth/register/') ||
        originalRequest.url.includes('/auth/token/refresh/')
      ) {
        return Promise.reject(error);
      }

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        logoutUser();
        window.dispatchEvent(new CustomEvent('session-expired'));
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const newAccessToken = response.data.access;
        localStorage.setItem('access_token', newAccessToken);
        if (response.data.refresh) {
          localStorage.setItem('refresh_token', response.data.refresh);
        }

        api.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;

        processQueue(null, newAccessToken);
        return api(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        logoutUser();
        window.dispatchEvent(new CustomEvent('session-expired'));
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// Video Analysis endpoints
export const previewVideo = async (url) => {
  const response = await api.get('/videos/preview/', {
    params: { url }
  });
  return response.data;
};

export const analyzeVideo = async (url, maxComments = 100, includeReplies = false) => {
  const payload = {
    url,
    max_comments: maxComments === 'all' || maxComments === null ? null : parseInt(maxComments, 10),
    include_replies: Boolean(includeReplies),
  };
  const response = await api.post('/videos/analyze/', payload);
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

export const getUserJobs = async (params = {}) => {
  const response = await api.get('/jobs/', { params });
  return response.data;
};

export const getMyAnalyses = async () => {
  const response = await api.get('/analyses/my/');
  return response.data;
};

export const compareVideos = async (job1Id, job2Id) => {
  const response = await api.get('/compare/', {
    params: { a: job1Id, b: job2Id }
  });
  return response.data;
};

export const getCompareInsights = async (job1Id, job2Id) => {
  const response = await api.post('/compare/insights/', {
    a: job1Id,
    b: job2Id,
  });
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

export const logoutUser = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  if (refreshToken) {
    try {
      await api.post('/auth/logout/', { refresh: refreshToken });
    } catch (e) {
      // Ignore network / blacklist errors during client sign out
    }
  }
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.dispatchEvent(new CustomEvent('user-logout'));
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
