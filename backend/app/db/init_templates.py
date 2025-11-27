"""
Seed Built-in Test Templates
Creates system templates on server startup if they don't exist
"""
from sqlalchemy.orm import Session
from app.models.test_template import TestTemplate
from app.services.test_template_service import TestTemplateService
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


def seed_system_templates(db: Session):
    """
    Seed built-in system templates
    These templates cannot be deleted or modified by users
    """
    # Get system user (admin) for created_by
    system_user = db.query(User).filter(User.email == "admin@aiwebtest.com").first()
    if not system_user:
        logger.warning("Admin user not found, skipping template seeding")
        return
    
    templates = [
        {
            "name": "REST API Endpoint Test",
            "description": "Test a REST API endpoint with various HTTP methods",
            "template_type": "api",
            "steps_template": [
                {
                    "action": "request",
                    "method": "${method}",
                    "endpoint": "${endpoint}",
                    "headers": "${headers}",
                    "body": "${request_body}",
                    "description": "Send HTTP request to endpoint"
                },
                {
                    "action": "assert_response",
                    "status_code": "${expected_status}",
                    "response_schema": "${schema}",
                    "description": "Verify response status and structure"
                },
                {
                    "action": "assert",
                    "condition": "${validation_rule}",
                    "description": "Validate response data"
                }
            ],
            "assertion_template": {
                "response_time_ms": "< 1000",
                "status_code_match": True,
                "schema_valid": True
            },
            "data_requirements": {
                "user": ["email", "name"],
                "product": ["name", "price"]
            }
        },
        {
            "name": "E2E User Login Flow",
            "description": "Complete user login test with navigation and assertions",
            "template_type": "e2e",
            "steps_template": [
                {
                    "action": "navigate",
                    "url": "${base_url}/login",
                    "description": "Navigate to login page"
                },
                {
                    "action": "wait",
                    "condition": "page_loaded",
                    "timeout": 5000,
                    "description": "Wait for page to load"
                },
                {
                    "action": "fill_field",
                    "selector": "${email_selector}",
                    "value": "${test_email}",
                    "description": "Enter email"
                },
                {
                    "action": "fill_field",
                    "selector": "${password_selector}",
                    "value": "${test_password}",
                    "description": "Enter password"
                },
                {
                    "action": "click",
                    "selector": "${login_button}",
                    "description": "Click login button"
                },
                {
                    "action": "wait_for_navigation",
                    "expected_url": "${dashboard_url}",
                    "timeout": 5000,
                    "description": "Wait for redirect to dashboard"
                },
                {
                    "action": "assert_element",
                    "selector": "${success_indicator}",
                    "visible": True,
                    "description": "Verify successful login"
                }
            ],
            "assertion_template": {
                "login_successful": True,
                "redirected_to_dashboard": True,
                "session_token_present": True
            },
            "data_requirements": {
                "user": ["email", "password"]
            }
        },
        {
            "name": "E2E Form Submission",
            "description": "Test form filling and submission with validation",
            "template_type": "e2e",
            "steps_template": [
                {
                    "action": "navigate",
                    "url": "${form_url}",
                    "description": "Navigate to form page"
                },
                {
                    "action": "fill_field",
                    "selector": "${name_field}",
                    "value": "${user.name}",
                    "description": "Fill name field"
                },
                {
                    "action": "fill_field",
                    "selector": "${email_field}",
                    "value": "${user.email}",
                    "description": "Fill email field"
                },
                {
                    "action": "fill_field",
                    "selector": "${phone_field}",
                    "value": "${user.phone}",
                    "description": "Fill phone field"
                },
                {
                    "action": "click",
                    "selector": "${submit_button}",
                    "description": "Submit form"
                },
                {
                    "action": "wait",
                    "condition": "success_message_visible",
                    "timeout": 3000,
                    "description": "Wait for success message"
                },
                {
                    "action": "assert_element",
                    "selector": "${success_message}",
                    "text_contains": "success",
                    "description": "Verify submission success"
                }
            ],
            "assertion_template": {
                "form_submitted": True,
                "validation_passed": True,
                "success_message_shown": True
            },
            "data_requirements": {
                "user": ["name", "email", "phone"]
            }
        },
        {
            "name": "Mobile App Navigation Test",
            "description": "Test mobile app navigation flow",
            "template_type": "mobile",
            "steps_template": [
                {
                    "action": "launch_app",
                    "app_id": "${app_id}",
                    "description": "Launch mobile app"
                },
                {
                    "action": "wait",
                    "timeout": 3000,
                    "description": "Wait for app to load"
                },
                {
                    "action": "tap",
                    "element": "${menu_button}",
                    "description": "Tap menu button"
                },
                {
                    "action": "tap",
                    "element": "${target_screen}",
                    "description": "Navigate to target screen"
                },
                {
                    "action": "assert_element",
                    "element": "${screen_title}",
                    "visible": True,
                    "description": "Verify correct screen loaded"
                }
            ],
            "assertion_template": {
                "navigation_successful": True,
                "correct_screen_displayed": True
            },
            "data_requirements": {}
        },
        {
            "name": "API Performance Test",
            "description": "Load test for API endpoint performance",
            "template_type": "performance",
            "steps_template": [
                {
                    "action": "setup_load_test",
                    "concurrent_users": "${concurrent_users}",
                    "duration_seconds": "${duration}",
                    "ramp_up_seconds": "${ramp_up}",
                    "description": "Configure load test parameters"
                },
                {
                    "action": "request",
                    "method": "${method}",
                    "endpoint": "${endpoint}",
                    "headers": "${headers}",
                    "description": "Send requests under load"
                },
                {
                    "action": "measure_performance",
                    "metrics": ["response_time", "throughput", "error_rate"],
                    "description": "Collect performance metrics"
                },
                {
                    "action": "assert",
                    "condition": "avg_response_time < ${max_response_time}",
                    "description": "Verify performance SLA"
                }
            ],
            "assertion_template": {
                "avg_response_time_ms": "< 500",
                "error_rate_percent": "< 1",
                "throughput_rps": "> 100"
            },
            "data_requirements": {
                "number": ["integer"]
            }
        },
        {
            "name": "API CRUD Operations",
            "description": "Test Create, Read, Update, Delete operations",
            "template_type": "api",
            "steps_template": [
                {
                    "action": "request",
                    "method": "POST",
                    "endpoint": "${create_endpoint}",
                    "body": "${create_data}",
                    "description": "Create new resource"
                },
                {
                    "action": "assert_response",
                    "status_code": 201,
                    "save_id": "resource_id",
                    "description": "Verify creation successful"
                },
                {
                    "action": "request",
                    "method": "GET",
                    "endpoint": "${read_endpoint}/${resource_id}",
                    "description": "Read created resource"
                },
                {
                    "action": "assert_response",
                    "status_code": 200,
                    "description": "Verify resource retrieved"
                },
                {
                    "action": "request",
                    "method": "PUT",
                    "endpoint": "${update_endpoint}/${resource_id}",
                    "body": "${update_data}",
                    "description": "Update resource"
                },
                {
                    "action": "assert_response",
                    "status_code": 200,
                    "description": "Verify update successful"
                },
                {
                    "action": "request",
                    "method": "DELETE",
                    "endpoint": "${delete_endpoint}/${resource_id}",
                    "description": "Delete resource"
                },
                {
                    "action": "assert_response",
                    "status_code": 204,
                    "description": "Verify deletion successful"
                }
            ],
            "assertion_template": {
                "all_operations_successful": True,
                "data_integrity_maintained": True
            },
            "data_requirements": {
                "product": ["name", "price", "description"],
                "text": ["sentence"]
            }
        }
    ]
    
    created_count = 0
    existing_count = 0
    
    for template_data in templates:
        # Check if template already exists
        existing = db.query(TestTemplate).filter(TestTemplate.name == template_data["name"]).first()
        if existing:
            existing_count += 1
            continue
        
        # Create system template
        try:
            TestTemplateService.create_template(
                db=db,
                name=template_data["name"],
                description=template_data["description"],
                template_type=template_data["template_type"],
                steps_template=template_data["steps_template"],
                assertion_template=template_data["assertion_template"],
                data_requirements=template_data["data_requirements"],
                created_by=system_user.id,
                is_system=True  # Mark as system template
            )
            created_count += 1
            logger.info(f"Created system template: {template_data['name']}")
        except Exception as e:
            logger.error(f"Failed to create template '{template_data['name']}': {e}")
    
    logger.info(f"[TEMPLATES] System templates initialized: {created_count} created, {existing_count} existing")
