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

      // Get provider first (with fallback)
      const provider = config.user_config?.provider || process.env.MODEL_PROVIDER || 'openrouter';
      
      // Get API key based on provider - fallback to environment variables
      let apiKey = config.user_config?.api_key;
      if (!apiKey) {
        if (provider === 'cerebras') {
          apiKey = process.env.CEREBRAS_API_KEY;
        } else if (provider === 'google' || provider === 'gemini') {
          apiKey = process.env.GOOGLE_API_KEY;
        } else if (provider === 'azure') {
          apiKey = process.env.AZURE_OPENAI_API_KEY;
        } else {
          apiKey = process.env.OPENROUTER_API_KEY || process.env.OPENAI_API_KEY;
        }
      }
      
      const modelName = config.user_config?.model || process.env.OPENROUTER_MODEL || process.env.MODEL_NAME || 'gpt-4o-mini';
      
      // Determine baseURL based on provider
      let baseURL: string | undefined = undefined;
      if (provider === 'openrouter' || apiKey?.startsWith('sk-or-v1-')) {
        baseURL = 'https://openrouter.ai/api/v1';
      } else if (provider === 'cerebras') {
        baseURL = 'https://api.cerebras.ai/v1';
      } else if (provider === 'azure') {
        baseURL = 'https://chatgpt-uat.openai.azure.com/openai/v1';
      } else if (provider === 'google' || provider === 'gemini') {
        // Google Gemini uses SDK, not baseURL
        baseURL = undefined;
      }
      
      logger.info('Initializing new Stagehand session', {
        sessionId,
        testId,
        userId,
        browser: config.browser || 'chromium',
        headless: config.headless === true,  // Default to false (show browser window)
        hasUserConfig: !!config.user_config,
        hasApiKey: !!apiKey,
        provider: provider,
        modelName: modelName,
        baseURL: baseURL,
        usingCustomBaseURL: !!baseURL,
      });

      // Validate API key is available
      if (!apiKey) {
        throw new Error('API key is required for Stagehand. Provide it in user_config or set OPENAI_API_KEY environment variable.');
      }

      // Create Stagehand instance with OpenRouter support
      const stagehandConfig: any = {
        env: 'LOCAL',  // Always use LOCAL mode (uses local Playwright)
        headless: config.headless === true,  // Default to false (show browser window)
        verbose: 1,
        debugDom: true,
        enableCaching: false,
        // User AI configuration with fallbacks
        modelName: modelName,
        apiKey: apiKey,
      };
      
      // Add baseURL for OpenRouter
      if (baseURL) {
        stagehandConfig.baseURL = baseURL;
      }
      
      const stagehand = new Stagehand(stagehandConfig);

      // Initialize Stagehand
      await stagehand.init();

      // Don't navigate to about:blank - act() doesn't work on blank pages
      // Let the first test step handle initial navigation
      logger.info('Stagehand session initialized, ready for navigation', { sessionId });

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

      // Check if this step is a navigation step
      const actionLower = step.action.toLowerCase();
      const isNavigationStep = 
        actionLower.includes('navigate to') ||
        actionLower.includes('go to') ||
        actionLower.startsWith('visit');

      logger.info('Step analysis', { 
        sessionId, 
        stepNumber, 
        actionLower: actionLower.substring(0, 100),
        isNavigationStep 
      });

      // If it's a navigation step, extract URL and use page.goto()
      // (act() doesn't work until a real page is loaded)
      if (isNavigationStep) {
        // Extract URL from step action
        // Patterns: "Navigate to URL: https://..." or "Navigate to https://..." or "Go to https://..."
        const urlMatch = step.action.match(/https?:\/\/[^\s]+/);
        
        logger.info('URL extraction', { sessionId, stepNumber, urlMatch: urlMatch?.[0] });
        
        if (urlMatch) {
          const url = urlMatch[0];
          logger.info('Detected navigation step, using page.goto()', { sessionId, stepNumber, url });
          
          // Try networkidle first (matching working test), fall back to load if it times out
          try {
            await stagehand.page.goto(url, { 
              waitUntil: 'networkidle',
              timeout: 30000  // 30s timeout for networkidle
            });
            logger.info('Page reached networkidle state', { sessionId, stepNumber });
          } catch (timeoutError) {
            // If networkidle times out, the page is already loaded, just log and continue
            logger.warn('Networkidle timeout, page is loaded but still has network activity', { 
              sessionId, 
              stepNumber 
            });
          }
          
          // Wait for page to stabilize and let act handler initialize (matching working test)
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          // Prime the act handler by calling it with a simple action
          // This forces Stagehand to initialize its AI handlers after navigation
          try {
            logger.info('Priming act handler after navigation', { sessionId, stepNumber });
            // Call act() with a no-op action to initialize the handler
            // This ensures the act handler is ready for subsequent steps
            await stagehand.act({ action: 'observe the page' });
            logger.info('Act handler primed successfully', { sessionId, stepNumber });
          } catch (e) {
            logger.warn('Failed to prime act handler, will initialize on first real step', { 
              sessionId, 
              stepNumber, 
              error: e instanceof Error ? e.message : String(e) 
            });
          }
          
          const duration = Date.now() - startTime;
          logger.info('Navigation step completed successfully', {
            sessionId,
            stepNumber,
            url,
            duration_ms: duration,
          });

          return {
            success: true,
            message: `Navigated to ${url}`,
            duration_ms: duration,
          };
        }
      }

      // Execute step using Stagehand's act method (working test calls act directly)
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
      
      // Re-initialize act handler context after navigation
      // This ensures Stagehand's act() method has proper page context
      try {
        await session.stagehand.page.evaluate(() => {
          // Simple page evaluation to ensure context is established
          return document.readyState;
        });
      } catch (e) {
        logger.warn('Failed to re-establish page context', { sessionId, error: String(e) });
      }
      
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
