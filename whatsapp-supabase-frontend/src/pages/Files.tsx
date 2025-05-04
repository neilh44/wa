import React from 'react';
import { Typography, Box } from '@mui/material';
import FileList from '../components/files/FileList';

const Files: React.FC = () => {
  return (
    <div>
      <Typography variant="h4" component="h1" gutterBottom>
        File Management
      </Typography>
      <Box sx={{ mb: 4 }}>
        <Typography variant="body1" color="text.secondary" paragraph>
          Manage files downloaded from WhatsApp. Files are organized by phone number and automatically uploaded to Supabase storage.
        </Typography>
      </Box>
      <FileList />
    </div>
  );
};

export default Files;
