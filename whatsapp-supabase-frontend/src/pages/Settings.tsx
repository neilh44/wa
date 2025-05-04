import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { 
  Typography, 
  Box, 
  Paper, 
  Divider, 
  List, 
  ListItem, 
  ListItemText, 
  Switch, 
  TextField, 
  Grid,
  Alert,
  Snackbar
} from '@mui/material';
import { RootState } from '../store';
import Button from '../components/common/Button';

const Settings: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const [settings, setSettings] = useState({
    autoDownload: true,
    autoUpload: true,
    notifyOnError: true,
    maxFileSize: 10,
    downloadInterval: 5
  });
  const [open, setOpen] = useState(false);

  const handleToggle = (setting: string) => () => {
    setSettings({
      ...settings,
      [setting]: !settings[setting as keyof typeof settings]
    });
  };

  const handleNumberChange = (setting: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value) || 0;
    setSettings({
      ...settings,
      [setting]: value
    });
  };

  const handleSave = () => {
    // In a real app, you'd save these settings to the backend
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <div>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Account Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            {user && (
              <List>
                <ListItem>
                  <ListItemText primary="Username" secondary={user.username} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Email" secondary={user.email} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Account Type" secondary={user.is_admin ? 'Administrator' : 'User'} />
                </ListItem>
              </List>
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              App Settings
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <List>
              <ListItem>
                <ListItemText 
                  primary="Auto Download Files" 
                  secondary="Automatically download files from WhatsApp" 
                />
                <Switch 
                  edge="end"
                  checked={settings.autoDownload}
                  onChange={handleToggle('autoDownload')}
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Auto Upload Files" 
                  secondary="Automatically upload files to Supabase" 
                />
                <Switch 
                  edge="end"
                  checked={settings.autoUpload}
                  onChange={handleToggle('autoUpload')}
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Error Notifications" 
                  secondary="Receive notifications on errors" 
                />
                <Switch 
                  edge="end"
                  checked={settings.notifyOnError}
                  onChange={handleToggle('notifyOnError')}
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Max File Size (MB)" 
                  secondary="Maximum file size to process" 
                />
                <TextField
                  type="number"
                  value={settings.maxFileSize}
                  onChange={handleNumberChange('maxFileSize')}
                  sx={{ width: 70 }}
                  size="small"
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Download Interval (minutes)" 
                  secondary="How often to check for new files" 
                />
                <TextField
                  type="number"
                  value={settings.downloadInterval}
                  onChange={handleNumberChange('downloadInterval')}
                  sx={{ width: 70 }}
                  size="small"
                />
              </ListItem>
            </List>
            
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="contained" onClick={handleSave}>
                Save Settings
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
      
      <Snackbar open={open} autoHideDuration={6000} onClose={handleClose}>
        <Alert onClose={handleClose} severity="success" sx={{ width: '100%' }}>
          Settings saved successfully
        </Alert>
      </Snackbar>
    </div>
  );
};

export default Settings;
