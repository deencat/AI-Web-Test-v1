"""Service for managing test case versions."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.models.test_version import TestCaseVersion
from app.models.test_case import TestCase


class VersionService:
    """Service for test case version control operations."""
    
    @staticmethod
    def save_version(
        db: Session,
        test_case_id: int,
        steps: List[str],
        created_by: str = "user",
        change_reason: str = "manual_edit",
        expected_result: Optional[str] = None,
        test_data: Optional[Dict[str, Any]] = None,
        parent_version_id: Optional[int] = None
    ) -> TestCaseVersion:
        """
        Save a new version of a test case.
        
        Args:
            db: Database session
            test_case_id: ID of the test case being versioned
            steps: Complete test steps for this version
            created_by: Who created this version ("user", "ai", or user_id)
            change_reason: Reason for the change ("manual_fix", "ai_improvement", "execution_failure")
            expected_result: Expected result at this version
            test_data: Test data at this version
            parent_version_id: ID of the parent version (for rollback tracking)
        
        Returns:
            TestCaseVersion: The newly created version
        """
        # Get the latest version number for this test case
        latest_version = db.query(TestCaseVersion).filter(
            TestCaseVersion.test_case_id == test_case_id
        ).order_by(desc(TestCaseVersion.version_number)).first()
        
        next_version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Create new version
        new_version = TestCaseVersion(
            test_case_id=test_case_id,
            version_number=next_version_number,
            steps=steps,
            expected_result=expected_result,
            test_data=test_data,
            created_by=created_by,
            change_reason=change_reason,
            parent_version_id=parent_version_id,
            created_at=datetime.utcnow()
        )
        
        db.add(new_version)
        db.commit()
        db.refresh(new_version)
        
        return new_version
    
    @staticmethod
    def get_version(db: Session, version_id: int) -> Optional[TestCaseVersion]:
        """
        Retrieve a specific version by ID.
        
        Args:
            db: Database session
            version_id: ID of the version to retrieve
        
        Returns:
            TestCaseVersion or None if not found
        """
        return db.query(TestCaseVersion).filter(TestCaseVersion.id == version_id).first()
    
    @staticmethod
    def get_version_history(
        db: Session,
        test_case_id: int,
        limit: int = 50
    ) -> List[TestCaseVersion]:
        """
        Get version history for a test case.
        
        Args:
            db: Database session
            test_case_id: ID of the test case
            limit: Maximum number of versions to return (default 50)
        
        Returns:
            List of TestCaseVersion objects, newest first
        """
        return db.query(TestCaseVersion).filter(
            TestCaseVersion.test_case_id == test_case_id
        ).order_by(desc(TestCaseVersion.created_at)).limit(limit).all()
    
    @staticmethod
    def get_latest_version(db: Session, test_case_id: int) -> Optional[TestCaseVersion]:
        """
        Get the latest version for a test case.
        
        Args:
            db: Database session
            test_case_id: ID of the test case
        
        Returns:
            TestCaseVersion or None if no versions exist
        """
        return db.query(TestCaseVersion).filter(
            TestCaseVersion.test_case_id == test_case_id
        ).order_by(desc(TestCaseVersion.version_number)).first()
    
    @staticmethod
    def rollback_to_version(
        db: Session,
        test_case_id: int,
        version_id: int,
        created_by: str = "user"
    ) -> TestCaseVersion:
        """
        Rollback a test case to a previous version.
        
        Creates a new version with the content from the specified version,
        preserving the version history.
        
        Args:
            db: Database session
            test_case_id: ID of the test case
            version_id: ID of the version to rollback to
            created_by: Who initiated the rollback
        
        Returns:
            TestCaseVersion: The new version created from rollback
        
        Raises:
            ValueError: If version not found or doesn't belong to test case
        """
        # Get the target version
        target_version = db.query(TestCaseVersion).filter(
            TestCaseVersion.id == version_id,
            TestCaseVersion.test_case_id == test_case_id
        ).first()
        
        if not target_version:
            raise ValueError(f"Version {version_id} not found for test case {test_case_id}")
        
        # Create new version with content from target version
        new_version = VersionService.save_version(
            db=db,
            test_case_id=test_case_id,
            steps=target_version.steps,
            expected_result=target_version.expected_result,
            test_data=target_version.test_data,
            created_by=created_by,
            change_reason=f"rollback_to_v{target_version.version_number}",
            parent_version_id=version_id
        )
        
        # Update the actual test case with the rollback content
        test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
        if test_case:
            test_case.steps = target_version.steps
            if target_version.expected_result:
                test_case.expected_result = target_version.expected_result
            if target_version.test_data:
                test_case.test_data = target_version.test_data
            db.commit()
        
        return new_version
    
    @staticmethod
    def compare_versions(
        db: Session,
        version_id_1: int,
        version_id_2: int
    ) -> Dict[str, Any]:
        """
        Compare two versions and return differences.
        
        Args:
            db: Database session
            version_id_1: ID of first version
            version_id_2: ID of second version
        
        Returns:
            Dictionary with comparison results
        """
        version_1 = db.query(TestCaseVersion).filter(TestCaseVersion.id == version_id_1).first()
        version_2 = db.query(TestCaseVersion).filter(TestCaseVersion.id == version_id_2).first()
        
        if not version_1 or not version_2:
            raise ValueError("One or both versions not found")
        
        # Simple comparison (can be enhanced with diff algorithms)
        return {
            "version_1": {
                "id": version_1.id,
                "version_number": version_1.version_number,
                "steps": version_1.steps,
                "created_at": version_1.created_at.isoformat(),
                "created_by": version_1.created_by
            },
            "version_2": {
                "id": version_2.id,
                "version_number": version_2.version_number,
                "steps": version_2.steps,
                "created_at": version_2.created_at.isoformat(),
                "created_by": version_2.created_by
            },
            "steps_changed": version_1.steps != version_2.steps,
            "steps_count_diff": len(version_2.steps) - len(version_1.steps) if isinstance(version_1.steps, list) and isinstance(version_2.steps, list) else None
        }
    
    @staticmethod
    def delete_old_versions(
        db: Session,
        test_case_id: int,
        keep_count: int = 10
    ) -> int:
        """
        Delete old versions, keeping only the most recent ones.
        
        Args:
            db: Database session
            test_case_id: ID of the test case
            keep_count: Number of recent versions to keep (default 10)
        
        Returns:
            Number of versions deleted
        """
        # Get all versions for this test case
        all_versions = db.query(TestCaseVersion).filter(
            TestCaseVersion.test_case_id == test_case_id
        ).order_by(desc(TestCaseVersion.version_number)).all()
        
        if len(all_versions) <= keep_count:
            return 0  # Nothing to delete
        
        # Get versions to delete (oldest ones)
        versions_to_delete = all_versions[keep_count:]
        
        deleted_count = 0
        for version in versions_to_delete:
            db.delete(version)
            deleted_count += 1
        
        db.commit()
        return deleted_count
