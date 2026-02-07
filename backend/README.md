# Retainly Backend API

FastAPI backend for processing invoice/receipt images and extracting InvoiceTotal, TotalDiscount using Azure Prebuilt Invoice model.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```env
   MONGODB_URL=mongodb://localhost:27017
   DATABASE_NAME=retainly
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_azure_endpoint
   AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_azure_api_key
   ```

3. **Start MongoDB:**
   Make sure MongoDB is running on `localhost:27017` (or update `MONGODB_URL` in `.env`)

4. **Run the server:**
   ```bash
   python run.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

- `POST /api/v1/upload` - Upload a JSON file to start processing
- `GET /api/v1/upload/status/{analysis_id}` - Get processing status
- `GET /api/v1/analysis/{analysis_id}` - Get analysis results
- `GET /api/v1/analysis/{analysis_id}/category/{category}` - Get category-specific entries
- `DELETE /api/v1/analysis/{analysis_id}` - Delete an analysis
- `GET /api/v1/history` - Get analysis history
- `GET /api/v1/history/{analysis_id}` - Get specific analysis from history
- `GET /api/v1/images/{receipt_number}` - Get receipt image

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── lifespan.py           # Application lifespan (startup/shutdown)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py         # Settings and configuration
│   │   └── database.py       # MongoDB connection
│   ├── models/
│   │   ├── __init__.py
│   │   └── analysis.py       # Pydantic models for MongoDB documents
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── analysis.py       # Pydantic schemas for API requests/responses
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analysis_service.py    # Business logic for analysis CRUD
│   │   └── ai_pipeline_service.py  # AI processing logic
│   └── api/
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           ├── upload.py     # File upload endpoints
│           ├── analysis.py    # Analysis endpoints
│           ├── history.py    # History endpoints
│           └── images.py     # Image serving endpoints
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Features

- **Asynchronous Processing**: File uploads trigger background tasks for AI processing
- **MongoDB Storage**: Analysis results are stored in MongoDB with date-wise history
- **GMT+5 Timestamps**: All timestamps are stored and displayed in GMT+5 timezone
- **Graceful Shutdown**: Background tasks are immediately cancelled on server shutdown
- **CORS Support**: Configured for frontend communication
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Environment Variables

- `MONGODB_URL`: MongoDB connection string (default: `mongodb://localhost:27017`)
- `DATABASE_NAME`: Database name (default: `retainly`)
- `GEMINI_API_KEY`: Google Gemini API key (required)
- `CORS_ORIGINS`: Comma-separated list of allowed origins (default includes localhost ports)
