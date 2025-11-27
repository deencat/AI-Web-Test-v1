"""
Scenario Generator Service
AI-powered test scenario generation with Faker integration
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple
from faker import Faker
import re
from datetime import datetime

from app.models.test_scenario import TestScenario
from app.models.test_template import TestTemplate
from app.services.test_template_service import TestTemplateService


class ScenarioGeneratorService:
    """Service for AI-powered test scenario generation"""
    
    def __init__(self):
        self.faker = Faker()
        
    @staticmethod
    def create_scenario(
        db: Session,
        name: str,
        steps: list,
        created_by: int,
        description: Optional[str] = None,
        template_id: Optional[int] = None,
        dependencies: Optional[list] = None,
        test_data: Optional[dict] = None,
        expected_results: Optional[dict] = None
    ) -> TestScenario:
        """Create a new test scenario"""
        scenario = TestScenario(
            name=name,
            description=description,
            template_id=template_id,
            steps=steps,
            dependencies=dependencies or [],
            test_data=test_data or {},
            expected_results=expected_results or {},
            created_by=created_by
        )
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        return scenario
    
    def generate_from_template(
        self,
        db: Session,
        template_id: int,
        context: dict,
        created_by: int,
        use_ai: bool = True,
        generate_data: bool = True
    ) -> TestScenario:
        """
        Generate scenario from template
        
        Args:
            db: Database session
            template_id: ID of template to use
            context: User-provided context (variable values)
            created_by: User ID creating the scenario
            use_ai: Use AI enhancement (future feature)
            generate_data: Generate faker data
        
        Returns:
            Generated TestScenario
        """
        # Get template
        template = TestTemplateService.get_template(db, template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Generate test data if needed
        test_data = {}
        if generate_data and template.data_requirements:
            test_data = self.generate_faker_data(template.data_requirements)
        
        # Merge context and generated data
        all_data = {**test_data, **context}
        
        # Expand template steps with data
        expanded_steps = self._expand_steps(template.steps_template, all_data)
        
        # Generate scenario name
        scenario_name = context.get('name', f"{template.name} - {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
        
        # Create scenario
        scenario = self.create_scenario(
            db=db,
            name=scenario_name,
            description=context.get('description', f"Generated from template: {template.name}"),
            template_id=template_id,
            steps=expanded_steps,
            test_data=all_data,
            expected_results=template.assertion_template,
            created_by=created_by
        )
        
        # Increment template usage
        TestTemplateService.increment_usage(db, template_id)
        
        return scenario
    
    def generate_faker_data(self, data_requirements: dict) -> dict:
        """
        Generate realistic test data using Faker
        
        data_requirements format:
        {
            "user": ["email", "name", "phone"],
            "address": ["street", "city", "country"],
            "product": ["name", "price"]
        }
        
        Returns: Nested dict with generated data
        """
        generated = {}
        
        for category, fields in data_requirements.items():
            generated[category] = {}
            
            for field in fields:
                value = self._generate_field_value(category, field)
                generated[category][field] = value
        
        return generated
    
    def _generate_field_value(self, category: str, field: str) -> Any:
        """Generate value for a specific field using Faker"""
        # User fields
        if category == "user":
            if field == "email":
                return self.faker.email()
            elif field == "name":
                return self.faker.name()
            elif field == "first_name":
                return self.faker.first_name()
            elif field == "last_name":
                return self.faker.last_name()
            elif field == "username":
                return self.faker.user_name()
            elif field == "password":
                return self.faker.password(length=12)
            elif field == "phone":
                return self.faker.phone_number()
            elif field == "ssn":
                return self.faker.ssn()
            elif field == "job":
                return self.faker.job()
        
        # Address fields
        elif category == "address":
            if field == "street":
                return self.faker.street_address()
            elif field == "city":
                return self.faker.city()
            elif field == "state":
                return self.faker.state()
            elif field == "country":
                return self.faker.country()
            elif field == "zipcode" or field == "zip":
                return self.faker.zipcode()
            elif field == "full":
                return self.faker.address()
        
        # Product fields
        elif category == "product":
            if field == "name":
                return f"{self.faker.word().capitalize()} {self.faker.word().capitalize()}"
            elif field == "price":
                return round(self.faker.random.uniform(10.0, 1000.0), 2)
            elif field == "sku":
                return self.faker.bothify(text='???-########')
            elif field == "description":
                return self.faker.sentence(nb_words=10)
        
        # Company fields
        elif category == "company":
            if field == "name":
                return self.faker.company()
            elif field == "email":
                return self.faker.company_email()
            elif field == "phone":
                return self.faker.phone_number()
        
        # Text fields
        elif category == "text":
            if field == "sentence":
                return self.faker.sentence()
            elif field == "paragraph":
                return self.faker.paragraph()
            elif field == "title":
                return self.faker.sentence(nb_words=5).rstrip('.')
            elif field == "word":
                return self.faker.word()
        
        # Date/Time fields
        elif category == "datetime":
            if field == "date":
                return self.faker.date()
            elif field == "time":
                return self.faker.time()
            elif field == "datetime":
                return str(self.faker.date_time())
            elif field == "future_date":
                return self.faker.future_date()
            elif field == "past_date":
                return self.faker.past_date()
        
        # Internet fields
        elif category == "internet":
            if field == "url":
                return self.faker.url()
            elif field == "domain":
                return self.faker.domain_name()
            elif field == "ip":
                return self.faker.ipv4()
            elif field == "mac":
                return self.faker.mac_address()
            elif field == "user_agent":
                return self.faker.user_agent()
        
        # Numbers
        elif category == "number":
            if field == "integer":
                return self.faker.random_int(min=1, max=1000)
            elif field == "float":
                return round(self.faker.random.uniform(1.0, 1000.0), 2)
            elif field == "digit":
                return self.faker.random_digit()
        
        # Default: return a generic value
        return self.faker.word()
    
    def _expand_steps(self, steps_template: list, data: dict) -> list:
        """
        Expand template steps by replacing ${variables} with actual data
        
        Example:
        Template: [{"action": "fill", "field": "email", "value": "${user.email}"}]
        Data: {"user": {"email": "test@example.com"}}
        Result: [{"action": "fill", "field": "email", "value": "test@example.com"}]
        """
        expanded_steps = []
        
        for step in steps_template:
            expanded_step = self._expand_dict(step, data)
            expanded_steps.append(expanded_step)
        
        return expanded_steps
    
    def _expand_dict(self, obj: Any, data: dict) -> Any:
        """Recursively expand ${variables} in a dict/list/string"""
        if isinstance(obj, dict):
            return {k: self._expand_dict(v, data) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_dict(item, data) for item in obj]
        elif isinstance(obj, str):
            return self._replace_variables(obj, data)
        else:
            return obj
    
    def _replace_variables(self, text: str, data: dict) -> str:
        """
        Replace ${variable.path} with actual values from data
        
        Example:
        text = "Email: ${user.email}, Name: ${user.name}"
        data = {"user": {"email": "test@example.com", "name": "John"}}
        result = "Email: test@example.com, Name: John"
        """
        pattern = r'\$\{([^}]+)\}'
        
        def replace(match):
            path = match.group(1)
            value = self._get_nested_value(data, path)
            return str(value) if value is not None else match.group(0)
        
        return re.sub(pattern, replace, text)
    
    def _get_nested_value(self, data: dict, path: str) -> Any:
        """
        Get nested value from dict using dot notation
        
        Example:
        data = {"user": {"address": {"city": "NYC"}}}
        path = "user.address.city"
        result = "NYC"
        """
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    @staticmethod
    def get_scenario(db: Session, scenario_id: int) -> Optional[TestScenario]:
        """Get scenario by ID"""
        return db.query(TestScenario).filter(TestScenario.id == scenario_id).first()
    
    @staticmethod
    def get_scenarios(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        template_id: Optional[int] = None
    ) -> List[TestScenario]:
        """Get scenarios with filters"""
        query = db.query(TestScenario)
        
        if status:
            query = query.filter(TestScenario.status == status)
        if template_id:
            query = query.filter(TestScenario.template_id == template_id)
        
        return query.order_by(TestScenario.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_scenario(db: Session, scenario_id: int, **kwargs) -> Optional[TestScenario]:
        """Update scenario fields"""
        scenario = db.query(TestScenario).filter(TestScenario.id == scenario_id).first()
        if not scenario:
            return None
        
        for key, value in kwargs.items():
            if hasattr(scenario, key) and value is not None:
                setattr(scenario, key, value)
        
        db.commit()
        db.refresh(scenario)
        return scenario
    
    @staticmethod
    def delete_scenario(db: Session, scenario_id: int) -> bool:
        """Delete scenario"""
        scenario = db.query(TestScenario).filter(TestScenario.id == scenario_id).first()
        if not scenario:
            return False
        
        db.delete(scenario)
        db.commit()
        return True
    
    def get_available_faker_fields(self) -> dict:
        """
        Return list of available faker fields by category
        Useful for frontend to show available options
        """
        return {
            "user": [
                "email", "name", "first_name", "last_name", "username",
                "password", "phone", "ssn", "job"
            ],
            "address": [
                "street", "city", "state", "country", "zipcode", "zip", "full"
            ],
            "product": [
                "name", "price", "sku", "description"
            ],
            "company": [
                "name", "email", "phone"
            ],
            "text": [
                "sentence", "paragraph", "title", "word"
            ],
            "datetime": [
                "date", "time", "datetime", "future_date", "past_date"
            ],
            "internet": [
                "url", "domain", "ip", "mac", "user_agent"
            ],
            "number": [
                "integer", "float", "digit"
            ]
        }
