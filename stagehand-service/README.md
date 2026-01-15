# Stagehand TypeScript Microservice

TypeScript-based Stagehand microservice for the AI Web Test Platform, providing browser automation capabilities via HTTP API.

## Features

- ✅ Express REST API for Stagehand operations
- ✅ Session management with automatic timeouts
- ✅ Support for multiple concurrent sessions
- ✅ Health monitoring and status endpoints
- ✅ Comprehensive logging with Winston
- ✅ TypeScript for type safety
- ✅ Graceful shutdown handling

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run Development Server

```bash
npm run dev
```

The service will start on `http://localhost:3001` by default.

### 4. Build for Production

```bash
npm run build
npm start
```

## API Endpoints

### Health Check

```http
GET /health
```

Returns service health status:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "active_sessions": 2,
  "memory_usage_mb": 256,
  "version": "1.0.0"
}
```

### Initialize Session

```http
POST /api/sessions/initialize
Content-Type: application/json

{
  "session_id": "session-123",
  "test_id": 1,
  "user_id": 1,
  "config": {
    "browser": "chromium",
    "headless": true,
    "user_config": {
      "model": "gpt-4",
      "api_key": "your-api-key"
    }
  }
}
```

### Execute Step

```http
POST /api/sessions/:sessionId/execute-step
Content-Type: application/json

{
  "step": {
    "action": "Click the login button"
  },
  "step_number": 1
}
```

### Navigate

```http
POST /api/sessions/:sessionId/navigate
Content-Type: application/json

{
  "url": "https://example.com"
}
```

### Take Screenshot

```http
POST /api/sessions/:sessionId/screenshot
Content-Type: application/json

{
  "path": "./screenshot.png"
}
```

### Get Session Info

```http
GET /api/sessions/:sessionId
```

### Get All Sessions

```http
GET /api/sessions
```

### Close Session

```http
DELETE /api/sessions/:sessionId
```

## Configuration

Environment variables (see `.env.example`):

- `PORT`: Server port (default: 3001)
- `NODE_ENV`: Environment (development/production)
- `CORS_ORIGIN`: Allowed CORS origin (default: http://localhost:8000)
- `SESSION_TIMEOUT_MS`: Session timeout in milliseconds (default: 3600000)
- `MAX_SESSIONS`: Maximum concurrent sessions (default: 10)
- `LOG_LEVEL`: Logging level (default: info)

## Integration with Python Backend

The Python backend's `TypeScriptStagehandAdapter` communicates with this service:

```python
# Backend automatically uses this service when user selects "typescript" provider
adapter = get_stagehand_adapter(db, user_id, ...)  # Returns TypeScriptStagehandAdapter
await adapter.initialize()  # Calls http://localhost:3001/api/sessions/initialize
await adapter.execute_test(...)  # Executes steps via HTTP
```

## Development

```bash
# Watch mode (auto-restart on changes)
npm run dev

# Type checking
npm run build

# Lint
npm run lint
```

## Architecture

```
stagehand-service/
├── src/
│   ├── index.ts              # Express app entry point
│   ├── types/                # TypeScript type definitions
│   ├── services/
│   │   ├── logger.ts         # Winston logger
│   │   └── sessionManager.ts # Stagehand session management
│   └── routes/
│       ├── health.ts         # Health check endpoints
│       └── sessions.ts       # Session API endpoints
├── dist/                     # Compiled JavaScript (generated)
├── logs/                     # Log files
├── package.json
├── tsconfig.json
└── .env
```

## Deployment

### Docker (Recommended)

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY dist ./dist
EXPOSE 3001
CMD ["node", "dist/index.js"]
```

### Process Manager (PM2)

```bash
npm install -g pm2
pm2 start dist/index.js --name stagehand-service
pm2 save
pm2 startup
```

## Monitoring

- Health endpoint: `GET /health`
- Logs: `./logs/combined.log` and `./logs/error.log`
- Metrics: Session count, memory usage, uptime

## Troubleshooting

### Sessions not cleaning up
- Check `SESSION_TIMEOUT_MS` setting
- Verify graceful shutdown is working (SIGTERM handling)

### High memory usage
- Reduce `MAX_SESSIONS`
- Ensure sessions are being closed properly
- Check for browser context leaks

### Connection refused
- Verify service is running: `curl http://localhost:3001/health`
- Check firewall settings
- Ensure PORT is not in use

## License

MIT
