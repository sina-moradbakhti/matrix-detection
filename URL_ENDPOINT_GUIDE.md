# URL-Based Image Processing Endpoint

## Overview

The service now includes a new endpoint `/detect_url` that allows you to process images directly from URLs. This is perfect for scenarios where images are already uploaded in another system and you want to process them without re-uploading.

## New Endpoint: `/detect_url`

**Method:** POST  
**Content-Type:** application/json

### Request Format

```json
{
  "url": "https://example.com/path/to/image.jpg",
  "include_image": false
}
```

### Parameters

- `url` (required): The URL of the image to process
- `include_image` (optional): Boolean, if true, includes the processed image as base64 in the response

### Response Format

```json
{
  "detected_codes": [
    {
      "method": "pyzbar",
      "data": "Detected text content",
      "type": "DATAMATRIX",
      "position": {
        "x": 100,
        "y": 200,
        "width": 50,
        "height": 50,
        "polygon": [[100, 200], [150, 200], [150, 250], [100, 250]]
      }
    }
  ],
  "count": 1,
  "image_url": "/download/result_filename.jpg",
  "source_url": "https://example.com/path/to/image.jpg"
}
```

## Usage Examples

### JavaScript/Node.js

```javascript
const axios = require('axios');

// Basic usage
const response = await axios.post('http://localhost:5001/detect_url', {
  url: 'https://example.com/student-photo.jpg'
});

console.log(`Found ${response.data.count} codes`);
console.log('Detected codes:', response.data.detected_codes);

// With processed image included
const responseWithImage = await axios.post('http://localhost:5001/detect_url', {
  url: 'https://example.com/student-photo.jpg',
  include_image: true
});

// Save the processed image
if (responseWithImage.data.image) {
  const fs = require('fs');
  const imgData = responseWithImage.data.image.split(',')[1];
  const imgBuffer = Buffer.from(imgData, 'base64');
  fs.writeFileSync('processed_image.jpg', imgBuffer);
}
```

### Python

```python
import requests
import base64

# Basic usage
response = requests.post('http://localhost:5001/detect_url', 
                        json={'url': 'https://example.com/student-photo.jpg'})

result = response.json()
print(f"Found {result['count']} codes")
print("Detected codes:", result['detected_codes'])

# With processed image included
response_with_image = requests.post('http://localhost:5001/detect_url', 
                                   json={
                                       'url': 'https://example.com/student-photo.jpg',
                                       'include_image': True
                                   })

result = response_with_image.json()
if 'image' in result:
    # Save the processed image
    img_data = result['image'].split(',')[1]
    with open('processed_image.jpg', 'wb') as f:
        f.write(base64.b64decode(img_data))
```

### cURL

```bash
# Basic usage
curl -X POST -H "Content-Type: application/json" \
     -d '{"url":"https://example.com/student-photo.jpg"}' \
     http://localhost:5001/detect_url

# With processed image included
curl -X POST -H "Content-Type: application/json" \
     -d '{"url":"https://example.com/student-photo.jpg","include_image":true}' \
     http://localhost:5001/detect_url
```

## Integration with NestJS

Add this method to your `DataMatrixService`:

```typescript
/**
 * Detect datamatrix codes in an image from URL
 */
async detectFromUrl(imageUrl: string, includeImage = false): Promise<any> {
  try {
    const response = await axios.post(
      `${this.apiUrl}/detect_url`,
      { 
        url: imageUrl,
        include_image: includeImage 
      },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      },
    );

    return response.data;
  } catch (error) {
    throw new HttpException(
      error.response?.data?.error || 'Failed to detect datamatrix from URL',
      error.response?.status || 500,
    );
  }
}
```

Add this controller method:

```typescript
@Post('url')
async detectFromUrl(@Body() body: { url: string, includeImage?: boolean }): Promise<any> {
  return this.dataMatrixService.detectFromUrl(
    body.url, 
    body.includeImage || false
  );
}
```

## Error Handling

The endpoint handles various error scenarios:

- **Invalid URL format**: Returns 400 with error message
- **URL doesn't point to an image**: Returns 400 with content-type information
- **Network errors**: Returns 400 with connection error details
- **Image processing errors**: Returns 500 with processing error details

## Features

- **Automatic image download**: Downloads images from any accessible URL
- **Content-type validation**: Ensures the URL points to an image
- **Browser-like headers**: Uses proper User-Agent to avoid blocking
- **Timeout handling**: 30-second timeout for downloads
- **Unique filename generation**: Prevents conflicts with multiple requests
- **Same processing pipeline**: Uses the same detection algorithms as file uploads

## Use Cases

1. **Student photo processing**: Process photos already uploaded to your student management system
2. **Batch processing**: Process multiple images by their URLs
3. **External image sources**: Process images from external systems or CDNs
4. **API integration**: Easy integration with existing image storage solutions

## Testing

Use the provided test client:

```bash
node test-url-client.js https://example.com/path/to/image.jpg
```

This will test both basic URL processing and processing with image inclusion.