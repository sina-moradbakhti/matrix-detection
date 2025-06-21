import cv2
import numpy as np
from pyzbar import pyzbar
from pylibdmtx import pylibdmtx
import base64
import os
import time
import requests
import uuid
from urllib.parse import urlparse
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def detect_datamatrix(image):
    """
    Detect Data Matrix codes using both pyzbar and pylibdmtx libraries
    """
    results = []
    
    # Try pyzbar first
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pyzbar_codes = pyzbar.decode(image_rgb)
    
    # Then try pylibdmtx
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    pylibdmtx_codes = pylibdmtx.decode(gray)
    
    # Process pyzbar results
    for code in pyzbar_codes:
        try:
            data = code.data.decode('utf-8')
            code_type = code.type
            
            # Get position information
            rect = code.rect
            position = {
                'x': int(rect.left),
                'y': int(rect.top),
                'width': int(rect.width),
                'height': int(rect.height)
            }
            
            # Add polygon points if available
            if hasattr(code, 'polygon') and code.polygon:
                polygon = [(int(p.x), int(p.y)) for p in code.polygon]
                position['polygon'] = polygon
                
            results.append({
                'method': 'pyzbar',
                'data': data,
                'type': code_type,
                'position': position
            })
        except Exception as e:
            print(f"Error processing pyzbar code: {e}")
    
    # Process pylibdmtx results
    for code in pylibdmtx_codes:
        try:
            data = code.data.decode('utf-8')
            
            # Get position information if available
            if hasattr(code, 'rect'):
                left, top, width, height = code.rect
                position = {
                    'x': int(left),
                    'y': int(top),
                    'width': int(width),
                    'height': int(height)
                }
            else:
                position = None
                
            results.append({
                'method': 'pylibdmtx',
                'data': data,
                'type': 'DATAMATRIX',
                'position': position
            })
        except Exception as e:
            print(f"Error processing pylibdmtx code: {e}")
    
    return results

def highlight_codes(image, detected_codes):
    """
    Draw rectangles around detected codes
    """
    result_image = image.copy()
    
    for i, code in enumerate(detected_codes):
        try:
            position = code.get('position')
            if not position:
                continue
                
            # Draw rectangle
            x = position.get('x', 0)
            y = position.get('y', 0)
            w = position.get('width', 0)
            h = position.get('height', 0)
            
            # Use different colors for different methods
            color = (0, 255, 0) if code.get('method') == 'pyzbar' else (255, 0, 0)
            cv2.rectangle(result_image, (x, y), (x + w, y + h), color, 2)
            
            # Add text label
            text = f"{i+1}: {code.get('data', '')}"
            cv2.putText(result_image, text, (x, max(y - 10, 15)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Draw polygon if available
            if 'polygon' in position:
                pts = np.array(position['polygon'], dtype=np.int32)
                cv2.polylines(result_image, [pts], True, color, 1)
                
        except Exception as e:
            print(f"Error highlighting code {i}: {e}")
    
    return result_image

def download_image_from_url(url, timeout=30):
    """
    Download image from URL and return as OpenCV image
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")
        
        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Download the image
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Check if the response contains image data
        content_type = response.headers.get('content-type', '').lower()
        if not content_type.startswith('image/'):
            raise ValueError(f"URL does not point to an image. Content-Type: {content_type}")
        
        # Convert to numpy array and decode as image
        image_array = np.frombuffer(response.content, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Could not decode image from URL")
        
        return image
    
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to download image from URL: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error processing image from URL: {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Docker
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'datamatrix-detection-service',
        'version': '1.0.0'
    })

@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint with API information
    """
    return jsonify({
        'service': 'Data Matrix Detection API',
        'version': '1.0.0',
        'endpoints': {
            '/detect': 'POST - Detect Data Matrix in uploaded image',
            '/detect_base64': 'POST - Detect Data Matrix in base64 encoded image',
            '/detect_url': 'POST - Detect Data Matrix in image from URL',
            '/download/<filename>': 'GET - Download processed image',
            '/health': 'GET - Health check endpoint'
        }
    })

@app.route('/detect', methods=['POST'])
def detect_datamatrix_endpoint():
    """
    API endpoint to detect Data Matrix codes in an uploaded image file
    """
    # Check if image file is provided
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    # Save the uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Read the image
    image = cv2.imread(filepath)
    if image is None:
        return jsonify({'error': 'Could not read image file'}), 400
    
    # Detect datamatrix codes
    detected_codes = detect_datamatrix(image)
    
    # Highlight the detected codes
    result_image = highlight_codes(image, detected_codes)
    
    # Save the result image
    output_filename = f"result_{filename}"
    output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)
    cv2.imwrite(output_filepath, result_image)
    
    # Prepare response
    response = {
        'detected_codes': detected_codes,
        'count': len(detected_codes),
        'image_url': f"/download/{output_filename}"
    }
    
    # Include image in response if requested
    include_image = request.args.get('include_image', 'false').lower() == 'true'
    if include_image:
        # Convert image to base64
        _, buffer = cv2.imencode('.jpg', result_image)
        img_str = base64.b64encode(buffer).decode('utf-8')
        response['image'] = f"data:image/jpeg;base64,{img_str}"
    
    return jsonify(response)

@app.route('/detect_base64', methods=['POST'])
def detect_datamatrix_base64_endpoint():
    """
    API endpoint to detect Data Matrix codes in a base64 encoded image
    """
    # Get JSON data
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'No image data provided'}), 400
    
    try:
        # Decode base64 image
        image_data = data['image']
        if image_data.startswith('data:image'):
            # Remove data URL prefix if present
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'error': 'Could not decode image data'}), 400
        
        # Detect datamatrix codes
        detected_codes = detect_datamatrix(image)
        
        # Highlight the detected codes
        result_image = highlight_codes(image, detected_codes)
        
        # Generate a unique filename
        import uuid
        filename = f"{uuid.uuid4()}.jpg"
        output_filepath = os.path.join(OUTPUT_FOLDER, filename)
        cv2.imwrite(output_filepath, result_image)
        
        # Prepare response
        response = {
            'detected_codes': detected_codes,
            'count': len(detected_codes),
            'image_url': f"/download/{filename}"
        }
        
        # Include image in response if requested
        include_image = data.get('include_image', False)
        if include_image:
            # Convert image to base64
            _, buffer = cv2.imencode('.jpg', result_image)
            img_str = base64.b64encode(buffer).decode('utf-8')
            response['image'] = f"data:image/jpeg;base64,{img_str}"
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

@app.route('/detect_url', methods=['POST'])
def detect_datamatrix_url_endpoint():
    """
    API endpoint to detect Data Matrix codes in an image from URL
    """
    # Get JSON data
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'No image URL provided'}), 400
    
    image_url = data['url']
    if not image_url.strip():
        return jsonify({'error': 'Empty image URL provided'}), 400
    
    try:
        # Download image from URL
        image = download_image_from_url(image_url)
        
        # Detect datamatrix codes
        detected_codes = detect_datamatrix(image)
        
        # Highlight the detected codes
        result_image = highlight_codes(image, detected_codes)
        
        # Generate a unique filename based on URL
        parsed_url = urlparse(image_url)
        original_filename = os.path.basename(parsed_url.path) or 'image'
        if not original_filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
            original_filename += '.jpg'
        
        # Create unique filename to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        output_filename = f"result_{unique_id}_{original_filename}"
        output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)
        cv2.imwrite(output_filepath, result_image)
        
        # Prepare response
        response = {
            'detected_codes': detected_codes,
            'count': len(detected_codes),
            'image_url': f"/download/{output_filename}",
            'source_url': image_url
        }
        
        # Include image in response if requested
        include_image = data.get('include_image', False)
        if include_image:
            # Convert image to base64
            _, buffer = cv2.imencode('.jpg', result_image)
            img_str = base64.b64encode(buffer).decode('utf-8')
            response['image'] = f"data:image/jpeg;base64,{img_str}"
        
        return jsonify(response)
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error processing image from URL: {str(e)}'}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Download processed image
    """
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)