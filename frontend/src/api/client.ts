import axios from 'axios';
import type {
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  User,
  AudioFile,
  AnalysisResult,
  AnalysisStatus,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// リクエストインターセプター: トークンを自動付与
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  console.log('API Request:', config.method?.toUpperCase(), config.url);
  return config;
});

// レスポンスインターセプター: エラーログ
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Error:', error.message);
    if (error.response) {
      console.error('Error Response:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('No response received:', error.request);
    }
    return Promise.reject(error);
  }
);

// 認証API
export const authAPI = {
  register: async (data: RegisterRequest): Promise<User> => {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },

  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login', data);
    return response.data;
  },

  me: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};

// ファイル管理API
export const filesAPI = {
  upload: async (file: File, recordingStartTime?: string): Promise<{ file: AudioFile }> => {
    const formData = new FormData();
    formData.append('file', file);
    if (recordingStartTime) {
      formData.append('recording_start_time', recordingStartTime);
    }

    const response = await api.post<{ file: AudioFile }>('/audio-files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  list: async (skip = 0, limit = 100): Promise<{ total: number; files: AudioFile[] }> => {
    const response = await api.get<{ total: number; files: AudioFile[] }>('/audio-files/', {
      params: { skip, limit },
    });
    return response.data;
  },

  get: async (id: number): Promise<AudioFile> => {
    const response = await api.get<AudioFile>(`/audio-files/${id}`);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/audio-files/${id}`);
  },
};

// 解析API
export const analysisAPI = {
  start: async (fileId: number): Promise<AnalysisStatus> => {
    const response = await api.post<AnalysisStatus>('/analysis/start', {
      file_id: fileId,
    });
    return response.data;
  },

  status: async (fileId: number): Promise<AnalysisStatus> => {
    const response = await api.get<AnalysisStatus>(`/analysis/status/${fileId}`);
    return response.data;
  },

  results: async (fileId: number): Promise<AnalysisResult[]> => {
    const response = await api.get<AnalysisResult[]>(`/analysis/results/${fileId}`);
    return response.data;
  },
};

// エクスポートAPI
export const exportAPI = {
  episodesCSV: (fileId: number): string => {
    return `${API_URL}/export/csv/episodes/${fileId}`;
  },

  featuresCSV: (fileId: number, episodeId: string): string => {
    return `${API_URL}/export/csv/features/${fileId}/${episodeId}`;
  },

  excel: (fileId: number): string => {
    return `${API_URL}/export/excel/${fileId}`;
  },

  pdf: (fileId: number): string => {
    return `${API_URL}/export/pdf/${fileId}`;
  },
};

// 可視化API
export const visualizationAPI = {
  getWaveform: async (fileId: number, episodeId?: string): Promise<any> => {
    const params = episodeId ? { episode_id: episodeId } : {};
    const response = await api.get(`/visualization/waveform/${fileId}`, { params });
    return response.data;
  },

  getSpectrogram: async (fileId: number, episodeId?: string): Promise<any> => {
    const params = episodeId ? { episode_id: episodeId } : {};
    const response = await api.get(`/visualization/spectrogram/${fileId}`, { params });
    return response.data;
  },
};

export default api;
