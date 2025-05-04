import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Typography, Grid, Paper, Box, Alert } from '@mui/material';
import { getFiles } from '../store/slices/filesSlice';
import { AppDispatch, RootState } from '../store';
import SessionManager from '../components/whatsapp/SessionManager';
import FileUploader from '../components/storage/FileUploader';

const Dashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { files } = useSelector((state: RootState) => state.files);
  const { user } = useSelector((state: RootState) => state.auth);
  const [stats, setStats] = useState({
    totalFiles: 0,
    uploadedFiles: 0,
    pendingFiles: 0,
    uniquePhoneNumbers: 0
  });

  useEffect(() => {
    dispatch(getFiles(undefined));
  }, [dispatch]);

  useEffect(() => {
    if (files.length > 0) {
      const uploadedFiles = files.filter(file => file.uploaded).length;
      const pendingFiles = files.length - uploadedFiles;
      const uniquePhoneNumbers = new Set(files.map(file => file.phone_number)).size;
      
      setStats({
        totalFiles: files.length,
        uploadedFiles,
        pendingFiles,
        uniquePhoneNumbers
      });
    }
  }, [files]);

  return (
    <div>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      {user && (
        <Box sx={{ mb: 3 }}>
          <Alert severity="info">
            Welcome, {user.username}! Your WhatsApp to Supabase integration is ready.
          </Alert>
        </Box>
      )}
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              Total Files
            </Typography>
            <Typography component="p" variant="h4">
              {stats.totalFiles}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              Uploaded
            </Typography>
            <Typography component="p" variant="h4">
              {stats.uploadedFiles}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              Pending
            </Typography>
            <Typography component="p" variant="h4">
              {stats.pendingFiles}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              Phone Numbers
            </Typography>
            <Typography component="p" variant="h4">
              {stats.uniquePhoneNumbers}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <SessionManager />
        </Grid>
        <Grid item xs={12} md={6}>
          <FileUploader />
        </Grid>
      </Grid>
    </div>
  );
};

export default Dashboard;
