#!/bin/bash

# Make script exit on first error
set -e

# Print commands before executing them
set -x

# Create necessary directories if they don't exist
mkdir -p uploads outputs nginx/conf.d nginx/ssl

# Generate self-signed SSL certificate for development
if [ ! -f nginx/ssl/cert.pem ] || [ ! -f nginx/ssl/key.pem ]; then
    echo "Generating self-signed SSL certificate for development..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Build and start the services
docker-compose up -d --build

# Display service status
docker-compose ps

echo ""
echo "Data Matrix Detection Service is now running!"
echo "API is available at: http://localhost:5001"
echo ""
echo "To test the service, run:"
echo "  python test_client.py <path_to_image>"
echo ""
echo "To stop the services:"
echo "  docker-compose down"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"