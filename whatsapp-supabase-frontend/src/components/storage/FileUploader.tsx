import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useDispatch } from 'react-redux';
import { Box, Paper, Typography, Alert, LinearProgress, Divider, List, ListItem, ListItemText } from '@mui/material';
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

  const getMissingFiles = async () => {
    setLoading(true);
    try {
      const response = await axios.get(config.STORAGE.MISSING);
      setMissingFiles(response.data.files || []);
      setMessage({
        type: 'info',
        text: `Found ${response.data.files.length} files pending upload`
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Failed to fetch missing files'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await dispatch(syncFiles());
      setMessage({
        type: 'success',
        text: 'Files synchronized successfully'
      });
      // Refresh the missing files list
      await getMissingFiles();
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Failed to synchronize files'
      });
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    // Get missing files on initial load
    getMissingFiles();
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
      
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Button
          variant="outlined"
          onClick={getMissingFiles}
          loading={loading}
        >
          Check Pending Files
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
    </Paper>
  );
};

export default FileUploader;
