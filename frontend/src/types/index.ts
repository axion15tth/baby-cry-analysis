// Type definitions for the baby cry analysis system
export interface User {
  id: number;
  email: string;
  role: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  role?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Tag {
  id: number;
  name: string;
  created_at: string;
}

export interface AudioFile {
  id: number;
  user_id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  recording_start_time?: string;
  sample_rate?: number;
  duration?: number;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  uploaded_at: string;
  tags: Tag[];
}

export interface CryEpisode {
  start_time: number;
  end_time: number;
  duration: number;
  confidence: number;
}

export interface AcousticFeatures {
  time: number;
  f0?: number;
  f1?: number;
  f2?: number;
  f3?: number;
  hnr?: number;
  shimmer?: number;
  jitter?: number;
  intensity?: number;
}

export interface Statistics {
  mean?: number;
  std?: number;
  min?: number;
  max?: number;
  median?: number;
}

export interface CryUnit {
  start_time: number;
  end_time: number;
  duration: number;
  is_voiced: boolean;
  mean_energy: number;
  peak_frequency: number;
}

export interface CryUnitsData {
  units: CryUnit[];
  unit_count: number;
  cryCE: number;
  unvoicedCE: number;
}

export interface AnalysisResult {
  id: number;
  audio_file_id: number;
  result_data: {
    cry_episodes: CryEpisode[];
    acoustic_features: {
      [key: string]: AcousticFeatures[];
    };
    statistics: {
      [key: string]: {
        [param: string]: Statistics | number;
      };
    };
    cry_units?: {
      [key: string]: CryUnitsData;
    };
  };
  analyzed_at: string;
}

export interface AnalysisStatus {
  file_id: number;
  status: string;
  message: string;
  progress?: number;
  task_id?: string;
}
