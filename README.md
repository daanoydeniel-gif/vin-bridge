# Vin Bridge

A lightweight starter app that connects a VIN lookup flow to ChatGPT for summarization and explanation.

This repo is designed to:
- validate VIN input
- decode the VIN through the NHTSA API
- optionally summarize vehicle details with OpenAI
- expose a simple API and web UI for local development

## Features

- VIN validation using standard 17-character format rules
- NHTSA VIN decode integration
- OpenAI-powered summary of the decoded vehicle data
- Health endpoint and simple browser UI
- Easy local setup with environment variables

## Tech Stack

- Node.js
- Express
- OpenAI SDK
- NHTSA VIN API

## Prerequisites

- Node.js 18+
- An OpenAI API key (optional but recommended for summaries)

## Local Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Copy the environment file:
   ```bash
   cp .env.example .env
   ```
4. Add your OpenAI API key to `.env`
5. Start the app:
   ```bash
   npm run dev
   ```

## Environment Variables

Create a `.env` file based on `.env.example`:

```bash
PORT=3000
OPENAI_API_KEY=your_openai_api_key_here
```

## API Endpoints

### GET /health
Returns service health status.

### POST /api/vin/lookup
Example request:

```bash
curl -X POST http://localhost:3000/api/vin/lookup \
  -H "Content-Type: application/json" \
  -d '{"vin":"1HGBH41JXMN109186"}'
```

Example response:

```json
{
  "vin": "1HGBH41JXMN109186",
  "valid": true,
  "nhtsa": {
    "count": 1,
    "message": "Results returned successfully",
    "results": []
  },
  "ai": {
    "enabled": true,
    "summary": "This is a vehicle with a 4-door body style..."
  }
}
```

## Browser UI

Open the app in a browser at:

```bash
http://localhost:3000/
```

## Notes

- The app works without an OpenAI key, but summary generation will be disabled.
- The NHTSA API is used for decoding public VIN data.
- You can extend this app by adding database storage, authentication, or integrations with vehicle marketplace APIs.

## Next Ideas

- add user authentication
- save VIN lookups to a database
- add a dashboard for recent VIN results
- integrate with a vehicle data provider
- expose a webhook or admin API
