# Submit crawl-and-save job (no login required)
$user_instruction = 'First login as customer using the provided credentials. After login, do not click on "Settings" button, Do not click "Download My3 App" button at all time. Click on "5G Monthly Plan" on the left menu and then Subscribe the $368/month plan - World Plan. Select "New Mobile Number" as Service Subscription and "Physical SIM" as SIM Card Type, "Free Zurich 24-Month Travel Insurance" as Free Value-added service, leave blank for "Referral Number". STOP immediately when you reach the SIM Card Setting page - do not proceed further.'

$bodyObj = @{
    url               = 'https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/'
    user_instruction  = $user_instruction
    stop_at_page_hint = 'SIM Card Setting'
    tail_steps        = @(
        "At SIM Card Setting page, on 'New Mobile Number', select one number from the available list",
        "On 'Service Effective Date' field, click Next button and select any date",
        "On 'Contact Number' field, enter '91234567'",
        "Click the Next button to proceed",
        "At Auto-pay Setup page, enter '4111111111111111' as credit card number",
        "Enter 'Chan Dai Man' as Card Holder Name",
        "Click the Next button to proceed",
        "At Contract Signature page, check all the checkboxes",
        "Do not click 'Preview' button, do not click 'Terms & Conditions' link, do not click 'Privacy Policy' link",
        "Click Next to proceed",
        "Do not click on 'My Wallet' at the side menu",
        "At Payment Method page, click on the Visa image (img tag with alt='Visa')",
        "Click the Checkout button",
        "Complete the rest of the purchase flow until the successful subscribed confirmation page"
    )
    test_title        = '5G World Plan $368/month - New Mobile Number (Physical SIM)'
    test_description  = 'E2E subscription flow for 5G Monthly World Plan. Navigational steps auto-crawled by browser-use up to SIM Card Setting page; SIM settings, autopay, signature and payment steps are hardcoded tail steps executed via 3-tier testing.'
    test_type         = 'e2e'
    priority          = 'high'
    login_credentials = @{
        username = 'pmo.andrewchan+015@gmail.com'
        password = 'cA8mn49&'
    }
    available_file_paths     = @('C:\Users\andrechw\Downloads\ekyctest\test06.jpg')
    max_browser_steps        = 200
    max_flow_timeout_seconds = 2400
    tags                     = @('5g', 'world-plan', 'physical-sim', 'new-mobile-number', 'purchase-flow')
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
} while ($status.status -notin @('completed','failed'))

# Show result
$result = Invoke-RestMethod -Uri "http://localhost:8000/api/v2/workflows/$workflowId/results"
if ($status.status -eq 'completed') {
    Write-Host "SUCCESS! Test case saved as ID: $($result.result.test_case_id)"
    Write-Host "Steps: $($result.result.total_steps) total ($($result.result.crawled_steps_count) crawled + $($result.result.tail_steps_count) tail)"
    Write-Host "View at: http://localhost:5173/tests/saved"
} else {
    Write-Host "FAILED: $($result.error)"
}
