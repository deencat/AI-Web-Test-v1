import { Router, Request, Response } from 'express';
import { sessionManager } from '../services/sessionManager';
import logger from '../services/logger';
import type { TestStep } from '../types';

const router = Router();

/**
 * POST /api/execute-test
 * Execute a complete test case with multiple steps
 */
router.post('/execute-test', async (req: Request, res: Response) => {
  try {
    const {
      session_id,
      test_case_id,
      execution_id,
      base_url,
      steps,
      environment,
      skip_navigation,
    }: {
      session_id: string;
      test_case_id: number;
      execution_id: number;
      base_url?: string;
      steps: TestStep[];
      environment?: string;
      skip_navigation?: boolean;
    } = req.body;

    // Validate required fields
    if (!session_id || !test_case_id || !execution_id || !steps) {
      return res.status(400).json({
        error: 'Missing required fields: session_id, test_case_id, execution_id, steps',
      });
    }

    logger.info('Starting test execution', {
      session_id,
      test_case_id,
      execution_id,
      num_steps: steps.length,
    });

    // Debug: Log first step to see its structure
    if (steps.length > 0) {
      logger.info('First step structure', { 
        step: steps[0],
        stepType: typeof steps[0],
        hasAction: !!steps[0].action,
        actionValue: steps[0].action
      });
    }

    // Check if first step is navigation - if so, skip base_url navigation
    const firstStepIsNav = steps.length > 0 && 
      steps[0].action && 
      (steps[0].action.toLowerCase().includes('navigate to') ||
       steps[0].action.toLowerCase().includes('go to') ||
       steps[0].action.toLowerCase().startsWith('visit'));
    
    logger.info('Navigation check', { 
      firstStepIsNav, 
      base_url, 
      skip_navigation,
      willNavigateToBase: base_url && !skip_navigation && !firstStepIsNav
    });
    
    // Navigate to base URL only if:
    // 1. base_url is provided
    // 2. skip_navigation is not true
    // 3. first step is NOT a navigation step
    if (base_url && !skip_navigation && !firstStepIsNav) {
      logger.info('Navigating to base URL', { base_url });
      await sessionManager.navigate(session_id, base_url);
    } else if (firstStepIsNav) {
      logger.info('Skipping base URL navigation - first step handles navigation');
    }

    // Execute each step sequentially
    const stepResults = [];
    let allStepsPassed = true;

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      const step_number = i + 1;

      logger.info('Executing step', { step_number, action: step.action });

      try {
        const result = await sessionManager.executeStep(session_id, step, step_number);
        stepResults.push({
          step_number,
          success: result.success,
          message: result.message || '',
          screenshot: result.screenshot,
        });

        if (!result.success) {
          allStepsPassed = false;
          logger.warn('Step failed', { step_number, error: result.error });
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logger.error('Step execution error', { step_number, error: errorMessage });
        
        stepResults.push({
          step_number,
          success: false,
          error: errorMessage,
        });
        
        allStepsPassed = false;
      }
    }

    // Return execution results
    const response: {
      success: boolean;
      test_case_id: number;
      execution_id: number;
      environment: string;
      steps_executed: number;
      steps_passed: number;
      steps_failed: number;
      step_results: any[];
      error_message?: string;
    } = {
      success: allStepsPassed,
      test_case_id,
      execution_id,
      environment: environment || 'default',
      steps_executed: stepResults.length,
      steps_passed: stepResults.filter(s => s.success).length,
      steps_failed: stepResults.filter(s => !s.success).length,
      step_results: stepResults,
    };

    if (!allStepsPassed) {
      const failedSteps = stepResults.filter(s => !s.success);
      response.error_message = `${failedSteps.length} step(s) failed`;
    }

    logger.info('Test execution completed', {
      success: allStepsPassed,
      steps_passed: response.steps_passed,
      steps_failed: response.steps_failed,
    });

    res.json(response);

  } catch (error) {
    logger.error('Test execution failed', {
      error: error instanceof Error ? error.message : String(error),
    });

    res.status(500).json({
      error: error instanceof Error ? error.message : 'Test execution failed',
      success: false,
    });
  }
});

export default router;
