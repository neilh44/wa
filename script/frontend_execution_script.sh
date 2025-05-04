# WhatsApp to Supabase Frontend Setup Instructions

These instructions will guide you through setting up the frontend of the WhatsApp to Supabase file management system.

## Prerequisites

- Node.js 14 or higher
- npm or yarn
- Supabase account with a project created
- Backend API running (following the backend setup instructions)

## Setup Steps

1. **Create project structure**

   Run the directory structure script to create the project structure:
   ```bash
   chmod +x create_project_structure.sh
   ./create_project_structure.sh
   ```

2. **Set up frontend code**

   Run the frontend code script to create all the necessary code files:
   ```bash
   chmod +x frontend_code_script.sh
   ./frontend_code_script.sh
   ```

3. **Configure environment variables**

   Edit the `.env` file with your API and Supabase credentials:
   ```
   REACT_APP_API_URL=http://localhost:8000/api
   REACT_APP_SUPABASE_URL=https://asdomjuggbhzsmfcmwia.supabase.co
   REACT_APP_SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFzZG9tanVnZ2JoenNtZmNtd2lhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYzMjkyNzUsImV4cCI6MjA2MTkwNTI3NX0.6H7JnS8oW1_-9cnj24Gr0Ue5bbkbImeVgNzdSq6LFFg            
   ```

4. **Run the application**

   Use the execution script to run the application:
   ```bash
   chmod +x frontend_execution_script.sh