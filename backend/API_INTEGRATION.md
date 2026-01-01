# Frontend API Integration Guide

This document describes how to integrate the frontend with the Retainly backend API.

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

### 1. Upload File

**POST** `/upload`

Upload a JSON file to start processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field containing the JSON file

**Response:**
```json
{
  "id": "analysis_id",
  "filename": "dataset.json",
  "timestamp": "2026-01-01T16:45:12+05:00",
  "status": "processing",
  "progress": 0.0,
  "data": {
    "summary": {
      "total_entries": 0,
      "processed": 0,
      "errors": 0,
      "exact_match_count": 0,
      "low_rank_count": 0,
      "medium_rank_count": 0,
      "critical_rank_count": 0,
      "error_count": 0
    },
    "exact_match": [],
    "low_rank": [],
    "medium_rank": [],
    "critical_rank": [],
    "errors": []
  }
}
```

### 2. Get Processing Status

**GET** `/upload/status/{analysis_id}`

Get the current processing status of an analysis.

**Response:** Same as upload response, with updated `status` and `progress` fields.

**Status values:**
- `processing`: Analysis is in progress
- `completed`: Analysis is complete
- `failed`: Analysis failed

### 3. Get Analysis

**GET** `/analysis/{analysis_id}`

Get complete analysis results.

**Response:** Full analysis object with all categorized entries.

### 4. Get Category Entries

**GET** `/analysis/{analysis_id}/category/{category}`

Get entries for a specific category.

**Categories:**
- `exact`: Exact match entries
- `low`: Low rank entries
- `medium`: Medium rank entries
- `critical`: Critical rank entries
- `error`: Error entries

**Response:**
```json
{
  "analysis_id": "analysis_id",
  "category": "low",
  "entries": [...],
  "count": 5
}
```

### 5. Get History

**GET** `/history?skip=0&limit=100`

Get all analysis history, sorted by timestamp (newest first).

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100, max: 1000)

**Response:**
```json
{
  "analyses": [...],
  "total": 10
}
```

### 6. Get History Item

**GET** `/history/{analysis_id}`

Get a specific analysis from history.

**Response:** Same as analysis response.

### 7. Delete Analysis

**DELETE** `/analysis/{analysis_id}`

Delete an analysis.

**Response:**
```json
{
  "message": "Analysis deleted successfully",
  "analysis_id": "analysis_id"
}
```

### 8. Get Receipt Image

**GET** `/images/{receipt_number}`

Get a receipt image by receipt number.

**Response:** Image file (JPEG)

## Frontend Integration Example

### TypeScript/React Example

```typescript
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Upload file
async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });
  
  return await response.json();
}

// Poll for status
async function pollStatus(analysisId: string) {
  const response = await fetch(`${API_BASE_URL}/upload/status/${analysisId}`);
  return await response.json();
}

// Get analysis
async function getAnalysis(analysisId: string) {
  const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}`);
  return await response.json();
}

// Get history
async function getHistory(skip = 0, limit = 100) {
  const response = await fetch(`${API_BASE_URL}/history?skip=${skip}&limit=${limit}`);
  return await response.json();
}
```

## Error Handling

All endpoints may return standard HTTP error codes:

- `400`: Bad Request (invalid input)
- `404`: Not Found (resource doesn't exist)
- `500`: Internal Server Error (server error)

Error responses follow this format:
```json
{
  "detail": "Error message"
}
```

## Polling Strategy

For processing status, implement polling:

```typescript
async function waitForCompletion(analysisId: string) {
  while (true) {
    const status = await pollStatus(analysisId);
    
    if (status.status === 'completed') {
      return status;
    }
    
    if (status.status === 'failed') {
      throw new Error('Processing failed');
    }
    
    // Wait 2 seconds before next poll
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}
```
