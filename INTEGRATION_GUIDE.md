# Integrating the 2D Datamatrix Detection Service with NestJS

This guide explains how to use the 2D Datamatrix Detection Service from your NestJS application.

## Overview

The 2D Datamatrix Detection Service is a standalone microservice that provides an API for detecting datamatrix codes in images. You can integrate it with your NestJS application by making HTTP requests to its endpoints.

## Prerequisites

1. The 2D Datamatrix Detection Service is running (either locally or on a server)
2. Your NestJS application has HTTP client capabilities (built-in HttpModule or Axios)

## Integration Steps

### 1. Install Required Dependencies

```bash
npm install --save axios form-data
```

### 2. Create a Service for the Datamatrix API

Create a new service in your NestJS application to handle communication with the Datamatrix Detection Service:

```typescript
// src/datamatrix/datamatrix.service.ts
import { Injectable, HttpException } from '@nestjs/common';
import axios from 'axios';
import * as FormData from 'form-data';
import * as fs from 'fs';

@Injectable()
export class DataMatrixService {
  private readonly apiUrl = 'http://localhost:5001'; // Update with your service URL

  /**
   * Detect datamatrix codes in an image file
   */
  async detectFromFile(filePath: string): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('image', fs.createReadStream(filePath));

      const response = await axios.post(`${this.apiUrl}/detect`, formData, {
        headers: {
          ...formData.getHeaders(),
        },
      });

      return response.data;
    } catch (error) {
      throw new HttpException(
        error.response?.data?.error || 'Failed to detect datamatrix',
        error.response?.status || 500,
      );
    }
  }

  /**
   * Detect datamatrix codes in a base64 encoded image
   */
  async detectFromBase64(base64Image: string, includeImage = false): Promise<any> {
    try {
      const response = await axios.post(
        `${this.apiUrl}/detect_base64`,
        { 
          image: base64Image,
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
        error.response?.data?.error || 'Failed to detect datamatrix',
        error.response?.status || 500,
      );
    }
  }

  /**
   * Download a processed image
   */
  async downloadProcessedImage(filename: string): Promise<Buffer> {
    try {
      const response = await axios.get(`${this.apiUrl}/download/${filename}`, {
        responseType: 'arraybuffer',
      });
      
      return Buffer.from(response.data);
    } catch (error) {
      throw new HttpException(
        'Failed to download processed image',
        error.response?.status || 500,
      );
    }
  }
}
```

### 3. Create a Controller

Create a controller to expose the datamatrix detection functionality in your NestJS application:

```typescript
// src/datamatrix/datamatrix.controller.ts
import { Controller, Post, Get, Param, Body, UploadedFile, UseInterceptors, Res } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { Response } from 'express';
import { DataMatrixService } from './datamatrix.service';

@Controller('datamatrix')
export class DataMatrixController {
  constructor(private readonly dataMatrixService: DataMatrixService) {}

  @Post('upload')
  @UseInterceptors(FileInterceptor('image'))
  async detectFromUpload(@UploadedFile() file): Promise<any> {
    // Save the uploaded file temporarily
    const filePath = `/tmp/${file.originalname}`;
    fs.writeFileSync(filePath, file.buffer);
    
    try {
      // Process the file
      const result = await this.dataMatrixService.detectFromFile(filePath);
      return result;
    } finally {
      // Clean up the temporary file
      fs.unlinkSync(filePath);
    }
  }

  @Post('base64')
  async detectFromBase64(@Body() body: { image: string, includeImage?: boolean }): Promise<any> {
    return this.dataMatrixService.detectFromBase64(
      body.image, 
      body.includeImage || false
    );
  }

  @Get('download/:filename')
  async downloadImage(@Param('filename') filename: string, @Res() res: Response): Promise<void> {
    const imageBuffer = await this.dataMatrixService.downloadProcessedImage(filename);
    
    res.set({
      'Content-Type': 'image/jpeg',
      'Content-Disposition': `attachment; filename=${filename}`,
    });
    
    res.send(imageBuffer);
  }
}
```

### 4. Register in Your Module

```typescript
// src/datamatrix/datamatrix.module.ts
import { Module } from '@nestjs/common';
import { MulterModule } from '@nestjs/platform-express';
import { DataMatrixController } from './datamatrix.controller';
import { DataMatrixService } from './datamatrix.service';

@Module({
  imports: [
    MulterModule.register({
      dest: '/tmp',
    }),
  ],
  controllers: [DataMatrixController],
  providers: [DataMatrixService],
  exports: [DataMatrixService],
})
export class DataMatrixModule {}
```

### 5. Import the Module in Your App Module

```typescript
// src/app.module.ts
import { Module } from '@nestjs/common';
import { DataMatrixModule } from './datamatrix/datamatrix.module';

@Module({
  imports: [
    DataMatrixModule,
    // other modules...
  ],
})
export class AppModule {}
```

## Usage Examples

### Example 1: Uploading an Image File

```typescript
// In a service or controller that uses the DataMatrixService
async processImageFile(filePath: string) {
  const result = await this.dataMatrixService.detectFromFile(filePath);
  
  console.log(`Found ${result.count} datamatrix codes`);
  console.log('Codes:', result.detected_codes);
  
  // If you want to download the processed image
  const imageUrl = result.image_url;
  // You can now use this URL to download the image
}
```

### Example 2: Using Base64 Encoded Image

```typescript
// In a service or controller that uses the DataMatrixService
async processBase64Image(base64Image: string) {
  const result = await this.dataMatrixService.detectFromBase64(base64Image, true);
  
  console.log(`Found ${result.count} datamatrix codes`);
  console.log('Codes:', result.detected_codes);
  
  // If you requested the image to be included (includeImage=true)
  const processedImageBase64 = result.image;
  // You can now use this base64 image data
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

If `include_image` is set to `true` in the request, the response will also include an `image` field with the base64-encoded processed image.

## Troubleshooting

1. **Connection Issues**: Ensure the Datamatrix Detection Service is running and accessible from your NestJS application.
2. **Image Format Problems**: The service supports common image formats (JPEG, PNG). Ensure your images are in a supported format.
3. **Large Images**: Very large images may cause timeouts. Consider resizing images before sending them.
4. **Service Errors**: Check the service logs for more detailed error information.

## Advanced Configuration

You can modify the `apiUrl` in the `DataMatrixService` to point to a different host or port if the service is running elsewhere. For production environments, consider using environment variables:

```typescript
private readonly apiUrl = process.env.DATAMATRIX_API_URL || 'http://localhost:5001';
```