# Soccer Chat API Server

FastAPI server that acts as a middleware between the frontend and an LLM model for soccer match commentary.

## Features

- Receives chat requests from frontend with match context
- Transforms requests to LLM format with dynamic system prompts
- Streams responses character by character to frontend
- Supports soccer match commentary with team-specific fan perspectives

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### POST /api/v1/chat/stream

Streams chat responses for soccer match commentary.

**Request Body:**
```json
{
  "message": "string",
  "timestamp": 0,
  "context": ["string"],
  "trigger": "string",
  "chat_history": [
    {
      "role": "user",
      "message": "string"
    }
  ],
  "selected_team": "string"
}
```

**Response:** Server-Sent Events (SSE) stream with character-by-character output

## Development

The server runs on `http://localhost:8000` by default.

API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
