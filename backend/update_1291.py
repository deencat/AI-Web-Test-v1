"""One-time script to update test case #1291 with proper meaningful steps."""
import sqlite3, json

STEPS = [
    "Step 1: Navigate to https://wwwuat.three.com.hk/DTPPD/postpaid/preprod0/en/ in a web browser",
    "Step 2: Click the 'Login' button on the top right corner of the page",
    "Step 3: Input 'pmo.andrewchan+015@gmail.com' in the email address field",
    "Step 4: Click the 'Login' button to proceed to the password input page",
    "Step 5: Input 'cA8mn49&' in the password field",
    "Step 6: Click the 'Login' button to log in to the account",
    "Step 7: Click the 'Continue Browsing' button",
    "Step 8: Click the '5G Monthly Plans' button on the left menu",
    "Step 9: Click the 'Subscribe Now' button for the World Plan at $368/month",
    "Step 10: Agree to Terms and Conditions and click Subscribe Now to proceed",
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
    "Upload the HKID document from C:\\Users\\andrechw\\Downloads\\ekyctest\\test06.jpg",
    "Wait for upload to complete",
    "Click the Next button to proceed",
    "At Auto-pay Setup page, input credit card number '4111111111111111'",
    "Input card holder name 'test'",
    "Input expiry date '01/39'",
    "Click the Next button to proceed",
    "At Contract Signature page, sign under Subscriber's signature",
    "Check the 'I confirm to subscribe' checkbox",
    "Check the 'I have read and agree to T&C' checkbox",
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
    "Wait for the confirmation page, then click the 'Back to Home' button",
]

conn = sqlite3.connect('aiwebtest.db')
cur = conn.cursor()
cur.execute(
    "UPDATE test_cases SET steps=?, title=?, description=? WHERE id=1291",
    (
        json.dumps(STEPS),
        "5G World Plan $368/month - New Mobile Number (Physical SIM)",
        "E2E subscription flow for 5G Monthly World Plan. Navigational steps auto-crawled by browser-use up to subscription options; all form-filling is hardcoded tail steps executed via 3-tier testing.",
    )
)
conn.commit()
print(f"Updated {cur.rowcount} row(s). Total steps: {len(STEPS)}")
cur.execute("SELECT id, title, json_array_length(steps) FROM test_cases WHERE id=1291")
print(cur.fetchone())
conn.close()
