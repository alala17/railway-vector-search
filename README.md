# Vector Search Service - Railway Deployment

A clean, simplified deployment of the vector search service for Railway.

## Files
- `app.py` - Main Flask application
- `query_pinecone.py` - DINOv2 and Pinecone integration
- `config.py` - Configuration settings
- `requirements.txt` - Python dependencies
- `Dockerfile` - Docker configuration
- `Procfile` - Alternative deployment method

## Environment Variables
Set these in Railway:
- `PINECONE_API_KEY` - Your Pinecone API key
- `PINECONE_ENVIRONMENT` - Pinecone environment (gcp-starter)
- `PINECONE_INDEX_NAME` - Index name (paris-18)

## Deployment
1. Connect this repository to Railway
2. Set environment variables
3. Deploy!
