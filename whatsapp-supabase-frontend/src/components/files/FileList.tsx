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
  Chip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Modal,
  Button as MuiButton
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import VisibilityIcon from '@mui/icons-material/Visibility';
import FileOpenIcon from '@mui/icons-material/FileOpen';
import CloseIcon from '@mui/icons-material/Close';
import DownloadIcon from '@mui/icons-material/Download';
// Import the supabase client directly from your API file
import { supabase } from '../../api/supabase';
import { getFiles } from '../../store/slices/filesSlice';
import { AppDispatch, RootState } from '../../store';
import { formatDate, formatFileSize, formatPhoneNumber } from '../../utils/formatters';
import Button from '../common/Button';

// Add a new interface for our grouped files
interface GroupedFiles {
  [phoneNumber: string]: {
    files: any[];
    totalSize: number;
    totalFiles: number;
  }
}

const FileList: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { files, loading, error } = useSelector((state: RootState) => state.files);
  const [phoneFilter, setPhoneFilter] = useState('');
  const [searchText, setSearchText] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [groupedFiles, setGroupedFiles] = useState<GroupedFiles>({});
  const [expandedGroup, setExpandedGroup] = useState<string | false>(false);
  const [viewingFile, setViewingFile] = useState<any | null>(null);
  const [fileViewModalOpen, setFileViewModalOpen] = useState<boolean>(false);
  
  // Log supabase connection
  useEffect(() => {
    console.log('Supabase client available:', !!supabase);
  }, []);

  useEffect(() => {
    // Fetch files without token check - connecting directly to data source
    console.log('Fetching files on component mount...');
    dispatch(getFiles(undefined))
      .unwrap()
      .then(() => {
        setLocalError(null);
      })
      .catch((err) => {
        console.error('Error fetching files:', err);
        // Don't show token-related errors to the user
        if (err && typeof err === 'string' && !err.includes('token')) {
          setLocalError(err);
        } else if (err && !String(err).includes('token')) {
          setLocalError('Failed to fetch files. Please try again.');
        }
      });
      
    // Check if supabase storage is accessible
    testSupabaseStorage();
  }, [dispatch]);
  
  // Function to test Supabase storage access
  const testSupabaseStorage = async () => {
    try {
      console.log('Testing Supabase storage access...');
      
      // List buckets
      const { data: buckets, error: bucketError } = await supabase.storage.listBuckets();
      
      if (bucketError) {
        console.error('Error listing buckets:', bucketError);
        return;
      }
      
      console.log('Available buckets:', buckets?.map(b => b.name) || 'None');
      
      // Try to find the whatsapp-files bucket
      const whatsappBucket = buckets?.find(b => b.name === 'whatsapp-files');
      
      if (whatsappBucket) {
        console.log('Found whatsapp-files bucket:', whatsappBucket);
        
        // List files in the root folder
        const { data: rootFiles, error: listError } = await supabase.storage
          .from('whatsapp-files')
          .list('', { sortBy: { column: 'name', order: 'asc' } });
          
        if (listError) {
          console.error('Error listing files in bucket root:', listError);
        } else {
          console.log('Files in whatsapp-files bucket root:', rootFiles?.length || 0, 'files found');
          if (rootFiles && rootFiles.length > 0) {
            console.log('First few files/folders in root:', rootFiles.slice(0, 5));
            
            // Check if there are any folders that might be phone numbers
            const potentialPhoneFolders = rootFiles.filter(f => f.id && f.name && f.name.match(/^[0-9]+$/));
            
            if (potentialPhoneFolders.length > 0) {
              console.log('Found potential phone number folders:', potentialPhoneFolders.slice(0, 3));
              
              // Check contents of the first phone folder to understand structure
              if (potentialPhoneFolders[0]) {
                const { data: phoneFiles, error: phoneError } = await supabase.storage
                  .from('whatsapp-files')
                  .list(potentialPhoneFolders[0].name);
                  
                if (phoneError) {
                  console.error(`Error listing files in folder ${potentialPhoneFolders[0].name}:`, phoneError);
                } else {
                  console.log(`Files in folder ${potentialPhoneFolders[0].name}:`, phoneFiles);
                }
              }
            } else {
              console.log('No phone number folders found in root. Storage might be using a different structure.');
            }
          }
        }
      } else {
        console.warn('whatsapp-files bucket not found! Available buckets:', buckets?.map(b => b.name).join(', '));
        
        // If whatsapp-files bucket doesn't exist, try the first available bucket
        if (buckets && buckets.length > 0) {
          const firstBucket = buckets[0].name;
          console.log(`Trying first available bucket: ${firstBucket}`);
          
          const { data: files, error: listError } = await supabase.storage
            .from(firstBucket)
            .list();
            
          if (listError) {
            console.error(`Error listing files in ${firstBucket}:`, listError);
          } else {
            console.log(`Files in ${firstBucket}:`, files);
          }
        }
      }
      
    } catch (err) {
      console.error('Error testing Supabase storage:', err);
    }
  };

  useEffect(() => {
    // Group files by phone number
    const groups: GroupedFiles = {};
    
    // Always filter locally to ensure UI is responsive
    const filteredFiles = files.filter(file => 
      !phoneFilter || file.phone_number.includes(phoneFilter)
    );
    
    filteredFiles.forEach(file => {
      if (!groups[file.phone_number]) {
        groups[file.phone_number] = {
          files: [],
          totalSize: 0,
          totalFiles: 0
        };
      }
      
      groups[file.phone_number].files.push(file);
      groups[file.phone_number].totalSize += file.size || 0;
      groups[file.phone_number].totalFiles += 1;
    });
    
    setGroupedFiles(groups);
  }, [files, phoneFilter]);

  const handleRefresh = () => {
    console.log('Refreshing files...');
    dispatch(getFiles(phoneFilter || undefined))
      .unwrap()
      .then(() => {
        setLocalError(null);
      })
      .catch((err) => {
        console.error('Error refreshing files:', err);
        // Don't show token-related errors
        if (typeof err === 'string' && !err.includes('token')) {
          setLocalError(err);
        } else if (!String(err).includes('token')) {
          setLocalError('Failed to refresh files. Please try again.');
        }
      });
  };

  const handlePhoneSearch = () => {
    setPhoneFilter(searchText);
    console.log('Searching files by phone number:', searchText);
    dispatch(getFiles(searchText || undefined))
      .unwrap()
      .then(() => {
        setLocalError(null);
      })
      .catch((err) => {
        console.error('Error searching files:', err);
        // Don't show token-related errors
        if (typeof err === 'string' && !err.includes('token')) {
          setLocalError(err);
        } else if (!String(err).includes('token')) {
          setLocalError('Failed to search files. Please try again.');
        }
      });
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
  };

  const handleSearchKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handlePhoneSearch();
    }
  };

  const handleAccordionChange = (phoneNumber: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedGroup(isExpanded ? phoneNumber : false);
  };
  
  const handleViewFile = async (file: any) => {
    try {
      // Get the file URL using Supabase storage
      const bucketName = 'whatsapp-files';
      
      // Since files are not organized by phone number, just use the filename directly
      const filePath = file.filename;
      
      console.log('Attempting to get public URL for file:', {
        bucket: bucketName,
        path: filePath,
        fileInfo: {
          id: file.id,
          name: file.filename
        }
      });
      
      // Try to list files in the root to verify file exists
      try {
        const { data: rootFiles, error: listError } = await supabase.storage
          .from(bucketName)
          .list();
          
        if (listError) {
          console.error(`Error listing files in bucket:`, listError);
        } else {
          console.log(`Files in bucket:`, rootFiles?.map(f => f.name));
          // Check if file exists in the directory
          const fileExists = rootFiles?.some(f => f.name === file.filename);
          console.log(`File ${file.filename} exists in bucket: ${fileExists}`);
        }
      } catch (listErr) {
        console.error(`Error listing files:`, listErr);
      }
      
      // Fetch the file URL directly through Supabase
      const { data } = supabase.storage.from(bucketName).getPublicUrl(filePath);
      
      console.log('Public URL response:', data);
      
      if (!data || !data.publicUrl) {
        throw new Error('Could not generate public URL for file');
      }
      
      console.log('Successfully got public URL:', data.publicUrl);
      
      // Store the URL with the viewing file for use in the modal
      setViewingFile({
        ...file,
        publicUrl: data.publicUrl
      });
      
      setFileViewModalOpen(true);
    } catch (err) {
      console.error('Error preparing file for view:', err);
      setLocalError(`Could not view file: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };
  
  const handleCloseFileView = () => {
    setFileViewModalOpen(false);
    setViewingFile(null);
  };
  
  const handleDownloadFile = async (file: any) => {
    try {
      // Use Supabase to download the file
      const bucketName = 'whatsapp-files';
      
      // Since files are not organized by phone number, use the filename directly
      const filePath = file.filename;
      
      console.log(`Attempting to download file:`, {
        bucket: bucketName,
        path: filePath,
        fileInfo: {
          id: file.id,
          name: file.filename,
          size: file.size
        }
      });
      
      // Try to list files in the bucket to see if the file exists
      try {
        const { data: files, error: listError } = await supabase.storage
          .from(bucketName)
          .list();
          
        if (listError) {
          console.error('Error listing files:', listError);
        } else {
          console.log(`Available files in bucket:`, files?.map(f => f.name));
          const fileExists = files?.some(f => f.name === file.filename);
          console.log(`File ${file.filename} exists in bucket: ${fileExists}`);
        }
      } catch (listErr) {
        console.error('Error listing files:', listErr);
      }
      
      // Try to find the correct bucket if whatsapp-files doesn't exist
      const { data: buckets } = await supabase.storage.listBuckets();
      console.log('Available buckets:', buckets?.map(b => b.name));
      
      // Check if whatsapp-files exists
      const correctBucket = buckets?.find(b => b.name === 'whatsapp-files')?.name || 
                          (buckets && buckets.length > 0 ? buckets[0].name : bucketName);
                          
      console.log(`Using bucket: ${correctBucket}`);
      
      // Download the file using Supabase storage
      const { data, error } = await supabase
        .storage
        .from(correctBucket)
        .download(filePath);
        
      if (error) {
        console.error('Error downloading file:', error);
        
        // Try alternative paths
        const alternativePaths = [
          file.storage_path,
          `uploads/${file.filename}`,
          `public/${file.filename}`,
          // Try original ID as filename
          file.id
        ].filter(Boolean);
        
        console.log('Trying alternative paths:', alternativePaths);
        
        let downloadSuccess = false;
        let downloadedData = null;
        
        for (const altPath of alternativePaths) {
          console.log(`Trying path: ${altPath}`);
          const { data: altData, error: altError } = await supabase
            .storage
            .from(correctBucket)
            .download(altPath);
            
          if (altError) {
            console.log(`Path ${altPath} failed:`, altError);
          } else if (altData) {
            console.log(`Path ${altPath} succeeded! File size: ${altData.size} bytes`);
            downloadSuccess = true;
            downloadedData = altData;
            break;
          }
        }
        
        if (!downloadSuccess) {
          setLocalError(`Failed to download file: ${error.message}`);
          return;
        }
        
        if (!downloadedData) {
          setLocalError('No file data received.');
          return;
        }
        
        // Create a URL for the downloaded blob
        const url = URL.createObjectURL(downloadedData);
        
        // Create a temporary link and trigger download
        const a = document.createElement('a');
        a.href = url;
        a.download = file.filename || 'download';
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        console.log('Download triggered successfully via alternative path');
        return;
      }
      
      if (!data) {
        console.error('No file data received');
        setLocalError('No file data received.');
        return;
      }
      
      console.log('File download successful, size:', data.size);
      
      // Create a URL for the downloaded blob
      const url = URL.createObjectURL(data);
      
      // Create a temporary link and trigger download
      const a = document.createElement('a');
      a.href = url;
      a.download = file.filename || 'download';
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      console.log('Download triggered successfully');
      
    } catch (err) {
      console.error('Error in download process:', err);
      setLocalError(`Failed to download file: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

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

      {(error || localError) && (
        <Box sx={{ mb: 3 }}>
          <Alert severity="error">
            {error || localError}
          </Alert>
        </Box>
      )}

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

      {loading ? (
        <Box sx={{ p: 4, textAlign: 'center' }}>
          <Typography>Loading files...</Typography>
        </Box>
      ) : Object.keys(groupedFiles).length === 0 ? (
        <Box sx={{ p: 4, textAlign: 'center' }}>
          <Typography>No files found</Typography>
        </Box>
      ) : (
        <Box sx={{ mb: 2 }}>
          {Object.entries(groupedFiles).map(([phoneNumber, group]) => (
            <Accordion 
              key={phoneNumber}
              expanded={expandedGroup === phoneNumber}
              onChange={handleAccordionChange(phoneNumber)}
              sx={{ mb: 2 }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                aria-controls={`panel-${phoneNumber}-content`}
                id={`panel-${phoneNumber}-header`}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                  <Typography sx={{ fontWeight: 'bold' }}>
                    {formatPhoneNumber(phoneNumber)}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Chip 
                      label={`${group.totalFiles} Files`} 
                      size="small" 
                      color="primary"
                    />
                    <Chip 
                      label={`Total: ${formatFileSize(group.totalSize)}`} 
                      size="small" 
                      color="secondary"
                    />
                  </Box>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>File Name</TableCell>
                        <TableCell>Size</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Upload Status</TableCell>
                        <TableCell>Date</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {group.files.map((file) => (
                        <TableRow key={file.id}>
                          <TableCell>{file.filename}</TableCell>
                          <TableCell>{formatFileSize(file.size || 0)}</TableCell>
                          <TableCell>{file.mime_type || 'Unknown'}</TableCell>
                          <TableCell>
                            <Chip 
                              label={file.uploaded ? 'Uploaded' : 'Pending'} 
                              color={file.uploaded ? 'success' : 'warning'} 
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{formatDate(file.created_at)}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <IconButton 
                                size="small" 
                                color="primary" 
                                onClick={() => handleViewFile(file)}
                                title="View File"
                              >
                                <VisibilityIcon fontSize="small" />
                              </IconButton>
                              <IconButton 
                                size="small" 
                                color="secondary" 
                                onClick={() => handleDownloadFile(file)}
                                title="Download File"
                              >
                                <DownloadIcon fontSize="small" />
                              </IconButton>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}
      
      {/* File Viewer Modal */}
      <Modal
        open={fileViewModalOpen}
        onClose={handleCloseFileView}
        aria-labelledby="file-view-modal"
        aria-describedby="modal-to-view-file-contents"
      >
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '80%',
          maxWidth: 800,
          bgcolor: 'background.paper',
          boxShadow: 24,
          p: 4,
          maxHeight: '80vh',
          overflow: 'auto',
          borderRadius: 1,
        }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" component="h2">
              {viewingFile?.filename}
            </Typography>
            <IconButton onClick={handleCloseFileView} aria-label="close">
              <CloseIcon />
            </IconButton>
          </Box>
          
          <Divider sx={{ mb: 2 }} />
          
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
              <Chip icon={<FileOpenIcon />} label={viewingFile?.mime_type || 'Unknown type'} />
              <Chip label={`Size: ${formatFileSize(viewingFile?.size || 0)}`} />
              <Chip label={`Uploaded: ${formatDate(viewingFile?.created_at)}`} />
            </Box>
            
            <MuiButton
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={() => viewingFile && handleDownloadFile(viewingFile)}
              sx={{ mr: 1 }}
            >
              Download
            </MuiButton>
          </Box>
          
          <Divider sx={{ mb: 2 }} />
          
          <Box sx={{ mt: 2 }}>
            {viewingFile && (
              <>
                {/* Render file preview based on mime type */}
                {viewingFile.mime_type?.includes('image/') ? (
                  // Image preview
                  <Box sx={{ textAlign: 'center' }}>
                    {viewingFile.publicUrl ? (
                      <img 
                        src={viewingFile.publicUrl}
                        alt={viewingFile.filename}
                        style={{ maxWidth: '100%', maxHeight: '50vh' }}
                      />
                    ) : (
                      <Typography color="error">
                        Error loading image preview. Please try downloading the file instead.
                      </Typography>
                    )}
                  </Box>
                ) : viewingFile.mime_type?.includes('application/pdf') ? (
                  // PDF preview
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    {viewingFile.publicUrl ? (
                      <>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          PDF preview:
                        </Typography>
                        <iframe
                          src={viewingFile.publicUrl}
                          title={viewingFile.filename}
                          width="100%"
                          height="500px"
                          style={{ border: 'none' }}
                        />
                      </>
                    ) : (
                      <Typography color="error">
                        Error loading PDF preview. Please try downloading the file instead.
                      </Typography>
                    )}
                  </Box>
                ) : (
                  // Default case for other file types
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      Preview not available for this file type. Please download the file to view its contents.
                    </Typography>
                  </Box>
                )}
              </>
            )}
          </Box>
        </Box>
      </Modal>
    </div>
  );
};

export default FileList;