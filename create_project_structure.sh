#!/bin/bash

# Create WhatsApp to Supabase Project Structure
echo "Creating WhatsApp to Supabase Project Directory Structure..."

# Create Backend Structure
echo -e "\n--- Creating Backend Structure ---"
mkdir -p whatsapp-supabase-backend
cd whatsapp-supabase-backend

# Create app directory and its subdirectories
mkdir -p app/api
mkdir -p app/models
mkdir -p app/services
mkdir -p app/utils

# Create workers directory
mkdir -p workers

# Create tests directory
mkdir -p tests

# Create main files
touch app/main.py
touch app/config.py

# Create API files
touch app/api/auth.py
touch app/api/files.py
touch app/api/whatsapp.py
touch app/api/storage.py

# Create model files
touch app/models/user.py
touch app/models/file.py
touch app/models/session.py

# Create service files
touch app/services/auth_service.py
touch app/services/whatsapp_service.py
touch app/services/storage_service.py
touch app/services/file_service.py

# Create utility files
touch app/utils/logger.py
touch app/utils/security.py

# Create worker files
touch workers/whatsapp_monitor.py
touch workers/file_uploader.py

# Create other necessary files
touch .env.example
touch requirements.txt
touch Dockerfile

echo "Backend directory structure created successfully!"

# Return to parent directory
cd ..

# Create Frontend Structure
echo -e "\n--- Creating Frontend Structure ---"
mkdir -p whatsapp-supabase-frontend
cd whatsapp-supabase-frontend

# Create public directory
mkdir -p public

# Create src directory and its subdirectories
mkdir -p src/api
mkdir -p src/components/common
mkdir -p src/components/auth
mkdir -p src/components/files
mkdir -p src/components/whatsapp
mkdir -p src/components/storage
mkdir -p src/pages
mkdir -p src/store/slices
mkdir -p src/utils

# Create public files
touch public/index.html

# Create main files
touch src/index.tsx
touch src/App.tsx

# Create API files
touch src/api/auth.ts
touch src/api/files.ts
touch src/api/config.ts
touch src/api/supabase.ts

# Create component files
touch src/components/common/Button.tsx
touch src/components/common/Navbar.tsx
touch src/components/auth/LoginForm.tsx
touch src/components/files/FileList.tsx
touch src/components/whatsapp/SessionManager.tsx
touch src/components/storage/FileUploader.tsx

# Create page files
touch src/pages/Login.tsx
touch src/pages/Dashboard.tsx
touch src/pages/Files.tsx
touch src/pages/Settings.tsx

# Create store files
touch src/store/index.ts
touch src/store/slices/authSlice.ts
touch src/store/slices/filesSlice.ts

# Create utility files
touch src/utils/formatters.ts

# Create config files
touch package.json
touch tsconfig.json

echo "Frontend directory structure created successfully!"

echo -e "\n--- Project Structure Creation Complete ---"