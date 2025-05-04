const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export default {
  API_URL,
  AUTH: {
    LOGIN: `${API_URL}/login`,
    REGISTER: `${API_URL}/register`,
    ME: `${API_URL}/me`,
  },
  FILES: {
    BASE: `${API_URL}/files`,
    SYNC: `${API_URL}/files/sync`,
  },
  WHATSAPP: {
    SESSION: `${API_URL}/whatsapp/session`,
    DOWNLOAD: `${API_URL}/whatsapp/download`,
  },
  STORAGE: {
    UPLOAD: `${API_URL}/storage/upload`,
    MISSING: `${API_URL}/storage/missing`,
  },
};
