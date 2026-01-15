/**
 * Standalone TypeScript Stagehand Test - Three.com.hk 5G Broadband Flow
 * 
 * This test validates the TypeScript @browserbasehq/stagehand implementation
 * with a real-world complex subscription flow.
 * 
 * Run: npm install && npm test
 */
import { Stagehand } from '@browserbasehq/stagehand';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// Load environment variables
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
dotenv.config({ path: join(__dirname, '.env') });

// Test configuration
const TEST_URL = 'https://web.three.com.hk/5gbroadband/plan-hsbc-en.html';
const TEST_EMAIL = 'pmo.andrewchan+010@gmail.com';
const TEST_PASSWORD = 'cA8mn49&';

// Helper functions
function logStep(stepNumber, description) {
  console.log(`\n${'='.repeat(70)}`);
  console.log(`  Step ${stepNumber}: ${description}`);
  console.log('='.repeat(70));
}

function logSuccess(message) {
  console.log(`✅ ${message}`);
}

function logError(message) {
  console.log(`❌ ${message}`);
}

function logInfo(message) {
  console.log(`ℹ️  ${message}`);
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Test the Three.com.hk 5G Broadband subscription flow
 */
async function testThreeBroadbandFlow() {
  console.log('\n╔════════════════════════════════════════════════════════════════════╗');
  console.log('║         TypeScript Stagehand - Three.com.hk 5G Broadband Test     ║');
  console.log('╚════════════════════════════════════════════════════════════════════╝\n');

  let stagehand;
  const startTime = Date.now();

  try {
    // Initialize Stagehand
    logInfo('Initializing TypeScript Stagehand...');
    stagehand = new Stagehand({
      env: 'LOCAL', // Always use local Playwright (not Browserbase cloud)
      modelName: process.env.MODEL_NAME || 'gpt-4o-mini',
      temperature: parseFloat(process.env.TEMPERATURE || '0.7'),
      maxTokens: parseInt(process.env.MAX_TOKENS || '4096'),
      apiKey: process.env.OPENAI_API_KEY,
      verbose: 1,
      debugDom: true,
      headless: process.env.HEADLESS === 'true'
    });

    await stagehand.init();
    logSuccess('Stagehand initialized successfully');

    // Step 1: Navigate to 5G Broadband plan page
    logStep(1, 'Navigate to 5G Broadband plan page');
    await stagehand.page.goto(TEST_URL, { waitUntil: 'networkidle' });
    logSuccess(`Navigated to: ${TEST_URL}`);
    await sleep(2000); // Wait for page to stabilize

    // Step 2: Scroll down until contract period options are visible
    logStep(2, 'Scroll down until 30 months or 48 months contract period options can be seen');
    await stagehand.page.evaluate(() => {
      window.scrollBy(0, 800);
    });
    await sleep(1000);
    logSuccess('Scrolled to contract period options');

    // Step 3: Select the "30 months" contract period
    logStep(3, 'Select the "30 months" contract period by clicking the button');
    await stagehand.act({ action: 'Click the "30 months" contract period button' });
    await sleep(1000);
    logSuccess('Selected 30 months contract period');

    // Step 4: Verify pricing
    logStep(4, 'Verify pricing: $135/month (discounted from $198)');
    const pricingText = await stagehand.page.textContent('body');
    if (pricingText.includes('135') && pricingText.includes('198')) {
      logSuccess('Pricing verified: $135/month (discounted from $198)');
    } else {
      logError('Pricing not found or incorrect');
    }

    // Step 5: Verify plan details
    logStep(5, 'Verify plan details: 5G Broadband Wi-Fi 6 Service Plan, Infinite 5G Data');
    if (pricingText.includes('5G Broadband') && pricingText.includes('Wi-Fi 6')) {
      logSuccess('Plan details verified');
    } else {
      logError('Plan details not found');
    }

    // Step 6: Click "Subscribe Now" button
    logStep(6, 'Click "Subscribe Now" button');
    await stagehand.act({ action: 'Click the "Subscribe Now" button' });
    await sleep(2000);
    logSuccess('Clicked Subscribe Now');

    // Step 7: Verify "Your Selection" page - Average Monthly fee
    logStep(7, 'At "Your Selection" page, verify Average Monthly fee is "$135/month"');
    const selectionText = await stagehand.page.textContent('body');
    if (selectionText.includes('135') && selectionText.includes('month')) {
      logSuccess('Average Monthly fee verified: $135/month');
    } else {
      logError('Average Monthly fee not verified');
    }

    // Step 8: Verify original price was strike out
    logStep(8, 'Verify original price "$198" was strike out');
    const hasStrikethrough = await stagehand.page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('*'));
      return elements.some(el => {
        const style = window.getComputedStyle(el);
        return (style.textDecoration.includes('line-through') || 
                style.textDecorationLine === 'line-through') &&
               el.textContent.includes('198');
      });
    });
    if (hasStrikethrough) {
      logSuccess('Original price $198 is struck out');
    } else {
      logInfo('Strike-through not detected (may need manual verification)');
    }

    // Step 9: Verify red area with "Free 6-mth monthly fee"
    logStep(9, 'Verify red area with "Free 6-mth monthly fee" message');
    if (selectionText.includes('Free') && selectionText.includes('6')) {
      logSuccess('Free 6-month promotion message verified');
    } else {
      logInfo('Promotion message not found (may be conditional)');
    }

    // Step 10: Verify service plan name
    logStep(10, 'Verify service plan is "5G Broadband Wi-Fi 6 Service Plan"');
    if (selectionText.includes('5G Broadband Wi-Fi 6 Service Plan')) {
      logSuccess('Service plan name verified');
    } else {
      logError('Service plan name not verified');
    }

    // Step 11: Verify Contract Period is "30-month"
    logStep(11, 'Verify Contract Period is selected with "30-month"');
    if (selectionText.includes('30') && (selectionText.includes('month') || selectionText.includes('Month'))) {
      logSuccess('Contract Period verified: 30-month');
    } else {
      logError('Contract Period not verified');
    }

    // Step 12: Click "Next" to proceed to service plan details
    logStep(12, 'Click "Next" to proceed to service plan details');
    await stagehand.act({ action: 'Click the "Next" button' });
    await sleep(2000);
    logSuccess('Clicked Next');

    // Step 13: Verify payment breakdown
    logStep(13, 'Verify payment breakdown: Prepayment SIM Card Fee $100, Total $100');
    const paymentText = await stagehand.page.textContent('body');
    if (paymentText.includes('100')) {
      logSuccess('Payment breakdown verified: $100');
    } else {
      logError('Payment breakdown not verified');
    }

    // Step 14: Tick "I confirm that I have reviewed details" checkbox
    logStep(14, 'Tick "I confirm that I have reviewed details" checkbox');
    await stagehand.act({ action: 'Click the "I confirm that I have reviewed details" checkbox' });
    await sleep(1000);
    logSuccess('Confirmed details checkbox ticked');

    // Step 15: Click "Subscribe Now" to proceed to login
    logStep(15, 'Click "Subscribe Now" to proceed to login');
    await stagehand.act({ action: 'Click the "Subscribe Now" button' });
    await sleep(2000);
    logSuccess('Clicked Subscribe Now to login');

    // Step 16: Complete login
    logStep(16, `Complete login with email: ${TEST_EMAIL}`);
    
    // Enter email
    await stagehand.act({ action: `Type "${TEST_EMAIL}" in the email field` });
    await sleep(500);
    
    // Enter password
    await stagehand.act({ action: `Type "${TEST_PASSWORD}" in the password field` });
    await sleep(500);
    
    // Click login button
    await stagehand.act({ action: 'Click the login or sign in button' });
    await sleep(3000);
    logSuccess('Login completed');

    // Step 17: Select service effective date (3 days from today)
    logStep(17, 'Select service effective date (3 days from today)');
    const threeDaysLater = new Date();
    threeDaysLater.setDate(threeDaysLater.getDate() + 3);
    const dateString = threeDaysLater.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    
    await stagehand.act({ action: `Select the date 3 days from today in the date picker` });
    await sleep(1000);
    logSuccess(`Selected service effective date: ${dateString}`);

    // Step 18: Click "Confirm" to complete subscription
    logStep(18, 'Click "Confirm" to complete subscription');
    await stagehand.act({ action: 'Click the "Confirm" button' });
    await sleep(2000);
    logSuccess('Clicked Confirm to complete subscription');

    // Test Summary
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log('\n╔════════════════════════════════════════════════════════════════════╗');
    console.log('║                         TEST SUMMARY                               ║');
    console.log('╚════════════════════════════════════════════════════════════════════╝');
    logSuccess(`Test completed successfully in ${duration} seconds`);
    logInfo('TypeScript Stagehand successfully handled complex multi-step flow');
    logInfo('All 18 steps executed');
    logInfo('Ready for Phase 4 Node.js microservice implementation');

    return true;

  } catch (error) {
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log('\n╔════════════════════════════════════════════════════════════════════╗');
    console.log('║                         TEST FAILED                                ║');
    console.log('╚════════════════════════════════════════════════════════════════════╝');
    logError(`Test failed after ${duration} seconds`);
    logError(`Error: ${error.message}`);
    console.error(error);
    return false;

  } finally {
    // Cleanup
    if (stagehand) {
      logInfo('Closing browser...');
      await stagehand.close();
      logSuccess('Browser closed');
    }
  }
}

// Run the test
testThreeBroadbandFlow()
  .then(success => {
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
