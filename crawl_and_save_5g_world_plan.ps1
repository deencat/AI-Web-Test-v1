# Submit crawl-and-save job
# browser-use ONLY navigates to the subscription options page.
# All form filling (SIM type, address, payment, signature) is in tail_steps
# and executed by the reliable 3-tier system - avoids agent looping on SPA dropdowns.
$user_instruction = 'Login with the provided credentials. After login: do NOT click Settings, do NOT click Download My3 App. Click 5G Monthly Plan on the left menu. Find the World Plan at $368/month and click Subscribe Now. Agree to Terms and Conditions if a modal appears. STOP as soon as the subscription options form appears (page with Service Subscription, SIM Card Type, Value-added Service options). Do NOT fill any fields. Do NOT click Next. Stop immediately.'

$bodyObj = @{
    url               = 'https://wwwuat.three.com.hk/DTPPD/postpaid/preprod0/en/'
    user_instruction  = $user_instruction
    stop_at_page_hint = 'subscription option'
    tail_steps        = @(
        "Select 'New Mobile Number' as Service Subscription",
        "Select 'Physical SIM' as SIM Card Type",
        "Select 'Free Zurich 24-Month Travel Insurance' as Free Value-added Service",
        "Leave the Referral Number field blank",
        "Click the Next button to proceed to SIM Card Setting",
        "At SIM Card Setting page, select a mobile number from the available list",
        "On the Service Effective Date field, click the date picker and select any available date",
        "Input contact number '91234567'",
        "Click the Next button to proceed",
        "Click 'Enter address manually'",
        "Select 'HONG KONG' from the Region dropdown",
        "Select 'EASTERN' from the District dropdown",
        "Input Floor '5'",
        "Input Room 'E'",
        "Input Street 'Happy street'",
        "Click the Next button to proceed",
        "Upload the HKID document from C:\Users\andrechw\Downloads\ekyctest\test06.jpg",
        "Wait for upload to complete",
        "Click the Next button to proceed",
        "At Auto-pay Setup page, input credit card number '4111111111111111'",
        "Input card holder name 'test'",
        "Input expiry date '01/39'",
        "Click the Next button to proceed",
        "At Contract Signature page, sign under Subscriber's signature",
        "Check the 'I confirm to subscribe' checkbox",
        "Check the 'I have read and agree to T and C' checkbox",
        "Click the Next button to proceed",
        "Click the Next button to proceed",
        "At Payment Method page, click the Visa/Master image",
        "Click the Checkout button",
        "Input credit card number '4111111111111111'",
        "Select expiry month '01' from the dropdown",
        "Select expiry year '39' from the dropdown",
        "Input card holder name 'test'",
        "Input CVV '100'",
        "Click the Pay Now button",
        "Click the Submit button",
        "Wait for the confirmation page, then click the Back to Home button"
    )

    #tail_steps        = @(
    #    "At SIM Card Setting page, on 'New Mobile Number', select one number from the available list",
    #    "On 'Service Effective Date' field, click Next button and select any date",
    #    "On 'Contact Number' field, enter '91234567'",
    #    "Click the Next button to proceed",
    #    "At Auto-pay Setup page, enter '4111111111111111' as credit card number",
    ##    "Enter 'Chan Dai Man' as Card Holder Name",
    #    "Click the Next button to proceed",
    #    "At Contract Signature page, check all the checkboxes",
    #    "Do not click 'Preview' button, do not click 'Terms & Conditions' link, do not click 'Privacy Policy' link",
    #    "Click Next to proceed",
    ##    "Do not click on 'My Wallet' at the side menu",
    #    "At Payment Method page, click on the Visa image (img tag with alt='Visa')",
    #    "Click the Checkout button",
    #    "Complete the rest of the purchase flow until the successful subscribed confirmation page"
    #)
    test_title        = '5G World Plan $368/month - New Mobile Number (Physical SIM)'
    test_description  = 'E2E subscription flow for 5G Monthly World Plan. Navigational steps auto-crawled by browser-use up to the subscription options page; all form-filling (SIM options, SIM Card Setting, address, HKID, autopay, signature, payment) are hardcoded tail steps executed via 3-tier testing.'
    test_type         = 'e2e'
    priority          = 'high'
    login_credentials = @{
        username = 'pmo.andrewchan+015@gmail.com'
        password = 'cA8mn49&'
    }
    available_file_paths     = @('C:\Users\andrechw\Downloads\ekyctest\test06.jpg')
    max_browser_steps        = 50
    max_flow_timeout_seconds = 600
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
