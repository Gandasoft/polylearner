#!/bin/bash

# Wait for Ollama to be ready
echo "Waiting for Ollama service to be ready..."
until docker exec polylearner-ollama ollama list > /dev/null 2>&1; do
    sleep 2
done

echo "Ollama is ready! Pulling model llama3.2:3b..."
docker exec polylearner-ollama ollama pull llama3.2:3b

echo "Model pulled successfully!"
echo "Available models:"
docker exec polylearner-ollama ollama list
