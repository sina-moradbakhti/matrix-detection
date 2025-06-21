import cv2
import numpy as np
from pyzbar import pyzbar
from pylibdmtx import pylibdmtx
import matplotlib.pyplot as plt
import base64
import io
import os
import json
import time
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure output folder
OUTPUT_FOLDER = 'outputs'
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def detect_datamatrix_pyzbar(image):
    """
    Detect Data Matrix codes using pyzbar library
    """
    # Convert to RGB for pyzbar
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Detect barcodes/datamatrix codes
    codes = pyzbar.decode(image_rgb)
    
    return codes

def detect_datamatrix_pylibdmtx(image):
    """
    Detect Data Matrix codes using pylibdmtx library (more specialized for Data Matrix)
    """
    # Convert to grayscale for better detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Detect Data Matrix codes
    codes = pylibdmtx.decode(gray)
    
    return codes

def highlight_codes(image, codes, method='pyzbar', color=(0, 255, 0), thickness=3):
    """
    Draw rectangles around detected codes with proper coordinate handling
    """
    result_image = image.copy()
    
    if method == 'pyzbar':
        for i, code in enumerate(codes):
            try:
                # Get the bounding box points
                points = code.polygon
                if len(points) == 4:
                    # Convert to numpy array with proper integer conversion
                    pts = np.array([[int(point.x), int(point.y)] for point in points], dtype=np.int32)
                    
                    # Draw polygon around the detected area
                    cv2.polylines(result_image, [pts], True, color, thickness)
                    
                    # Also draw a bounding rectangle for clarity
                    rect = code.rect
                    x, y, w, h = int(rect.left), int(rect.top), int(rect.width), int(rect.height)
                    cv2.rectangle(result_image, (x, y), (x + w, y + h), color, thickness//2)
                    
                    # Add text label with better positioning
                    text = f"DM{i+1}: {code.data.decode('utf-8')}"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                    
                    # Position text above the code, but check if there's space
                    text_y = max(y - 10, text_size[1] + 5)
                    cv2.putText(result_image, text, (x, text_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                               
                else:
                    # Fallback to rectangle if polygon points are not available
                    rect = code.rect
                    x, y, w, h = int(rect.left), int(rect.top), int(rect.width), int(rect.height)
                    cv2.rectangle(result_image, (x, y), (x + w, y + h), color, thickness)
                    
                    text = f"DM{i+1}: {code.data.decode('utf-8')}"
                    cv2.putText(result_image, text, (x, max(y - 10, 15)), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                               
            except Exception as e:
                print(f"Error highlighting code {i}: {e}")
                continue
    
    elif method == 'pylibdmtx':
        for i, code in enumerate(codes):
            try:
                # Get the bounding box with proper coordinate conversion
                if hasattr(code, 'rect'):
                    left, top, width, height = code.rect
                    x, y, w, h = int(left), int(top), int(width), int(height)
                    
                    # Draw rectangle
                    cv2.rectangle(result_image, (x, y), (x + w, y + h), color, thickness)
                    
                    # Add text label
                    text = f"DM{i+1}: {code.data.decode('utf-8')}"
                    text_y = max(y - 10, 15)
                    cv2.putText(result_image, text, (x, text_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                else:
                    print(f"Warning: Code {i} has no rect attribute")
                    
            except Exception as e:
                print(f"Error highlighting pylibdmtx code {i}: {e}")
                continue
    
    return result_image

def enhance_image_for_detection(image):
    """
    Preprocess image to improve detection accuracy
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
    
    # Convert back to BGR for consistent processing
    enhanced_bgr = cv2.cvtColor(blurred, cv2.COLOR_GRAY2BGR)
    
    return enhanced_bgr

def process_image(image):
    """
    Process image and detect Data Matrix codes
    """
    all_results = []
    detected_codes = []
    
    # Try both methods
    methods = ['pyzbar', 'pylibdmtx']
    colors = [(0, 255, 0), (255, 0, 0)]
    
    for i, method in enumerate(methods):
        if method == 'pyzbar':
            codes = detect_datamatrix_pyzbar(image)
        else:
            codes = detect_datamatrix_pylibdmtx(image)
        
        if codes:
            # Extract code data
            for j, code in enumerate(codes):
                try:
                    data = code.data.decode('utf-8')
                    code_type = code.type if hasattr(code, 'type') else 'DATAMATRIX'
                    
                    # Get position information
                    if method == 'pyzbar':
                        rect = code.rect
                        position = {
                            'x': int(rect.left),
                            'y': int(rect.top),
                            'width': int(rect.width),
                            'height': int(rect.height)
                        }
                        if hasattr(code, 'polygon') and code.polygon:
                            polygon = [(int(p.x), int(p.y)) for p in code.polygon]
                            position['polygon'] = polygon
                    elif method == 'pylibdmtx':
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
                    
                    detected_codes.append({
                        'method': method,
                        'data': data,
                        'type': code_type,
                        'position': position
                    })
                    
                except Exception as e:
                    print(f"Error processing code {j+1}: {e}")
            
            # Highlight the codes
            color = colors[i % len(colors)]
            highlighted_image = highlight_codes(image, codes, method, color)
            all_results.append((method, highlighted_image, codes))
    
    # If no codes found, try with enhanced image
    if not all_results:
        enhanced_image = enhance_image_for_detection(image)
        
        for i, method in enumerate(methods):
            if method == 'pyzbar':
                codes = detect_datamatrix_pyzbar(enhanced_image)
            else:
                codes = detect_datamatrix_pylibdmtx(enhanced_image)
            
            if codes:
                # Extract code data
                for j, code in enumerate(codes):
                    try:
                        data = code.data.decode('utf-8')
                        code_type = code.type if hasattr(code, 'type') else 'DATAMATRIX'
                        
                        # Get position information
                        if method == 'pyzbar':
                            rect = code.rect
                            position = {
                                'x': int(rect.left),
                                'y': int(rect.top),
                                'width': int(rect.width),
                                'height': int(rect.height)
                            }
                            if hasattr(code, 'polygon') and code.polygon:
                                polygon = [(int(p.x), int(p.y)) for p in code.polygon]
                                position['polygon'] = polygon
                        elif method == 'pylibdmtx':
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
                        
                        detected_codes.append({
                            'method': method + '_enhanced',
                            'data': data,
                            'type': code_type,
                            'position': position
                        })
                        
                    except Exception as e:
                        print(f"Error processing code {j+1}: {e}")
                
                color = colors[i % len(colors)]
                highlighted_image = highlight_codes(enhanced_image, codes, method, color)
                all_results.append((f"{method}_enhanced", highlighted_image, codes))
    
    # Prepare result image
    result_image = None
    if all_results:
        # Prefer pyzbar result as it's usually more accurate
        for method, highlighted_image, codes in all_results:
            if 'pyzbar' in method:
                result_image = highlighted_image
                break
        if result_image is None:
            result_image = all_results[0][1]
    else:
        result_image = image
    
    return result_image, detected_codes

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
            '/download/<filename>': 'GET - Download processed image',
            '/health': 'GET - Health check endpoint'
        }
    })

@app.route('/detect', methods=['POST'])
def detect_datamatrix():
    """
    API endpoint to detect Data Matrix codes in an image
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
    
    # Process the image
    result_image, detected_codes = process_image(image)
    
    # Save the result image
    output_filename = f"result_{filename}"
    output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)
    cv2.imwrite(output_filepath, result_image)
    
    # Prepare response
    response = {
        'detected_codes': detected_codes,
        'count': len(detected_codes)
    }
    
    # Check if client wants the image in the response
    include_image = request.args.get('include_image', 'false').lower() == 'true'
    if include_image:
        # Convert image to base64
        _, buffer = cv2.imencode('.jpg', result_image)
        img_str = base64.b64encode(buffer).decode('utf-8')
        response['image'] = f"data:image/jpeg;base64,{img_str}"
    else:
        # Provide URL to download the image
        response['image_url'] = f"/download/{output_filename}"
    
    return jsonify(response)

@app.route('/detect_base64', methods=['POST'])
def detect_datamatrix_base64():
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
        
        # Process the image
        result_image, detected_codes = process_image(image)
        
        # Generate a unique filename
        import uuid
        filename = f"{uuid.uuid4()}.jpg"
        output_filepath = os.path.join(OUTPUT_FOLDER, filename)
        cv2.imwrite(output_filepath, result_image)
        
        # Prepare response
        response = {
            'detected_codes': detected_codes,
            'count': len(detected_codes)
        }
        
        # Check if client wants the image in the response
        include_image = data.get('include_image', False)
        if include_image:
            # Convert image to base64
            _, buffer = cv2.imencode('.jpg', result_image)
            img_str = base64.b64encode(buffer).decode('utf-8')
            response['image'] = f"data:image/jpeg;base64,{img_str}"
        else:
            # Provide URL to download the image
            response['image_url'] = f"/download/{filename}"
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Download processed image
    """
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    # Install required packages if not already installed:
    # pip install flask opencv-python pyzbar pylibdmtx matplotlib numpy
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)