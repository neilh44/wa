#!/usr/bin/env node

/**
 * WhatsApp QR Code Error Identifier
 * 
 * This script analyzes errors in WhatsApp QR code generation and linking.
 * It checks API endpoints, QR code generation, and connection issues.
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const { execSync } = require('child_process');

// Configuration
const CONFIG = {
  // API endpoint to test - adjust this to match your backend
  apiBaseUrl: 'http://localhost:8000/api',
  // Path to debug logs
  debugLogPath: './whatsapp-debug-logs.txt',
  // Enable or disable specific tests
  tests: {
    apiConnectivity: true,
    backendLogs: true,
    qrCodeGeneration: true,
    chromeDriver: true,
    networkConnectivity: true
  }
};

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

// Initialize log file
fs.writeFileSync(CONFIG.debugLogPath, `WhatsApp QR Code Error Analysis - ${new Date().toISOString()}\n\n`, { flag: 'w' });

/**
 * Log a message to console and file
 */
function log(message, type = 'info') {
  const timestamp = new Date().toISOString();
  let coloredMessage;
  
  switch (type) {
    case 'error':
      coloredMessage = `${colors.red}[ERROR]${colors.reset} ${message}`;
      break;
    case 'warning':
      coloredMessage = `${colors.yellow}[WARNING]${colors.reset} ${message}`;
      break;
    case 'success':
      coloredMessage = `${colors.green}[SUCCESS]${colors.reset} ${message}`;
      break;
    case 'heading':
      coloredMessage = `\n${colors.bright}${colors.cyan}=== ${message} ===${colors.reset}\n`;
      break;
    default:
      coloredMessage = `[INFO] ${message}`;
  }
  
  console.log(coloredMessage);
  
  // Also log to file (without color codes)
  const plainMessage = `[${timestamp}] [${type.toUpperCase()}] ${message}\n`;
  fs.appendFileSync(CONFIG.debugLogPath, plainMessage);
}

/**
 * Parse debug data JSON file
 */
function parseDebugFile(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      log(`Debug file not found: ${filePath}`, 'error');
      return null;
    }
    
    const data = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    log(`Error parsing debug file: ${error.message}`, 'error');
    return null;
  }
}

/**
 * Test API connectivity
 */
async function testApiConnectivity() {
  log('Testing API connectivity', 'heading');
  
  const endpoints = [
    { url: '/', method: 'get', name: 'API Root' },
    { url: '/whatsapp/session', method: 'post', name: 'WhatsApp Session Initialization' },
    { url: '/files/', method: 'get', name: 'Files List' }
  ];
  
  let allSuccessful = true;
  
  for (const endpoint of endpoints) {
    try {
      log(`Testing endpoint: ${endpoint.name} (${endpoint.method.toUpperCase()} ${CONFIG.apiBaseUrl}${endpoint.url})`);
      
      // Get auth token if available
      const token = process.env.AUTH_TOKEN || localStorage?.getItem('token') || '';
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      const response = await axios({
        method: endpoint.method,
        url: `${CONFIG.apiBaseUrl}${endpoint.url}`,
        headers,
        timeout: 5000
      });
      
      log(`✓ ${endpoint.name} endpoint is accessible (Status: ${response.status})`, 'success');
    } catch (error) {
      allSuccessful = false;
      
      if (error.response) {
        log(`✗ ${endpoint.name} endpoint returned error status: ${error.response.status}`, 'error');
        log(`Response data: ${JSON.stringify(error.response.data)}`, 'error');
      } else if (error.request) {
        log(`✗ ${endpoint.name} endpoint could not be reached. No response received.`, 'error');
        log(`This indicates the API server is not running or is on a different URL.`, 'error');
      } else {
        log(`✗ Error testing ${endpoint.name} endpoint: ${error.message}`, 'error');
      }
    }
  }
  
  if (!allSuccessful) {
    log('API connectivity test failed. Please check your backend service.', 'error');
    log('Possible solutions:', 'warning');
    log('1. Ensure your backend server is running');
    log('2. Check if the API base URL is correct (currently set to: ' + CONFIG.apiBaseUrl + ')');
    log('3. Verify network connectivity between frontend and backend');
    log('4. Check for any CORS issues in browser console');
  }
  
  return allSuccessful;
}

/**
 * Test Chrome and ChromeDriver compatibility
 */
function testChromeDriver() {
  log('Testing Chrome and ChromeDriver', 'heading');
  
  try {
    // Get Chrome version
    let chromeVersion;
    try {
      if (process.platform === 'win32') {
        const output = execSync('reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version').toString();
        chromeVersion = output.match(/version\s+REG_SZ\s+([\d.]+)/i)[1];
      } else if (process.platform === 'darwin') {
        chromeVersion = execSync('/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version').toString();
      } else {
        chromeVersion = execSync('google-chrome --version').toString();
      }
      
      log(`Chrome version: ${chromeVersion}`);
    } catch (err) {
      log('Could not determine Chrome version. Make sure Chrome is installed.', 'warning');
    }
    
    // Check if ChromeDriver is installed
    try {
      const chromeDriverVersion = execSync('chromedriver --version').toString();
      log(`ChromeDriver version: ${chromeDriverVersion}`);
      
      if (chromeVersion && chromeDriverVersion) {
        // Compare major versions
        const chromeVerMajor = chromeVersion.match(/\d+/)[0];
        const driverVerMajor = chromeDriverVersion.match(/\d+/)[0];
        
        if (chromeVerMajor !== driverVerMajor) {
          log(`Chrome major version (${chromeVerMajor}) doesn't match ChromeDriver version (${driverVerMajor})`, 'warning');
          log('Version mismatch can cause issues with WhatsApp Web automation', 'warning');
          log('Solution: Install matching ChromeDriver for your Chrome version', 'warning');
        } else {
          log('Chrome and ChromeDriver versions appear compatible', 'success');
        }
      }
    } catch (err) {
      log('ChromeDriver not found in PATH. It needs to be installed or available.', 'error');
      log('Solution: Install ChromeDriver matching your Chrome version', 'warning');
    }
    
    return true;
  } catch (error) {
    log(`Error testing ChromeDriver: ${error.message}`, 'error');
    return false;
  }
}

/**
 * Test QR code generation
 */
async function testQRCodeGeneration(authToken) {
  log('Testing QR code generation', 'heading');
  
  try {
    log('Attempting to initialize WhatsApp session and get QR code');
    
    const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {};
    
    const response = await axios({
      method: 'post',
      url: `${CONFIG.apiBaseUrl}/whatsapp/session`,
      headers,
      timeout: 30000 // Longer timeout for QR code generation
    });
    
    if (response.data) {
      if (response.data.already_authenticated) {
        log('WhatsApp session is already authenticated', 'success');
        return true;
      } else if (response.data.qr_available && response.data.qr_data) {
        const qrDataLength = response.data.qr_data.length;
        log(`QR code generated successfully (data length: ${qrDataLength})`, 'success');
        
        // Check QR data quality
        if (qrDataLength < 1000) {
          log('QR data seems too short for a valid QR code', 'warning');
        } else {
          log('QR data length is reasonable');
          
          // Test base64 validity
          try {
            const decodedLength = Buffer.from(response.data.qr_data, 'base64').length;
            log(`Base64 decoded successfully (decoded length: ${decodedLength})`, 'success');
          } catch (e) {
            log('QR data is not valid base64', 'error');
          }
        }
        
        // Check if session ID is provided
        if (response.data.session_id) {
          log(`Session ID received: ${response.data.session_id}`, 'success');
        } else {
          log('No session ID in the response', 'error');
        }
        
        return true;
      } else {
        log('QR code not available in the response', 'error');
        log(`Response data: ${JSON.stringify(response.data)}`, 'error');
        return false;
      }
    } else {
      log('Empty response from server', 'error');
      return false;
    }
  } catch (error) {
    if (error.response) {
      log(`QR code generation failed with status: ${error.response.status}`, 'error');
      log(`Response data: ${JSON.stringify(error.response.data)}`, 'error');
    } else if (error.request) {
      log('No response received for QR code generation request', 'error');
    } else {
      log(`Error in QR code generation: ${error.message}`, 'error');
    }
    
    log('Possible solutions:', 'warning');
    log('1. Check if your backend WhatsAppService is properly configured');
    log('2. Verify Chrome and ChromeDriver versions are compatible');
    log('3. Check backend logs for Selenium or ChromeDriver errors');
    log('4. Try disabling headless mode temporarily for debugging');
    
    return false;
  }
}

/**
 * Test network connectivity to WhatsApp Web
 */
async function testWhatsAppWebConnectivity() {
  log('Testing connectivity to WhatsApp Web', 'heading');
  
  const whatsappEndpoints = [
    { url: 'https://web.whatsapp.com/', name: 'WhatsApp Web' },
    { url: 'https://static.whatsapp.net/rsrc.php', name: 'WhatsApp Static Resources' }
  ];
  
  let allSuccessful = true;
  
  for (const endpoint of whatsappEndpoints) {
    try {
      log(`Testing connectivity to ${endpoint.name}`);
      
      const response = await axios({
        method: 'get',
        url: endpoint.url,
        timeout: 10000
      });
      
      log(`✓ ${endpoint.name} is accessible (Status: ${response.status})`, 'success');
    } catch (error) {
      allSuccessful = false;
      
      if (error.response) {
        log(`${endpoint.name} returned status: ${error.response.status}`, 'warning');
      } else if (error.request) {
        log(`${endpoint.name} could not be reached. No response received.`, 'error');
        log('This indicates possible network connectivity issues to WhatsApp servers', 'error');
      } else {
        log(`Error testing ${endpoint.name}: ${error.message}`, 'error');
      }
    }
  }
  
  if (!allSuccessful) {
    log('WhatsApp Web connectivity test failed.', 'error');
    log('Possible solutions:', 'warning');
    log('1. Check your network connectivity');
    log('2. Verify your server has access to WhatsApp Web domains');
    log('3. Check if any proxy or firewall is blocking access');
  }
  
  return allSuccessful;
}

/**
 * Analyze debug log file
 */
function analyzeDebugFile(filePath) {
  log('Analyzing debug file', 'heading');
  
  const debugData = parseDebugFile(filePath);
  if (!debugData) return;
  
  log(`Debug data timestamp: ${debugData.timestamp}`);
  
  // Check API availability
  const apiErrors = debugData.logs.filter(log => 
    log.message.includes('API is not available') || 
    log.message.includes('404') ||
    log.message.includes('failed with status code')
  );
  
  if (apiErrors.length > 0) {
    log(`Found ${apiErrors.length} API-related errors`, 'error');
    log('API connection issues detected:', 'error');
    apiErrors.forEach(err => log(`- ${err.message}`, 'error'));
    
    log('Possible solutions:', 'warning');
    log('1. Ensure your backend server is running at the expected URL');
    log('2. Check API endpoints configuration in your frontend');
    log('3. Verify network connectivity between frontend and backend');
    log('4. Check for any CORS issues in browser console');
  }
  
  // Check QR code issues
  const qrErrors = debugData.logs.filter(log => 
    log.message.includes('QR') && 
    (log.message.includes('error') || log.message.includes('failed') || log.message.includes('not found'))
  );
  
  if (qrErrors.length > 0) {
    log(`Found ${qrErrors.length} QR code related errors`, 'error');
    qrErrors.forEach(err => log(`- ${err.message}`, 'error'));
    
    log('Possible QR code issues:', 'warning');
    log('1. QR code element not found in WhatsApp Web page');
    log('2. Canvas security restrictions in headless mode');
    log('3. QR code data extraction failed');
    log('4. Frontend rendering issues with base64 data');
  }
  
  // Check component details
  if (debugData.componentDetails) {
    if (debugData.componentDetails.found === false) {
      log('WhatsAppQRCode component not found in DOM', 'error');
      log('Make sure the component is properly imported and rendered', 'warning');
    }
    
    if (debugData.componentDetails.qrContainer === false) {
      log('QR container element not found in component', 'error');
      log('Check your component rendering structure', 'warning');
    }
    
    if (debugData.componentDetails.qrImage === false) {
      log('QR image element not found in container', 'error');
      log('Check your image rendering in the component', 'warning');
    }
  }
  
  // Summary
  log('\nDebug Analysis Summary:', 'heading');
  
  if (apiErrors.length > 0) {
    log('✗ API Connection Issues Detected', 'error');
  } else {
    log('✓ No API connection issues found in the logs', 'success');
  }
  
  if (qrErrors.length > 0) {
    log('✗ QR Code Generation Issues Detected', 'error');
  } else {
    log('✓ No QR code generation issues found in the logs', 'success');
  }
  
  if (debugData.componentDetails && Object.values(debugData.componentDetails).includes(false)) {
    log('✗ Frontend Component Issues Detected', 'error');
  } else {
    log('✓ No frontend component issues found', 'success');
  }
}

/**
 * Generate a comprehensive report
 */
function generateReport() {
  const reportPath = './whatsapp-qr-error-report.md';
  
  log('Generating detailed error report', 'heading');
  
  try {
    const reportContent = `# WhatsApp QR Code Error Analysis Report
Generated: ${new Date().toISOString()}

## Summary of Findings

${fs.readFileSync(CONFIG.debugLogPath, 'utf8')}

## Recommended Solutions

### API Connection Issues
- Verify the backend server is running at the correct URL (${CONFIG.apiBaseUrl})
- Check for any network connectivity issues between frontend and backend
- Ensure proper CORS configuration on the backend server
- Verify authentication token is valid and being sent correctly

### QR Code Generation Issues
- Update Chrome and ChromeDriver to matching versions
- Try disabling headless mode for debugging
- Add more logging in the backend to identify extraction failures
- Implement multiple fallback methods for QR code extraction

### Frontend Issues
- Verify the WhatsAppQRCode component is properly rendered
- Implement multiple rendering methods (img and canvas)
- Add error handling for QR code display
- Add a manual refresh button for the QR code

## Next Steps

1. Fix the identified issues
2. Run this script again to verify the fixes
3. Test WhatsApp QR code scanning with a real device
`;

    fs.writeFileSync(reportPath, reportContent);
    log(`Report generated successfully: ${reportPath}`, 'success');
  } catch (error) {
    log(`Error generating report: ${error.message}`, 'error');
  }
}

/**
 * Main function to run all tests
 */
async function main() {
  log('WhatsApp QR Code Error Identifier', 'heading');
  log(`Current date and time: ${new Date().toISOString()}`);
  log(`API base URL: ${CONFIG.apiBaseUrl}`);
  
  // Parse command line arguments
  const args = process.argv.slice(2);
  let debugFilePath = null;
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--debug-file' && i + 1 < args.length) {
      debugFilePath = args[i + 1];
      i++;
    } else if (args[i] === '--api-url' && i + 1 < args.length) {
      CONFIG.apiBaseUrl = args[i + 1];
      i++;
    } else if (args[i] === '--help') {
      console.log(`
WhatsApp QR Code Error Identifier

Usage:
  node whatsapp-error-identifier.js [options]

Options:
  --debug-file <path>    Path to the debug JSON file
  --api-url <url>        API base URL (default: ${CONFIG.apiBaseUrl})
  --help                 Show this help message
      `);
      return;
    }
  }
  
  // Analyze debug file if provided
  if (debugFilePath) {
    analyzeDebugFile(debugFilePath);
  }
  
  // Run tests
  let apiConnected = false;
  
  if (CONFIG.tests.apiConnectivity) {
    apiConnected = await testApiConnectivity();
  }
  
  if (CONFIG.tests.chromeDriver) {
    testChromeDriver();
  }
  
  if (CONFIG.tests.networkConnectivity) {
    await testWhatsAppWebConnectivity();
  }
  
  if (CONFIG.tests.qrCodeGeneration && apiConnected) {
    const token = process.env.AUTH_TOKEN || '';
    await testQRCodeGeneration(token);
  }
  
  // Generate report
  generateReport();
  
  log('\nAnalysis complete. Check the logs and report for details.', 'heading');
}

// Run the main function
main().catch(error => {
  log(`Unhandled error: ${error.message}`, 'error');
  console.error(error);
});