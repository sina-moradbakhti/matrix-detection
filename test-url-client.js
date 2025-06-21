// Test client for the URL-based image processing endpoint
// Usage: node test-url-client.js <image-url>

const axios = require('axios');

// Configuration
const API_URL = 'http://localhost:5001';

// Check command line arguments
if (process.argv.length < 3) {
  console.error('Usage: node test-url-client.js <image-url>');
  console.error('Example: node test-url-client.js https://example.com/path/to/image.jpg');
  process.exit(1);
}

const imageUrl = process.argv[2];

// Test URL endpoint
async function testUrlEndpoint() {
  console.log(`Testing URL endpoint with: ${imageUrl}`);
  
  try {
    // Send request to the detection service
    const response = await axios.post(`${API_URL}/detect_url`, {
      url: imageUrl,
      include_image: false  // Set to true if you want the processed image in response
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Process the response
    const result = response.data;
    console.log(`Success! Found ${result.count} codes`);
    console.log(`Source URL: ${result.source_url}`);
    console.log(`Processed Image URL: ${result.image_url}`);
    
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

// Test with include_image option
async function testUrlEndpointWithImage() {
  console.log(`Testing URL endpoint with image inclusion: ${imageUrl}`);
  
  try {
    // Send request to the detection service
    const response = await axios.post(`${API_URL}/detect_url`, {
      url: imageUrl,
      include_image: true  // Include processed image in response
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Process the response
    const result = response.data;
    console.log(`Success! Found ${result.count} codes`);
    
    // Save the returned image if it's included
    if (result.image) {
      const fs = require('fs');
      // Extract the base64 part
      const imgData = result.image.split(',')[1];
      const imgBuffer = Buffer.from(imgData, 'base64');
      
      // Save to file
      const outputPath = 'processed_from_url.jpg';
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
  console.log('=== Testing URL-based Image Processing ===\n');
  
  // Test basic URL processing
  await testUrlEndpoint();
  
  console.log('\n' + '-'.repeat(50) + '\n');
  
  // Test with image inclusion
  await testUrlEndpointWithImage();
}

runTests().catch(console.error);