const fs = require('fs');
const path = require('path');

// Check if .env file exists
const envPath = path.join(process.cwd(), '.env');
const envExists = fs.existsSync(envPath);

console.log('==========================================');
console.log('Checking environment variables');
console.log('==========================================');
console.log(`.env file exists: ${envExists ? 'Yes' : 'No'}`);

if (envExists) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  const lines = envContent.split('\n').filter(line => line.trim() !== '' && !line.startsWith('#'));
  
  console.log('\nEnvironment variables found:');
  lines.forEach(line => {
    const [key] = line.split('=');
    console.log(`- ${key}: ${line.includes('=') ? 'Has value' : 'No value'}`);
  });
  
  // Check for required Supabase variables
  const hasSupabaseUrl = lines.some(line => line.startsWith('REACT_APP_SUPABASE_URL='));
  const hasSupabaseKey = lines.some(line => line.startsWith('REACT_APP_SUPABASE_ANON_KEY='));
