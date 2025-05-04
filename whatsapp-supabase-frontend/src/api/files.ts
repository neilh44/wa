import axios from 'axios';
import config from './config';

// Types
export interface FileData {
  id: string;
  filename: string;
  phone_number: string;
  size?: number;
  mime_type?: string;
  storage_path: string;
  uploaded: boolean;
  created_at: string;
}

export interface FileCreateData {
  filename: string;
  phone_number: string;
  size?: number;
  mime_type?: string;
}

export interface SyncResult {
  message: string;
  files_synced: number;
  total_missing: number;
}

// Files API functions
export const getFiles = async (phoneNumber?: string): Promise<FileData[]> => {
  const params = phoneNumber ? { phone_number: phoneNumber } : {};
  const response = await axios.get(config.FILES.BASE, { params });
  return response.data;
};

export const createFile = async (fileData: FileCreateData): Promise<FileData> => {
  const response = await axios.post(config.FILES.BASE, fileData);
  return response.data;
};

export const syncFiles = async (): Promise<SyncResult> => {
  const response = await axios.post(config.FILES.SYNC);
  return response.data;
};
