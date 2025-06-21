import requests
import base64
import json
import sys
import os

def test_file_upload(image_path):
    """Test the /detect endpoint with file upload"""
    print(f"Testing file upload with {image_path}")
    
    url = "http://localhost:5001/detect"
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} does not exist")
        return
    
    # Prepare the file for upload
    files = {'image': open(image_path, 'rb')}
    
    # Make the request
    response = requests.post(url, files=files)
    
    # Print the response
    if response.status_code == 200:
        result = response.json()
        print(f"Success! Found {result['count']} codes")
        print(f"Image URL: {result['image_url']}")
        
        # Print detected codes
        for i, code in enumerate(result['detected_codes']):
            print(f"Code {i+1}:")
            print(f"  Method: {code['method']}")
            print(f"  Data: {code['data']}")
            print(f"  Type: {code['type']}")
            print(f"  Position: {code['position']}")
            print()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_base64_upload(image_path):
    """Test the /detect_base64 endpoint with base64 encoded image"""
    print(f"Testing base64 upload with {image_path}")
    
    url = "http://localhost:5001/detect_base64"
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} does not exist")
        return
    
    # Read the image and encode it as base64
    with open(image_path, 'rb') as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Prepare the JSON payload
    payload = {
        'image': encoded_string,
        'include_image': True  # Include the processed image in the response
    }
    
    # Make the request
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    # Print the response
    if response.status_code == 200:
        result = response.json()
        print(f"Success! Found {result['count']} codes")
        
        # Print detected codes
        for i, code in enumerate(result['detected_codes']):
            print(f"Code {i+1}:")
            print(f"  Method: {code['method']}")
            print(f"  Data: {code['data']}")
            print(f"  Type: {code['type']}")
            print(f"  Position: {code['position']}")
            print()
        
        # Save the returned image if it's included
        if 'image' in result:
            # Extract the base64 part
            img_data = result['image'].split(',')[1]
            img_bytes = base64.b64decode(img_data)
            
            # Save to file
            output_path = "received_image.jpg"
            with open(output_path, 'wb') as f:
                f.write(img_bytes)
            print(f"Saved processed image to {output_path}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # Check if image path is provided
    if len(sys.argv) < 2:
        print("Usage: python test_client.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Test both endpoints
    test_file_upload(image_path)
    print("\n" + "-"*50 + "\n")
    test_base64_upload(image_path)