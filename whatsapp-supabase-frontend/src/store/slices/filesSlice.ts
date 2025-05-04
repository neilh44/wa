import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { getFiles as getFilesApi, createFile as createFileApi, syncFiles as syncFilesApi, FileData, FileCreateData, SyncResult } from '../../api/files';

interface FilesState {
  files: FileData[];
  loading: boolean;
  error: string | null;
  syncStatus: {
    syncing: boolean;
    lastSynced: string | null;
    result: SyncResult | null;
  };
}

const initialState: FilesState = {
  files: [],
  loading: false,
  error: null,
  syncStatus: {
    syncing: false,
    lastSynced: null,
    result: null,
  },
};

export const getFiles = createAsyncThunk(
  'files/getFiles',
  async (phoneNumber: string | undefined, { rejectWithValue }) => {
    try {
      return await getFilesApi(phoneNumber);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch files');
    }
  }
);

export const createFile = createAsyncThunk(
  'files/createFile',
  async (fileData: FileCreateData, { rejectWithValue }) => {
    try {
      return await createFileApi(fileData);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to create file');
    }
  }
);

export const syncFiles = createAsyncThunk(
  'files/syncFiles',
  async (_, { rejectWithValue }) => {
    try {
      return await syncFilesApi();
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to sync files');
    }
  }
);

const filesSlice = createSlice({
  name: 'files',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Get Files
      .addCase(getFiles.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getFiles.fulfilled, (state, action: PayloadAction<FileData[]>) => {
        state.loading = false;
        state.files = action.payload;
      })
      .addCase(getFiles.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Create File
      .addCase(createFile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createFile.fulfilled, (state, action: PayloadAction<FileData>) => {
        state.loading = false;
        state.files.push(action.payload);
      })
      .addCase(createFile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Sync Files
      .addCase(syncFiles.pending, (state) => {
        state.syncStatus.syncing = true;
        state.error = null;
      })
      .addCase(syncFiles.fulfilled, (state, action: PayloadAction<SyncResult>) => {
        state.syncStatus.syncing = false;
        state.syncStatus.lastSynced = new Date().toISOString();
        state.syncStatus.result = action.payload;
      })
      .addCase(syncFiles.rejected, (state, action) => {
        state.syncStatus.syncing = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError } = filesSlice.actions;
export default filesSlice.reducer;
