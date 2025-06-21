# Production Deployment Guide

## Overview
This guide shows how to deploy the datamatrix detection service on your production server alongside your existing backend.

## Prerequisites
- Your existing backend is running on port 3001
- Docker and docker-compose are installed
- Your backend uses the `server-network` Docker network

## Deployment Options

### Option 1: Standalone Service (Recommended)

1. **Upload the service to your server:**
   ```bash
   # From your local machine
   scp -r /path/to/test-2dd root@your-server:/root/datamatrix-service
   ```

2. **On your server, deploy the service:**
   ```bash
   cd /root/datamatrix-service
   
   # Create the shared network if it doesn't exist
   docker network create server-network 2>/dev/null || true
   
   # Build and start the service
   docker-compose up --build -d
   ```

3. **Verify the service is running:**
   ```bash
   docker ps
   curl http://localhost:5001/health
   ```

### Option 2: Integrated with Existing Backend

1. **Copy the datamatrix service to your backend directory:**
   ```bash
   cp -r /root/datamatrix-service /root/mexlefirst-backend/
   ```

2. **Update your existing docker-compose.yml:**
   Add the datamatrix service section from `docker-compose.integrated.yml` to your existing `/root/mexlefirst-backend/docker-compose.yml`

3. **Restart your entire stack:**
   ```bash
   cd /root/mexlefirst-backend
   docker-compose down
   docker-compose up --build -d
   ```

## Integration with Your Backend

### Backend Code Example (Node.js/Express)

```javascript
const axios = require('axios');

// Process student uploaded image for datamatrix detection
app.post('/api/detect-datamatrix', async (req, res) => {
  try {
    const { imageUrl } = req.body; // e.g., "/uploads/processed/image.jpg"
    
    // Call datamatrix service using container name
    const response = await axios.post('http://datamatrix-service:5001/detect_url', {
      url: `http://backend:3001${imageUrl}`,
      include_image: false
    });
    
    res.json({
      success: true,
      detectedCodes: response.data.detected_codes,
      count: response.data.count,
      processedImageUrl: response.data.image_url
    });
    
  } catch (error) {
    console.error('Datamatrix detection error:', error.message);
    res.status(500).json({
      success: false,
      error: 'Failed to detect datamatrix codes'
    });
  }
});

// Alternative: Process with base64 image
app.post('/api/detect-datamatrix-base64', async (req, res) => {
  try {
    const { base64Image } = req.body;
    
    const response = await axios.post('http://datamatrix-service:5001/detect_base64', {
      image: base64Image,
      include_image: false
    });
    
    res.json({
      success: true,
      detectedCodes: response.data.detected_codes,
      count: response.data.count
    });
    
  } catch (error) {
    console.error('Datamatrix detection error:', error.message);
    res.status(500).json({
      success: false,
      error: 'Failed to detect datamatrix codes'
    });
  }
});
```

### Frontend Integration Example

```javascript
// In your frontend (React/Vue/etc.)
const detectDatamatrix = async (imageUrl) => {
  try {
    const response = await fetch('/api/detect-datamatrix', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ imageUrl })
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log(`Found ${result.count} datamatrix codes:`);
      result.detectedCodes.forEach((code, i) => {
        console.log(`Code ${i+1}: ${code.data}`);
      });
    }
    
    return result;
  } catch (error) {
    console.error('Error detecting datamatrix:', error);
  }
};

// Usage
detectDatamatrix('/uploads/processed/student-image.jpg');
```

## Service URLs

- **Health Check:** `http://localhost:5001/health`
- **File Upload Detection:** `http://localhost:5001/detect`
- **Base64 Detection:** `http://localhost:5001/detect_base64`
- **URL Detection:** `http://localhost:5001/detect_url`
- **Download Processed Image:** `http://localhost:5001/download/<filename>`

## Container Communication

When both services are in the same Docker network:

- **From backend to datamatrix service:** `http://datamatrix-service:5001`
- **From datamatrix service to backend:** `http://backend:3001`
- **External access:** `http://your-server-ip:5001`

## Monitoring and Logs

```bash
# Check service status
docker ps

# View logs
docker logs datamatrix-service

# Follow logs in real-time
docker logs -f datamatrix-service

# Check health
curl http://localhost:5001/health
```

## Troubleshooting

### Common Issues:

1. **Network connectivity:**
   ```bash
   # Ensure both containers are in the same network
   docker network ls
   docker network inspect server-network
   ```

2. **Port conflicts:**
   ```bash
   # Check if port 5001 is available
   netstat -tlnp | grep 5001
   ```

3. **Image access issues:**
   ```bash
   # Test image accessibility from container
   docker exec datamatrix-service curl -I http://backend:3001/uploads/processed/test-image.jpg
   ```

## Security Considerations

- The service runs on port 5001 - consider firewall rules
- Images are temporarily stored in `/app/uploads` and `/app/outputs`
- Logs are rotated (max 10MB, 3 files)
- Service restarts automatically unless stopped

## Performance

- Service includes health checks every 30 seconds
- Supports concurrent requests
- Processes images in memory (no permanent storage of input images)
- Output images are saved for download via `/download/<filename>`