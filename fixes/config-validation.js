// Run this with Node.js to validate your configuration before deploying
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('Validating configuration for WhatsApp-Supabase integration...');

// Check if .env files exist
const frontendEnvPath = path.join(process.cwd(), '.env.local');
const backendEnvPath = path.join(process.cwd(), '.env');

let hasErrors = false;

// Check frontend env
if (!fs.existsSync(frontendEnvPath)) {
  console.error('❌ Frontend .env.local file missing');
  hasErrors = true;
} else {
  const frontendEnv = fs.readFileSync(frontendEnvPath, 'utf8');
  
  if (!frontendEnv.includes('REACT_APP_SUPABASE_URL=')) {
    console.error('❌ REACT_APP_SUPABASE_URL missing in frontend .env.local');
    hasErrors = true;
  } else if (frontendEnv.includes('REACT_APP_SUPABASE_URL=your-project-id')) {
    console.error('❌ REACT_APP_SUPABASE_URL not configured in frontend .env.local');
    hasErrors = true;
  }
  
  if (!frontendEnv.includes('REACT_APP_SUPABASE_KEY=')) {
    console.error('❌ REACT_APP_SUPABASE_KEY missing in frontend .env.local');
    hasErrors = true;
  } else if (frontendEnv.includes('REACT_APP_SUPABASE_KEY=your-supabase-anon-key')) {
    console.error('❌ REACT_APP_SUPABASE_KEY not configured in frontend .env.local');
    hasErrors = true;
  }
}

// Check backend env
if (!fs.existsSync(backendEnvPath)) {
  console.error('❌ Backend .env file missing');
  hasErrors = true;
} else {
  const backendEnv = fs.readFileSync(backendEnvPath, 'utf8');
  
  if (!backendEnv.includes('SUPABASE_URL=')) {
    console.error('❌ SUPABASE_URL missing in backend .env');
    hasErrors = true;
  } else if (backendEnv.includes('SUPABASE_URL=your_supabase_url')) {
    console.error('❌ SUPABASE_URL not configured in backend .env');
    hasErrors = true;
  }
  
  if (!backendEnv.includes('SUPABASE_KEY=')) {
    console.error('❌ SUPABASE_KEY missing in backend .env');
    hasErrors = true;
  } else if (backendEnv.includes('SUPABASE_KEY=your_supabase_key')) {
    console.error('❌ SUPABASE_KEY not configured in backend .env');
    hasErrors = true;
  }
  
  if (!backendEnv.includes('SUPABASE_JWT_SECRET=')) {
    console.error('❌ SUPABASE_JWT_SECRET missing in backend .env');
    hasErrors = true;
  }
  
  if (!backendEnv.includes('APP_SECRET_KEY=')) {
    console.error('❌ APP_SECRET_KEY missing in backend .env');
    hasErrors = true;
  }
}

// Render specific checks
console.log('\nChecking Render deployment compatibility...');

// Check if a render.yaml exists
const renderYamlPath = path.join(process.cwd(), 'render.yaml');
if (!fs.existsSync(renderYamlPath)) {
  console.warn('⚠️ render.yaml not found - you will need to configure your Render services manually');
} else {
  console.log('✅ render.yaml found');
}

// Print summary
if (hasErrors) {
  console.log('\n❌ Configuration validation failed. Please fix the errors before deploying.');
} else {
  console.log('\n✅ Configuration validation passed. Your application should be ready for deployment.');
}

// Provide deployment instructions
console.log('\n--- DEPLOYMENT INSTRUCTIONS ---');
console.log('1. Fix any configuration errors shown above');
console.log('2. Apply the SQL schema to your Supabase project');
console.log('3. Set up the following environment variables in Render:');
console.log('   - SUPABASE_URL');
console.log('   - SUPABASE_KEY');
console.log('   - SUPABASE_JWT_SECRET');
console.log('   - APP_SECRET_KEY');
console.log('   - APP_DEBUG (set to false for production)');
console.log('4. Link your GitHub repository in Render');
console.log('5. Deploy both frontend and backend services');
