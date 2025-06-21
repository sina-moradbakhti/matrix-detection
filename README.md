# 2D Datamatrix Detection Service

This is a standalone service for detecting 2D datamatrix codes in images. It provides a REST API that can be used by any client application, including NestJS applications.

## Features

- Detect Data Matrix codes in images
- Support for both file upload and base64 encoded images
- Returns code data, position, and type
- Optional highlighted image showing detected codes

## Quick Start

### Running with Docker

1. Clone this repository
2. Run the setup script:

```bash
chmod +x docker-setup.sh
./docker-setup.sh
```

This will:
- Create necessary directories
- Generate self-signed SSL certificates for development
- Build and start the Docker container
- Expose the API on port 5001

### API Endpoints

The service exposes the following endpoints:

- `GET /health` - Health check endpoint
- `POST /detect` - Detect Data Matrix in uploaded image file
- `POST /detect_base64` - Detect Data Matrix in base64 encoded image
- `GET /download/<filename>` - Download processed image

## Using from a NestJS Application

### Method 1: HTTP Client (Recommended)

You can use the built-in HTTP client in NestJS to call this service:

```typescript
// In your NestJS service
import { Injectable, HttpService } from '@nestjs/common';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import * as FormData from 'form-data';
import * as fs from 'fs';

@Injectable()
export class DataMatrixService {
  constructor(private httpService: HttpService) {}

  // Method 1: Send file directly
  detectDataMatrixFromFile(filePath: string): Observable<any> {
    const formData = new FormData();
    formData.append('image', fs.createReadStream(filePath));

    return this.httpService
      .post('http://localhost:5001/detect', formData, {
        headers: {
          ...formData.getHeaders(),
        },
      })
      .pipe(map(response => response.data));
  }

  // Method 2: Send base64 encoded image
  detectDataMatrixFromBase64(base64Image: string): Observable<any> {
    return this.httpService
      .post(
        'http://localhost:5001/detect_base64',
        { image: base64Image, include_image: true },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        },
      )
      .pipe(map(response => response.data));
  }
}
```

### Method 2: Using Axios Directly

If you prefer using Axios directly:

```typescript
import { Injectable } from '@nestjs/common';
import axios from 'axios';
import * as FormData from 'form-data';
import * as fs from 'fs';

@Injectable()
export class DataMatrixService {
  private readonly apiUrl = 'http://localhost:5001';

  async detectDataMatrixFromFile(filePath: string): Promise<any> {
    const formData = new FormData();
    formData.append('image', fs.createReadStream(filePath));

    const response = await axios.post(`${this.apiUrl}/detect`, formData, {
      headers: {
        ...formData.getHeaders(),
      },
    });

    return response.data;
  }

  async detectDataMatrixFromBase64(base64Image: string): Promise<any> {
    const response = await axios.post(
      `${this.apiUrl}/detect_base64`,
      { image: base64Image, include_image: true },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      },
    );

    return response.data;
  }
}
```

### Example Usage in a NestJS Controller

```typescript
import { Controller, Post, UploadedFile, UseInterceptors, Body } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { DataMatrixService } from './datamatrix.service';

@Controller('datamatrix')
export class DataMatrixController {
  constructor(private readonly dataMatrixService: DataMatrixService) {}

  @Post('upload')
  @UseInterceptors(FileInterceptor('image'))
  async detectFromUpload(@UploadedFile() file): Promise<any> {
    // Save the uploaded file temporarily
    const filePath = `/tmp/${file.originalname}`;
    require('fs').writeFileSync(filePath, file.buffer);
    
    // Process the file
    const result = await this.dataMatrixService.detectDataMatrixFromFile(filePath);
    
    // Clean up
    require('fs').unlinkSync(filePath);
    
    return result;
  }

  @Post('base64')
  async detectFromBase64(@Body() body: { image: string }): Promise<any> {
    return this.dataMatrixService.detectDataMatrixFromBase64(body.image);
  }
}
```

## Response Format

The API returns a JSON response with the following structure:

```json
{
  "detected_codes": [
    {
      "method": "pyzbar",
      "data": "Example Data",
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
  "image_url": "/download/result_image.jpg"
}
```

If `include_image` is set to `true` in the request, the response will also include a `image` field with the base64-encoded processed image.

## Deployment Considerations

For production use:
1. Configure proper SSL certificates
2. Set up authentication if needed
3. Consider using a reverse proxy like Nginx
4. Adjust Docker settings for your environment

## Troubleshooting

If you encounter issues:
1. Check the Docker logs: `docker-compose logs -f`
2. Ensure the service is running: `docker-compose ps`
3. Test with the included test client: `python test_client.py <path_to_image>`