# Submit crawl-and-save job — Step Library edition
#
# browser-use crawls ONLY the navigational run-up:
#   Navigate → login (stripped) → click 5G Monthly Plan → find World Plan → Subscribe Now → stop
#
# Step Library modules handle the reusable parts:
#   @module:login_my3_andrew()                          — replaces captured login steps
#   @module:plan_subscribe_flow_existing_preprod_andrew — if existing subscriber popup detected
#   @module:plan_subscriber_flow_andrew                 — if no popup (new subscriber)
#
# subscriber_type_hint = 'auto' lets the server auto-detect from browser-use history.
# Override with 'existing' or 'new' if you already know the account type.

$user_instruction = 'Login with the provided credentials. After login: do NOT click Settings, do NOT click Download My3 App.
Click 5G Monthly Plan on the left menu. Click voucher monthly plan tab. Find and Select $288 plan with 36 months contract from the available plans. Complete the whole purchase flow until the successful subscribed page.'

$bodyObj = @{
    url                        = 'https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/'
    user_instruction           = $user_instruction
    stop_at_page_hint          = 'SIM Card Setting'

    # Step Library — replaces tail_steps
    login_module               = 'login_my3_andrew'
    existing_subscriber_module = 'plan_subscribe_flow_existing_preprod_andrew'
    new_subscriber_module      = 'plan_subscriber_flow_andrew'
    subscriber_type_hint       = 'auto'   # 'auto' | 'existing' | 'new'

    test_title        = '5G Monthly Voucher Plan $288/month - Step Library (auto subscriber detect)'
    test_description  = 'E2E subscription flow for 5G Monthly Voucher Plan $288/month. Navigational steps auto-crawled by browser-use up to the subscription options page. Login and full checkout flow are handled by Step Library modules resolved at execution time.'
    test_type         = 'e2e'
    priority          = 'high'
    login_credentials = @{
        username = 'pmo.andrewchan+015@gmail.com'
        password = 'cA8mn49&'
    }
    available_file_paths     = @('C:\Users\andrechw\Downloads\ekyctest\test06.jpg')
    max_browser_steps        = 50
    max_flow_timeout_seconds = 600
    tags                     = @('5g', 'voucher-plan', 'step-library', 'purchase-flow')

    # LLM review pass — compare generated steps against this model-answer test case
    # and remove noise (price labels, repeated Next loops, off-script forms).
    # Set to $null to skip the review pass.
    reference_test_id        = 1217
}

# Safety check: abort if a browser-use (chrome) process is already running
$existingChrome = Get-Process -Name "chrome","chromium" -ErrorAction SilentlyContinue
if ($existingChrome) {
    Write-Host "⚠️  WARNING: $($existingChrome.Count) Chrome process(es) already running."
    Write-Host "   A previous crawl may still be in progress."
    $confirm = Read-Host "Kill existing browser(s) and continue? [y/N]"
    if ($confirm -notmatch '^[Yy]') { Write-Host "Aborted."; exit 1 }
    $existingChrome | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Host "Cleared. Proceeding..."
}

$json     = $bodyObj | ConvertTo-Json -Depth 20
$response = Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/api/v2/crawl-and-save-test' -Body $json -ContentType 'application/json; charset=utf-8'

Write-Host "Workflow started! ID: $($response.workflow_id)"
$workflowId = $response.workflow_id

# Poll until done
do {
    Start-Sleep -Seconds 15
    $status = Invoke-RestMethod -Uri "http://localhost:8000/api/v2/workflows/$workflowId"
    Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] Status: $($status.status) | Agent: $($status.current_agent)"
} while ($status.status -notin @('completed', 'failed'))

# Show result
$result = Invoke-RestMethod -Uri "http://localhost:8000/api/v2/workflows/$workflowId/results"
if ($status.status -eq 'completed') {
    Write-Host "SUCCESS! Test case saved as ID: $($result.result.test_case_id)"
    Write-Host "Steps: $($result.result.total_steps) total ($($result.result.crawled_steps_count) crawled)"
    Write-Host "Login module   : $($result.result.login_module)"
    Write-Host "Subscriber type: $($result.result.subscriber_type)"
    Write-Host "Tail module    : $(if ($result.result.subscriber_type -eq 'existing') { $result.result.existing_subscriber_module } else { $result.result.new_subscriber_module })"
    Write-Host "View at: http://localhost:5173/tests/saved"
} else {
    Write-Host "FAILED: $($result.error)"
}
