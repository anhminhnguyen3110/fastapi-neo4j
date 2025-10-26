# API Manual for Generating Embed URLs

This document provides instructions on how to use the `/api/embed` endpoint to generate embed URLs for visualizing data.

## API Documentation

- **Swagger UI**: `http://<your-server-url>/docs`
- **ReDoc**: `http://<your-server-url>/redoc`  
- **OpenAPI Schema**: `http://<your-server-url>/openapi.json`

## API Overview

This FastAPI application provides endpoints for generating embed URLs and querying Neo4j data. The embed URLs point to `/view/{token}` which serves an HTML page that visualizes Neo4j data based on the Cypher query associated with the token.

## Endpoints

### 1. POST `/api/embed` - Generate Embed URL

### 2. POST `/api/proxy/query` - Execute Neo4j Query

### 3. GET `/view/{token}` - View Embed Page

### 4. GET `/api/embed/{token}` - Get Embed Data

## Endpoint: POST `/api/embed`

### Request

- **URL**: `http://<your-server-url>/api/embed`

- **Method**: POST

- **Content-Type**: `application/json`

### Request Body

```json
{
  "cypherQuery": "MATCH (n) RETURN n",
  "expiresInDays": 1
}
```

- **cypherQuery** (string, required): The Cypher query to execute in Neo4j.

- **expiresInDays** (integer, optional): The number of days the embed token will remain valid. Default is 1 day.

### Response

- **Status Code**: `200 OK`

- **Content-Type**: `application/json`

#### Success Response

```json
{
  "success": true,
  "data": {
    "embedUrl": "http://<your-server-url>/view/<token>",
    "embedToken": "<token>",
    "expiresAt": "2025-10-27T00:00:00Z",
    "expiresIn": 86400
  }
}
```

- **embedUrl**: The URL to use for embedding the visualization.

- **embedToken**: The token associated with the embed URL.

- **expiresAt**: The expiration date and time of the token (ISO 8601 format).

- **expiresIn**: The time-to-live of the token in seconds.

#### Error Response

```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "Invalid request body."
  }
}
```

- **code**: The HTTP status code.

- **message**: A description of the error.

### Example Usage

#### cURL Command

```bash
curl -X POST \
  http://<your-server-url>/api/embed \
  -H "Content-Type: application/json" \
  -d '{
    "cypherQuery": "MATCH (n) RETURN n",
    "expiresInDays": 1
  }'
```

#### Python Example

```python
import requests

url = "http://<your-server-url>/api/embed"
headers = {"Content-Type": "application/json"}
data = {
    "cypherQuery": "MATCH (n) RETURN n",
    "expiresInDays": 1
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

Replace `<your-server-url>` with the actual server URL where the FastAPI application is running.

## Endpoint: GET `/view/{token}` - View Embed Page

This endpoint serves the embed visualization HTML page for a given token.

### Request

- **URL**: `http://<your-server-url>/view/{token}`

- **Method**: GET

- **Path Parameters**:
  - `token` (string, required): The embed token

### Response

Returns an HTML page that displays the Neo4j visualization based on the Cypher query associated with the token.

## Endpoint: GET `/api/embed/{token}` - Get Embed Data

This endpoint returns the embed data (including the Cypher query) for a given token.

### Request

- **URL**: `http://<your-server-url>/api/embed/{token}`

- **Method**: GET

- **Path Parameters**:
  - `token` (string, required): The embed token

### Response

```json
{
  "success": true,
  "data": {
    "cypherQuery": "MATCH (n) RETURN n",
    "token": "abc123def456",
    "expiresAt": "2025-10-27T00:00:00Z"
  }
}
```

## How It Works

1. Call `POST /api/embed` with a Cypher query to get an embed URL
2. The embed URL points to `/view/{token}` which serves an HTML page
3. The HTML page calls `/api/embed/{token}` to get the Cypher query
4. The HTML page then calls `/api/proxy/query` to execute the query and display results
