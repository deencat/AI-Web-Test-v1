import { Router, Request, Response } from 'express';
import logger from '../services/logger';
import { sessionManager } from '../services/sessionManager';
import type { HealthStatus } from '../types';

const router = Router();
const startTime = Date.now();

/**
 * GET /health
 * Health check endpoint
 */
router.get('/', (req: Request, res: Response) => {
  try {
    const uptime = Math.floor((Date.now() - startTime) / 1000);
    const activeSessions = sessionManager.getAllSessions().length;
    const memoryUsage = Math.round(process.memoryUsage().heapUsed / 1024 / 1024);

    const health: HealthStatus = {
      status: 'healthy',
      uptime_seconds: uptime,
      active_sessions: activeSessions,
      memory_usage_mb: memoryUsage,
      version: '1.0.0',
    };

    // Check if service is degraded
    if (activeSessions >= 8 || memoryUsage > 500) {
      health.status = 'degraded';
    }

    res.json(health);
  } catch (error) {
    logger.error('Health check failed', {
      error: error instanceof Error ? error.message : String(error),
    });

    res.status(500).json({
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Health check failed',
    });
  }
});

/**
 * GET /ping
 * Simple ping endpoint
 */
router.get('/ping', (req: Request, res: Response) => {
  res.json({ message: 'pong' });
});

export default router;
