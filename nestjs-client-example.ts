// NestJS Client Example for 2D Datamatrix Detection Service

// 1. Install required dependencies in your NestJS project:
// npm install --save axios form-data

// 2. Create a service for interacting with the datamatrix detection API:

import { Injectable, HttpException } from '@nestjs/common';
import axios from 'axios';
import * as FormData from 'form-data';
import * as fs from 'fs';

@Injectable()
export class DataMatrixService {
  private readonly apiUrl = 'http://localhost:5001'; // Update with your service URL

  /**
   * Detect datamatrix codes in an image file
   * @param filePath Path to the image file
   * @returns Detection results
   */
  async detectFromFile(filePath: string): Promise<any> {
    try {
      // Create form data with the image file
      const formData = new FormData();
      formData.append('image', fs.createReadStream(filePath));

      // Send request to the detection service
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
   * @param base64Image Base64 encoded image data
   * @param includeImage Whether to include the processed image in the response
   * @returns Detection results
   */
  async detectFromBase64(base64Image: string, includeImage = false): Promise<any> {
    try {
      // Send request to the detection service
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
   * @param filename Filename from the detection response
   * @returns Image buffer
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

// 3. Example controller using the service:

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

// 4. Register in your NestJS module:

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