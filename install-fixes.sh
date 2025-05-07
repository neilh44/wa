#!/bin/bash

# Script to apply fixes to the WhatsApp-Supabase project
echo "Applying authentication fixes..."

# Apply frontend fixes
echo "Applying frontend fixes..."
cp fixes/frontend/manifest.json public/manifest.json
cp fixes/frontend/auth.ts src/api/auth.ts
cp fixes/frontend/supabase.ts src/api/supabase.ts
cp fixes/frontend/.env.local .env.local

# Apply backend fixes
echo "Applying backend fixes..."
cp fixes/backend/auth_service.py app/services/auth_service.py

# Copy configuration files
echo "Copying configuration files..."
cp fixes/render.yaml render.yaml

echo "✅ Fixes applied successfully!"
echo ""
echo "Next steps:"
echo "1. Update .env.local with your Supabase credentials"
echo "2. Update .env with your Supabase credentials"
echo "3. Run the Supabase SQL script in your Supabase SQL editor"
echo "4. Run 'node fixes/config-validation.js' to validate your configuration"
echo "5. Follow the deployment instructions for Render"
