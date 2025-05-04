import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper, 
  Typography, 
  TextField, 
  InputAdornment,
  IconButton,
  Box,
  Chip
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import { getFiles } from '../../store/slices/filesSlice';
import { AppDispatch, RootState } from '../../store';
import { formatDate, formatFileSize, formatPhoneNumber } from '../../utils/formatters';
import Button from '../common/Button';

const FileList: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { files, loading } = useSelector((state: RootState) => state.files);
  const [phoneFilter, setPhoneFilter] = useState('');
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    dispatch(getFiles(undefined));
  }, [dispatch]);

  const handleRefresh = () => {
    dispatch(getFiles(phoneFilter || undefined));
  };

  const handlePhoneSearch = () => {
    setPhoneFilter(searchText);
    dispatch(getFiles(searchText || undefined));
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
  };

  const handleSearchKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handlePhoneSearch();
    }
  };

  const filteredFiles = files.filter(file => 
    !phoneFilter || file.phone_number.includes(phoneFilter)
  );

  return (
    <div>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Files
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            placeholder="Search by phone number"
            size="small"
            value={searchText}
            onChange={handleSearchChange}
            onKeyPress={handleSearchKeyPress}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={handlePhoneSearch}>
                    <SearchIcon />
                  </IconButton>
                </InputAdornment>
              )
            }}
          />
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />} 
            onClick={handleRefresh}
            loading={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {phoneFilter && (
        <Box sx={{ mb: 2 }}>
          <Chip 
            label={`Filtering by: ${formatPhoneNumber(phoneFilter)}`} 
            onDelete={() => {
              setPhoneFilter('');
              setSearchText('');
              dispatch(getFiles(undefined));
            }} 
          />
        </Box>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>File Name</TableCell>
              <TableCell>Phone Number</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Upload Status</TableCell>
              <TableCell>Date</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredFiles.length > 0 ? (
              filteredFiles.map((file) => (
                <TableRow key={file.id}>
                  <TableCell>{file.filename}</TableCell>
                  <TableCell>{formatPhoneNumber(file.phone_number)}</TableCell>
                  <TableCell>{formatFileSize(file.size)}</TableCell>
                  <TableCell>{file.mime_type || 'Unknown'}</TableCell>
                  <TableCell>
                    <Chip 
                      label={file.uploaded ? 'Uploaded' : 'Pending'} 
                      color={file.uploaded ? 'success' : 'warning'} 
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{formatDate(file.created_at)}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No files found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
};

export default FileList;
