import { Stagehand } from '@browserbasehq/stagehand';
import { v4 as uuidv4 } from 'uuid';
import logger from './logger';
import type { SessionConfig, SessionInfo, TestCase, ExecutionResult, TestStep } from '../types';

interface ActiveSession {
  stagehand: Stagehand;
  info: SessionInfo;
  timeout?: NodeJS.Timeout;
}

export class StagehandSessionManager {
  private sessions: Map<string, ActiveSession> = new Map();
  private readonly maxSessions: number;
  private readonly sessionTimeoutMs: number;

  constructor(
    maxSessions: number = 10,
    sessionTimeoutMs: number = 3600000 // 1 hour
  ) {
    this.maxSessions = maxSessions;
    this.sessionTimeoutMs = sessionTimeoutMs;
    logger.info('StagehandSessionManager initialized', {
      maxSessions,
      sessionTimeoutMs,
    });
  }

  /**
   * Initialize a new Stagehand session
   */
  async initializeSession(
    sessionId: string,
    testId: number,
    userId: number,
    config: SessionConfig = {}
  ): Promise<void> {
    try {
      // Check session limit
      if (this.sessions.size >= this.maxSessions) {
        throw new Error(
          `Maximum number of sessions (${this.maxSessions}) reached. Please close an existing session.`
        );
      }

      // Check if session already exists
      if (this.sessions.has(sessionId)) {
        logger.warn('Session already exists, reinitializing', { sessionId });
        await this.closeSession(sessionId);
      }

      logger.info('Initializing new Stagehand session', {
        sessionId,
        testId,
        userId,
        browser: config.browser || 'chromium',
        headless: config.headless !== false,
      });

      // Create Stagehand instance
      const stagehand = new Stagehand({
        env: config.headless !== false ? 'BROWSERBASE' : 'LOCAL',
        verbose: 1,
        debugDom: true,
        enableCaching: false,
        // User AI configuration
        modelName: config.user_config?.model as any, // Type cast to allow dynamic model names
        apiKey: config.user_config?.api_key,
      });

      // Initialize Stagehand
      await stagehand.init();

      // Navigate to blank page to initialize act handler
      // Stagehand requires a page to be loaded before act() can be used
      await stagehand.page.goto('about:blank');
      logger.info('Act handler initialized with blank page', { sessionId });

      // Create session info
      const info: SessionInfo = {
        session_id: sessionId,
        test_id: testId,
        user_id: userId,
        created_at: new Date().toISOString(),
        last_activity: new Date().toISOString(),
        status: 'active',
      };

      // Set up session timeout
      const timeout = setTimeout(() => {
        logger.warn('Session timeout reached', { sessionId });
        this.closeSession(sessionId).catch((err) =>
          logger.error('Error closing timed-out session', { sessionId, error: err })
        );
      }, this.sessionTimeoutMs);

      // Store session
      this.sessions.set(sessionId, { stagehand, info, timeout });

      logger.info('Session initialized successfully', { sessionId });
    } catch (error) {
      logger.error('Failed to initialize session', {
        sessionId,
        error: error instanceof Error ? error.message : String(error),
      });
      throw error;
    }
  }

  /**
   * Execute a single test step
   */
  async executeStep(
    sessionId: string,
    step: TestStep,
    stepNumber: number
  ): Promise<ExecutionResult> {
    const startTime = Date.now();

    try {
      const session = this.getSession(sessionId);
      this.updateSessionActivity(sessionId);

      logger.info('Executing step', { sessionId, stepNumber, action: step.action });

      const { stagehand } = session;

      // Execute step using Stagehand's act method
      await stagehand.act({ action: step.action });

      const duration = Date.now() - startTime;

      logger.info('Step executed successfully', {
        sessionId,
        stepNumber,
        duration_ms: duration,
      });

      return {
        success: true,
        message: `Step ${stepNumber} completed successfully`,
        duration_ms: duration,
      };
    } catch (error) {
      const duration = Date.now() - startTime;
      const errorMessage = error instanceof Error ? error.message : String(error);

      logger.error('Step execution failed', {
        sessionId,
        stepNumber,
        error: errorMessage,
        duration_ms: duration,
      });

      return {
        success: false,
        error: errorMessage,
        duration_ms: duration,
      };
    }
  }

  /**
   * Navigate to a URL
   */
  async navigate(sessionId: string, url: string): Promise<ExecutionResult> {
    try {
      const session = this.getSession(sessionId);
      this.updateSessionActivity(sessionId);

      logger.info('Navigating to URL', { sessionId, url });

      // Use 'domcontentloaded' instead of 'networkidle' to avoid timeout on pages
      // that continuously load resources (ads, analytics, etc.)
      await session.stagehand.page.goto(url, { 
        waitUntil: 'domcontentloaded',
        timeout: 60000 
      });
      
      // Wait for page to stabilize and dynamic content to load
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      logger.info('Navigation completed successfully', { sessionId, url });

      return {
        success: true,
        message: `Navigated to ${url}`,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logger.error('Navigation failed', { sessionId, url, error: errorMessage });

      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Take a screenshot
   */
  async takeScreenshot(sessionId: string, path?: string): Promise<string> {
    try {
      const session = this.getSession(sessionId);
      this.updateSessionActivity(sessionId);

      logger.info('Taking screenshot', { sessionId, path });

      const screenshotBuffer = await session.stagehand.page.screenshot({
        path,
        fullPage: true,
      });

      return screenshotBuffer.toString('base64');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logger.error('Screenshot failed', { sessionId, error: errorMessage });
      throw error;
    }
  }

  /**
   * Close a session
   */
  async closeSession(sessionId: string): Promise<void> {
    try {
      const session = this.sessions.get(sessionId);

      if (!session) {
        logger.warn('Session not found for closing', { sessionId });
        return;
      }

      logger.info('Closing session', { sessionId });

      // Clear timeout
      if (session.timeout) {
        clearTimeout(session.timeout);
      }

      // Close Stagehand
      await session.stagehand.close();

      // Remove from sessions
      this.sessions.delete(sessionId);

      logger.info('Session closed successfully', { sessionId });
    } catch (error) {
      logger.error('Error closing session', {
        sessionId,
        error: error instanceof Error ? error.message : String(error),
      });
      throw error;
    }
  }

  /**
   * Get session info
   */
  getSessionInfo(sessionId: string): SessionInfo | null {
    const session = this.sessions.get(sessionId);
    return session ? session.info : null;
  }

  /**
   * Get all active sessions
   */
  getAllSessions(): SessionInfo[] {
    return Array.from(this.sessions.values()).map((s) => s.info);
  }

  /**
   * Close all sessions
   */
  async closeAllSessions(): Promise<void> {
    logger.info('Closing all sessions', { count: this.sessions.size });

    const closePromises = Array.from(this.sessions.keys()).map((sessionId) =>
      this.closeSession(sessionId)
    );

    await Promise.allSettled(closePromises);

    logger.info('All sessions closed');
  }

  // Private helper methods

  private getSession(sessionId: string): ActiveSession {
    const session = this.sessions.get(sessionId);

    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }

    return session;
  }

  private updateSessionActivity(sessionId: string): void {
    const session = this.sessions.get(sessionId);

    if (session) {
      session.info.last_activity = new Date().toISOString();
      session.info.status = 'active';
    }
  }
}

// Export singleton instance
export const sessionManager = new StagehandSessionManager(
  parseInt(process.env.MAX_SESSIONS || '10'),
  parseInt(process.env.SESSION_TIMEOUT_MS || '3600000')
);
