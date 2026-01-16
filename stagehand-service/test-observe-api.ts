/**
 * Quick test to understand stagehand.observe() API response structure
 */
import { Stagehand } from '@browserbasehq/stagehand';
import dotenv from 'dotenv';

dotenv.config();

async function testObserveAPI() {
  console.log('Testing Stagehand observe() API...\n');
  
  const stagehand = new Stagehand({
    env: 'LOCAL',
    modelName: 'gpt-4o-mini',
    apiKey: process.env.OPENAI_API_KEY,
    verbose: 1,
    headless: false
  });

  try {
    await stagehand.init();
    console.log('✅ Stagehand initialized\n');

    // Navigate to a simple test page
    await stagehand.page.goto('https://github.com/login', { waitUntil: 'networkidle' });
    console.log('✅ Navigated to GitHub login page\n');

    // Prime the act handler first (required before observe)
    console.log('Priming act handler...\n');
    await stagehand.act({ action: 'observe the page' });
    console.log('✅ Act handler primed\n');

    // Test observe() and see what it returns
    console.log('Calling stagehand.observe({ instruction: "find the login button" })...\n');
    const observeResult = await stagehand.observe({ instruction: "find the login button" });
    
    console.log('='.repeat(70));
    console.log('OBSERVE RESULT:');
    console.log('='.repeat(70));
    console.log(JSON.stringify(observeResult, null, 2));
    console.log('='.repeat(70));
    
    // Also check the type
    console.log(`\nResult type: ${typeof observeResult}`);
    console.log(`Is Array: ${Array.isArray(observeResult)}`);
    
    if (Array.isArray(observeResult) && observeResult.length > 0) {
      console.log(`\nFirst element structure:`);
      console.log(JSON.stringify(observeResult[0], null, 2));
      console.log(`\nFirst element keys: ${Object.keys(observeResult[0]).join(', ')}`);
    }

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    await stagehand.close();
    console.log('\n✅ Cleanup complete');
  }
}

testObserveAPI().catch(console.error);
