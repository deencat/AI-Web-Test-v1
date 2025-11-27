"""
Test Template Service
Manages test template CRUD operations and statistics
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from app.models.test_template import TestTemplate
from app.models.kb_document import KBCategory


class TestTemplateService:
    """Service for managing test templates"""
    
    @staticmethod
    def create_template(
        db: Session,
        name: str,
        template_type: str,
        steps_template: list,
        assertion_template: dict,
        created_by: int,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        data_requirements: Optional[dict] = None,
        is_system: bool = False
    ) -> TestTemplate:
        """Create a new test template"""
        template = TestTemplate(
            name=name,
            description=description,
            template_type=template_type,
            category_id=category_id,
            steps_template=steps_template,
            assertion_template=assertion_template,
            data_requirements=data_requirements or {},
            created_by=created_by,
            is_system=is_system
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template
    
    @staticmethod
    def get_template(db: Session, template_id: int) -> Optional[TestTemplate]:
        """Get template by ID"""
        return db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
    
    @staticmethod
    def get_templates(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        template_type: Optional[str] = None,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[TestTemplate]:
        """Get templates with filters"""
        query = db.query(TestTemplate)
        
        if template_type:
            query = query.filter(TestTemplate.template_type == template_type)
        if category_id:
            query = query.filter(TestTemplate.category_id == category_id)
        if is_active is not None:
            query = query.filter(TestTemplate.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_templates_by_type(db: Session, template_type: str) -> List[TestTemplate]:
        """Get all active templates of a specific type"""
        return db.query(TestTemplate)\
            .filter(TestTemplate.template_type == template_type)\
            .filter(TestTemplate.is_active == True)\
            .all()
    
    @staticmethod
    def update_template(
        db: Session,
        template_id: int,
        **kwargs
    ) -> Optional[TestTemplate]:
        """Update template fields"""
        template = db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
        if not template:
            return None
        
        # Don't allow updating system templates
        if template.is_system and not kwargs.get('allow_system_update', False):
            return None
        
        # Remove internal flags
        kwargs.pop('allow_system_update', None)
        
        for key, value in kwargs.items():
            if hasattr(template, key) and value is not None:
                setattr(template, key, value)
        
        db.commit()
        db.refresh(template)
        return template
    
    @staticmethod
    def delete_template(db: Session, template_id: int) -> bool:
        """Delete template (cannot delete system templates)"""
        template = db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
        if not template:
            return False
        
        # Cannot delete system templates
        if template.is_system:
            return False
        
        db.delete(template)
        db.commit()
        return True
    
    @staticmethod
    def clone_template(
        db: Session,
        template_id: int,
        new_name: str,
        created_by: int
    ) -> Optional[TestTemplate]:
        """Clone an existing template"""
        original = db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
        if not original:
            return None
        
        cloned = TestTemplate(
            name=new_name,
            description=f"Cloned from: {original.name}",
            template_type=original.template_type,
            category_id=original.category_id,
            steps_template=original.steps_template.copy(),
            assertion_template=original.assertion_template.copy(),
            data_requirements=original.data_requirements.copy() if original.data_requirements else {},
            created_by=created_by,
            is_system=False  # Clones are never system templates
        )
        db.add(cloned)
        db.commit()
        db.refresh(cloned)
        return cloned
    
    @staticmethod
    def increment_usage(db: Session, template_id: int):
        """Increment template usage count"""
        template = db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
        if template:
            template.increment_usage()
            db.commit()
    
    @staticmethod
    def update_success_rate(db: Session, template_id: int, success: bool):
        """Update template success rate"""
        template = db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
        if template:
            template.update_success_rate(success)
            db.commit()
    
    @staticmethod
    def validate_template_structure(template_data: dict) -> Tuple[bool, List[str]]:
        """
        Validate template JSON structure
        Returns (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        required_fields = ['name', 'template_type', 'steps_template', 'assertion_template']
        for field in required_fields:
            if field not in template_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate template type
        valid_types = ['api', 'mobile', 'e2e', 'performance']
        if 'template_type' in template_data and template_data['template_type'] not in valid_types:
            errors.append(f"Invalid template_type. Must be one of: {', '.join(valid_types)}")
        
        # Validate steps_template is array
        if 'steps_template' in template_data and not isinstance(template_data['steps_template'], list):
            errors.append("steps_template must be an array")
        
        # Validate each step has required fields
        if isinstance(template_data.get('steps_template'), list):
            for i, step in enumerate(template_data['steps_template']):
                if not isinstance(step, dict):
                    errors.append(f"Step {i} must be an object")
                    continue
                if 'action' not in step:
                    errors.append(f"Step {i} missing 'action' field")
        
        # Validate assertion_template is object
        if 'assertion_template' in template_data and not isinstance(template_data['assertion_template'], dict):
            errors.append("assertion_template must be an object")
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def get_popular_templates(db: Session, limit: int = 10) -> List[TestTemplate]:
        """Get most used templates"""
        return db.query(TestTemplate)\
            .filter(TestTemplate.is_active == True)\
            .order_by(TestTemplate.usage_count.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_best_templates(db: Session, limit: int = 10) -> List[TestTemplate]:
        """Get templates with highest success rate"""
        return db.query(TestTemplate)\
            .filter(TestTemplate.is_active == True)\
            .filter(TestTemplate.usage_count >= 5)\
            .order_by(TestTemplate.success_rate.desc())\
            .limit(limit)\
            .all()
