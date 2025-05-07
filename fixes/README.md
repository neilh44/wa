# WhatsApp-Supabase Authentication Fix

This directory contains fixes for the authentication issues in the WhatsApp-Supabase integration.

## Common Authentication Issues

1. **Invalid Manifest**: The application's manifest.json has syntax errors.
2. **Supabase Authentication Error**: Invalid login credentials or configuration.
3. **Backend Authentication Error**: 401 Unauthorized from the backend API.
4. **Missing Auth Session**: No active authentication session in Supabase.

## How to Apply Fixes

Run the installation script:

```bash
./install-fixes.sh
```

## Required Environment Variables

### Frontend (.env.local)
```
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_SUPABASE_URL=https://your-project-id.supabase.co
REACT_APP_SUPABASE_KEY=your-supabase-anon-key
```

### Backend (.env)
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
APP_SECRET_KEY=your-app-secret-key
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000
WHATSAPP_DATA_DIR=./whatsapp_data
```

## Deploying to Render

1. Make sure your configuration is valid by running:
   ```
   node fixes/config-validation.js
   ```

2. Set up your database schema in Supabase:
   - Run the SQL in `fixes/supabase-setup.sql` in the Supabase SQL Editor
   - Create a storage bucket named `whatsapp_files` in Supabase

3. Connect your GitHub repository to Render and deploy using the `render.yaml` configuration

4. Set up the required environment variables in Render as specified in the validation script output

## Troubleshooting

If you experience issues after applying these fixes:

1. Check the browser console for errors
2. Verify your Supabase credentials
3. Confirm your backend API is accessible
4. Review the backend logs for detailed error messages
5. Ensure your Supabase tables are properly created
