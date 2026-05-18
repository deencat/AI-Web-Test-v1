"""Fix crawl_and_save_5g_world_plan.ps1 tail_steps with proper clean content."""
import re

NEW_TAIL = r"""    tail_steps        = @(
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
    )"""

path = "crawl_and_save_5g_world_plan.ps1"
content = open(path, encoding="utf-8").read()
new_content = re.sub(
    r"    tail_steps\s*=\s*@\(.*?\n    \)",
    NEW_TAIL,
    content,
    flags=re.DOTALL,
)
open(path, "w", encoding="utf-8").write(new_content)
print("Done.")
print("Has 'Step 18: wait':", "Step 18: wait" in new_content)
print("Has 'HONG KONG':", "HONG KONG" in new_content)
print("Has 'subscription option':", "subscription option" in new_content)
print("Has corrupted char:", "\ue93b" in new_content)
