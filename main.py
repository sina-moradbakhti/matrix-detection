import cv2
import numpy as np
from pyzbar import pyzbar
from pylibdmtx import pylibdmtx
import matplotlib.pyplot as plt

def detect_datamatrix_pyzbar(image_path):
    """
    Detect Data Matrix codes using pyzbar library
    """
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return None, []
    
    # Convert to RGB for pyzbar
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Detect barcodes/datamatrix codes
    codes = pyzbar.decode(image_rgb)
    
    return image, codes

def detect_datamatrix_pylibdmtx(image_path):
    """
    Detect Data Matrix codes using pylibdmtx library (more specialized for Data Matrix)
    """
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return None, []
    
    # Convert to grayscale for better detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Detect Data Matrix codes
    codes = pylibdmtx.decode(gray)
    
    return image, codes

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

def detect_and_highlight_datamatrix(image_path, output_path=None, colors=[(0, 255, 0), (255, 0, 0)]):
    """
    Main function to detect and highlight Data Matrix codes with improved positioning
    """
    print(f"Processing image: {image_path}")
    
    # Try both methods
    methods = ['pyzbar', 'pylibdmtx']
    all_results = []
    
    for i, method in enumerate(methods):
        print(f"\nTrying method: {method}")
        
        if method == 'pyzbar':
            image, codes = detect_datamatrix_pyzbar(image_path)
        else:
            image, codes = detect_datamatrix_pylibdmtx(image_path)
        
        if image is None:
            continue
            
        print(f"Found {len(codes)} codes with {method}")
        
        if codes:
            # Print detailed coordinate information for debugging
            for j, code in enumerate(codes):
                try:
                    data = code.data.decode('utf-8')
                    print(f"  Code {j+1}: {data}")
                    
                    if method == 'pyzbar':
                        rect = code.rect
                        print(f"    Position: x={rect.left}, y={rect.top}, w={rect.width}, h={rect.height}")
                        if hasattr(code, 'polygon') and code.polygon:
                            points = [(p.x, p.y) for p in code.polygon]
                            print(f"    Polygon: {points}")
                    elif method == 'pylibdmtx':
                        if hasattr(code, 'rect'):
                            left, top, width, height = code.rect
                            print(f"    Position: x={left}, y={top}, w={width}, h={height}")
                        
                except Exception as e:
                    print(f"  Code {j+1}: Could not decode data - {e}")
            
            # Highlight the codes
            color = colors[i % len(colors)]
            highlighted_image = highlight_codes(image, codes, method, color)
            all_results.append((method, highlighted_image, codes))
    
    # If no codes found, try with enhanced image
    if not all_results:
        print("\nNo codes found. Trying with image enhancement...")
        
        image, _ = detect_datamatrix_pyzbar(image_path)
        if image is not None:
            enhanced_image = enhance_image_for_detection(image)
            
            # Save enhanced image temporarily and try detection again
            temp_path = "temp_enhanced.jpg"
            cv2.imwrite(temp_path, enhanced_image)
            
            for i, method in enumerate(methods):
                if method == 'pyzbar':
                    _, codes = detect_datamatrix_pyzbar(temp_path)
                else:
                    _, codes = detect_datamatrix_pylibdmtx(temp_path)
                
                if codes:
                    print(f"Found {len(codes)} codes with {method} (enhanced)")
                    color = colors[i % len(colors)]
                    highlighted_image = highlight_codes(enhanced_image, codes, method, color)
                    all_results.append((f"{method}_enhanced", highlighted_image, codes))
            
            # Clean up temporary file
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    # Display results
    if all_results:
        plt.figure(figsize=(15, 10))
        
        for i, (method, highlighted_image, codes) in enumerate(all_results):
            plt.subplot(1, len(all_results), i+1)
            plt.imshow(cv2.cvtColor(highlighted_image, cv2.COLOR_BGR2RGB))
            plt.title(f"{method} - {len(codes)} codes found")
            plt.axis('off')
        
        plt.tight_layout()
        plt.show()
        
        # Save the result (prefer pyzbar result as it's usually more accurate)
        if output_path:
            best_result = None
            for method, highlighted_image, codes in all_results:
                if 'pyzbar' in method:
                    best_result = highlighted_image
                    break
            if best_result is None:
                best_result = all_results[0][1]
            
            cv2.imwrite(output_path, best_result)
            print(f"Result saved to: {output_path}")
    
    else:
        print("No Data Matrix codes detected in the image.")
        
        # Still show the original image
        image, _ = detect_datamatrix_pyzbar(image_path)
        if image is not None:
            plt.figure(figsize=(10, 8))
            plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            plt.title("Original Image - No codes detected")
            plt.axis('off')
            plt.show()
    
    return all_results

# Example usage
if __name__ == "__main__":
    # Replace with your image path
    image_path = "20250523-0820-17269.jpg"  # Change this to your image path
    output_path = "highlighted_datamatrix.jpg"
    
    # Install required packages if not already installed:
    # pip install opencv-python pyzbar pylibdmtx matplotlib numpy
    
    detect_and_highlight_datamatrix(image_path, output_path)