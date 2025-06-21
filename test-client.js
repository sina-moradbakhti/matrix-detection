// Simple Node.js test client for the 2D Datamatrix Detection Service
// Usage: node test-client.js <path-to-image>

const fs = require('fs');
const axios = require('axios');
const FormData = require('form-data');
const path = require('path');

// Configuration
const API_URL = 'http://localhost:5001';

// Check command line arguments
if (process.argv.length < 3) {
  console.error('Usage: node test-client.js <path-to-image>');
  process.exit(1);
}

const imagePath = process.argv[2];

// Ensure the image file exists
if (!fs.existsSync(imagePath)) {
  console.error(`Error: File ${imagePath} does not exist`);
  process.exit(1);
}

// Test file upload endpoint
async function testFileUpload() {
  console.log(`Testing file upload with ${imagePath}`);
  
  try {
    // Create form data with the image file
    const formData = new FormData();
    formData.append('image', fs.createReadStream(imagePath));
    
    // Send request to the detection service
    const response = await axios.post(`${API_URL}/detect`, formData, {
      headers: {
        ...formData.getHeaders(),
      },
    });
    
    // Process the response
    const result = response.data;
    console.log(`Success! Found ${result.count} codes`);
    console.log(`Image URL: ${result.image_url}`);
    
    // Print detected codes
    result.detected_codes.forEach((code, i) => {
      console.log(`Code ${i+1}:`);
      console.log(`  Method: ${code.method}`);
      console.log(`  Data: ${code.data}`);
      console.log(`  Type: ${code.type}`);
      console.log(`  Position:`, code.position);
      console.log();
    });
    
    return result;
  } catch (error) {
    console.error('Error:', error.response?.status || error.message);
    console.error(error.response?.data || error);
    return null;
  }
}

// Test base64 upload endpoint
async function testBase64Upload() {
  console.log(`Testing base64 upload with ${imagePath}`);
  
  try {
    // Read the image and encode it as base64
    const imageBuffer = fs.readFileSync(imagePath);
    const base64Image = imageBuffer.toString('base64');
    
    // Prepare the JSON payload
    const payload = {
      image: base64Image,
      include_image: true  // Include the processed image in the response
    };
    
    // Send request to the detection service
    const response = await axios.post(`${API_URL}/detect_base64`, payload, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Process the response
    const result = response.data;
    console.log(`Success! Found ${result.count} codes`);
    
    // Print detected codes
    result.detected_codes.forEach((code, i) => {
      console.log(`Code ${i+1}:`);
      console.log(`  Method: ${code.method}`);
      console.log(`  Data: ${code.data}`);
      console.log(`  Type: ${code.type}`);
      console.log(`  Position:`, code.position);
      console.log();
    });
    
    // Save the returned image if it's included
    if (result.image) {
      // Extract the base64 part
      const imgData = result.image.split(',')[1];
      const imgBuffer = Buffer.from(imgData, 'base64');
      
      // Save to file
      const outputPath = 'received_image.jpg';
      fs.writeFileSync(outputPath, imgBuffer);
      console.log(`Saved processed image to ${outputPath}`);
    }
    
    return result;
  } catch (error) {
    console.error('Error:', error.response?.status || error.message);
    console.error(error.response?.data || error);
    return null;
  }
}

// Run the tests
async function runTests() {
  console.log('=== Testing 2D Datamatrix Detection Service ===\n');
  
  // Test file upload
  await testFileUpload();
  
  console.log('\n' + '-'.repeat(50) + '\n');
  
  // Test base64 upload
  await testBase64Upload();
}

runTests().catch(console.error);