import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useDispatch } from 'react-redux';
import { Box, Paper, Typography, Alert, LinearProgress, Divider, List, ListItem, ListItemText, Snackbar } from '@mui/material';
import { syncFiles } from '../../store/slices/filesSlice';
import { AppDispatch } from '../../store';
import config from '../../api/config';
import Button from '../common/Button';
import { formatFileSize, formatPhoneNumber } from '../../utils/formatters';

interface FileInfo {
  id: string;
  filename: string;
  phone_number: string;
  size?: number;
  mime_type?: string;
  uploaded: boolean;
}

const FileUploader: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<{ type: 'info' | 'success' | 'error' | 'warning', text: string } | null>(null);
  const [missingFiles, setMissingFiles] = useState<FileInfo[]>([]);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Helper to show temporary messages
  const showSnackbar = (message: string) => {
    setSnackbarMessage(message);
    setSnackbarOpen(true);
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  const getMissingFiles = async () => {
    console.log('Fetching missing files...');
    setLoading(true);
    
    try {
      // Check for authentication token
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No authentication token found');
        setMessage({
          type: 'error',
          text: 'Authentication token is missing. Please log in again.'
        });
        return;
      }
      
      // Make API request with explicit auth header
      const response = await axios.get(config.STORAGE.MISSING, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      console.log('Missing files response:', response.data);
      
      if (Array.isArray(response.data)) {
        setMissingFiles(response.data);
        setMessage({
          type: 'info',
          text: `Found ${response.data.length} files pending upload`
        });
      } else {
        console.warn('Unexpected response format:', response.data);
        setMissingFiles(response.data?.files || []);
        setMessage({
          type: 'info',
          text: `Found ${response.data?.files?.length || 0} files pending upload`
        });
      }
    } catch (error) {
      console.error('API Error:', error);
      
      if (axios.isAxiosError(error)) {
        console.error('Error response:', error.response?.data);
        console.error('Error status:', error.response?.status);
        
        if (error.response?.status === 401) {
          setMessage({
            type: 'error',
            text: 'Your session has expired. Please log in again.'
          });
          // Clear the token if it's invalid
          localStorage.removeItem('token');
        } else {
          setMessage({
            type: 'error',
            text: `Failed to fetch missing files: ${error.response?.data?.detail || error.message || 'Unknown error'}`
          });
        }
      } else {
        setMessage({
          type: 'error',
          text: 'Network error. Please check your connection.'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadFiles = async () => {
    console.log('Downloading files from WhatsApp...');
    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(config.WHATSAPP.DOWNLOAD, {}, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      console.log('Download response:', response.data);
      
      if (response.data.files && response.data.files.length > 0) {
        showSnackbar(`Downloaded ${response.data.files.length} files successfully`);
        setMessage({
          type: 'success',
          text: `Downloaded ${response.data.files.length} files successfully`
        });
      } else {
        showSnackbar('No new files found to download');
        setMessage({
          type: 'info',
          text: 'No new files found to download'
        });
      }
      
      // Refresh the files list
      await getMissingFiles();
    } catch (error) {
      console.error('Download Error:', error);
      
      if (axios.isAxiosError(error)) {
        console.error('Error response:', error.response?.data);
        
        if (error.response?.status === 401) {
          setMessage({
            type: 'error',
            text: 'Your session has expired. Please log in again.'
          });
        } else {
          setMessage({
            type: 'error',
            text: `Download failed: ${error.response?.data?.detail || error.message || 'Unknown error'}`
          });
        }
      } else {
        setMessage({
          type: 'error',
          text: 'Network error during download. Please check your connection.'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    console.log('Syncing files...');
    setSyncing(true);
    
    try {
      // Use Redux action for syncing
      const result = await dispatch(syncFiles()).unwrap();
      console.log('Sync result:', result);
      
      setMessage({
        type: 'success',
        text: result.message || 'Files synchronized successfully'
      });
      
      showSnackbar(`Synced ${result.files_synced} files`);
      
      // Refresh the missing files list
      await getMissingFiles();
    } catch (error) {
      console.error('Sync failed:', error);
      
      if (typeof error === 'string') {
        setMessage({
          type: 'error',
          text: error
        });
      } else {
        setMessage({
          type: 'error',
          text: 'Failed to synchronize files'
        });
      }
    } finally {
      setSyncing(false);
    }
  };

  // Load files when component mounts
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      getMissingFiles();
    } else {
      console.warn('No auth token found, cannot fetch files');
      setMessage({
        type: 'warning',
        text: 'Please login to access file management'
      });
    }
  }, []);

  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h6" gutterBottom>
        File Synchronization
      </Typography>
      
      <Divider sx={{ mb: 2 }} />
      
      {message && (
        <Box sx={{ mb: 3 }}>
          <Alert severity={message.type}>
            {message.text}
          </Alert>
        </Box>
      )}
      
      {(loading || syncing) && (
        <Box sx={{ width: '100%', mb: 3 }}>
          <LinearProgress />
        </Box>
      )}
      
      <Box sx={{ mb: 3 }}>
        {missingFiles.length > 0 ? (
          <List>
            {missingFiles.slice(0, 5).map((file) => (
              <ListItem key={file.id} divider>
                <ListItemText
                  primary={file.filename}
                  secondary={`${formatPhoneNumber(file.phone_number)} - ${formatFileSize(file.size)}`}
                />
              </ListItem>
            ))}
            {missingFiles.length > 5 && (
              <ListItem>
                <ListItemText
                  primary={`${missingFiles.length - 5} more files...`}
                />
              </ListItem>
            )}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary" align="center">
            No pending files
          </Typography>
        )}
      </Box>
      
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Button
          variant="outlined"
          onClick={getMissingFiles}
          loading={loading}
        >
          Check Pending Files
        </Button>
        
        <Button
          variant="contained"
          color="secondary"
          onClick={handleDownloadFiles}
          loading={loading}
        >
          Download From WhatsApp
        </Button>
        
        <Button
          variant="contained"
          onClick={handleSync}
          loading={syncing}
          disabled={missingFiles.length === 0}
        >
          Synchronize Files
        </Button>
      </Box>
      
      {/* Notification Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        message={snackbarMessage}
      />
    </Paper>
  );
};

export default FileUploader;