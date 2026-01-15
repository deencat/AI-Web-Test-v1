import express, { Application, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import logger from './services/logger';
import sessionRoutes from './routes/sessions';
import healthRoutes from './routes/health';
import executionRoutes from './routes/execution';
import { sessionManager } from './services/sessionManager';

// Load environment variables
dotenv.config();

const app: Application = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({
  origin: [
    process.env.CORS_ORIGIN || 'http://localhost:8000',
    'http://localhost:5173', // Frontend dev server
    'http://localhost:3000'  // Alternative frontend port
  ],
  credentials: true,
}));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Request logging middleware
app.use((req: Request, res: Response, next: NextFunction) => {
  logger.info('Incoming request', {
    method: req.method,
    path: req.path,
    ip: req.ip,
  });
  next();
});

// Routes
app.use('/health', healthRoutes);
app.use('/api/sessions', sessionRoutes);
app.use('/api', executionRoutes);

// Root endpoint
app.get('/', (req: Request, res: Response) => {
  res.json({
    service: 'Stagehand TypeScript Microservice',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      health: '/health',
      sessions: '/api/sessions',
      'execute-test': '/api/execute-test',
    },
  });
});

// Error handling middleware
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  logger.error('Unhandled error', {
    error: err.message,
    stack: err.stack,
    path: req.path,
  });

  res.status(500).json({
    error: 'Internal server error',
    message: err.message,
  });
});

// 404 handler
app.use((req: Request, res: Response) => {
  res.status(404).json({
    error: 'Not found',
    path: req.path,
  });
});

// Graceful shutdown
const gracefulShutdown = async () => {
  logger.info('Shutting down gracefully...');

  try {
    await sessionManager.closeAllSessions();
    logger.info('All sessions closed');

    process.exit(0);
  } catch (error) {
    logger.error('Error during shutdown', {
      error: error instanceof Error ? error.message : String(error),
    });
    process.exit(1);
  }
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

// Start server
app.listen(PORT, () => {
  logger.info(`Stagehand TypeScript Microservice started`, {
    port: PORT,
    environment: process.env.NODE_ENV || 'development',
    maxSessions: process.env.MAX_SESSIONS || '10',
  });
});

export default app;
