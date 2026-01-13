import { Router, Request, Response } from 'express';
import { sessionManager } from '../services/sessionManager';
import logger from '../services/logger';
import type { SessionConfig, TestStep } from '../types';

const router = Router();

/**
 * POST /api/sessions/initialize
 * Initialize a new Stagehand session
 */
router.post('/initialize', async (req: Request, res: Response) => {
  try {
    const {
      session_id,
      test_id,
      user_id,
      config,
    }: {
      session_id: string;
      test_id: number;
      user_id: number;
      config?: SessionConfig;
    } = req.body;

    // Validate required fields
    if (!session_id || !test_id || !user_id) {
      return res.status(400).json({
        error: 'Missing required fields: session_id, test_id, user_id',
      });
    }

    await sessionManager.initializeSession(session_id, test_id, user_id, config);

    res.json({
      success: true,
      message: 'Session initialized successfully',
      session_id,
    });
  } catch (error) {
    logger.error('Session initialization failed', {
      error: error instanceof Error ? error.message : String(error),
    });

    res.status(500).json({
      error: error instanceof Error ? error.message : 'Session initialization failed',
    });
  }
});

/**
 * POST /api/sessions/:sessionId/execute-step
 * Execute a single test step
 */
router.post('/:sessionId/execute-step', async (req: Request, res: Response) => {
  try {
    const { sessionId } = req.params;
    const { step, step_number }: { step: TestStep; step_number: number } = req.body;

    if (!step || !step.action) {
      return res.status(400).json({
        error: 'Missing required field: step.action',
      });
    }

    const result = await sessionManager.executeStep(sessionId, step, step_number || 0);

    res.json(result);
  } catch (error) {
    logger.error('Step execution failed', {
      error: error instanceof Error ? error.message : String(error),
    });

    res.status(500).json({
      error: error instanceof Error ? error.message : 'Step execution failed',
    });
  }
});

/**
 * POST /api/sessions/:sessionId/navigate
 * Navigate to a URL
 */
router.post('/:sessionId/navigate', async (req: Request, res: Response) => {
  try {
    const { sessionId } = req.params;
    const { url }: { url: string } = req.body;

    if (!url) {
      return res.status(400).json({
        error: 'Missing required field: url',
      });
    }

    const result = await sessionManager.navigate(sessionId, url);

    res.json(result);
  } catch (error) {
    logger.error('Navigation failed', {
      error: error instanceof Error ? error.message : String(error),
    });

    res.status(500).json({
      error: error instanceof Error ? error.message : 'Navigation failed',
    });
  }
});

/**
 * POST /api/sessions/:sessionId/screenshot
 * Take a screenshot
 */
router.post('/:sessionId/screenshot', async (req: Request, res: Response) => {
  try {
    const { sessionId } = req.params;
    const { path }: { path?: string } = req.body;

    const screenshot = await sessionManager.takeScreenshot(sessionId, path);

    res.json({
      success: true,
      screenshot,
    });
  } catch (error) {
    logger.error('Screenshot failed', {
      error: error instanceof Error ? error.message : String(error),
    });

    res.status(500).json({
      error: error instanceof Error ? error.message : 'Screenshot failed',
    });
  }
});

/**
 * GET /api/sessions/:sessionId
 * Get session info
 */
router.get('/:sessionId', (req: Request, res: Response) => {
  try {
    const { sessionId } = req.params;
    const info = sessionManager.getSessionInfo(sessionId);

    if (!info) {
      return res.status(404).json({
        error: 'Session not found',
      });
    }

    res.json(info);
  } catch (error) {
    logger.error('Failed to get session info', {
      error: error instanceof Error ? error.message : String(error),
    });

    res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to get session info',
    });
  }
});

/**
 * GET /api/sessions
 * Get all active sessions
 */
router.get('/', (req: Request, res: Response) => {
  try {
    const sessions = sessionManager.getAllSessions();

    res.json({
      sessions,
      count: sessions.length,
    });
  } catch (error) {
    logger.error('Failed to get sessions', {
      error: error instanceof Error ? error.message : String(error),
    });

    res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to get sessions',
    });
  }
});

/**
 * DELETE /api/sessions/:sessionId
 * Close a session
 */
router.delete('/:sessionId', async (req: Request, res: Response) => {
  try {
    const { sessionId } = req.params;

    await sessionManager.closeSession(sessionId);

    res.json({
      success: true,
      message: 'Session closed successfully',
    });
  } catch (error) {
    logger.error('Failed to close session', {
      error: error instanceof Error ? error.message : String(error),
    });

    res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to close session',
    });
  }
});

export default router;
