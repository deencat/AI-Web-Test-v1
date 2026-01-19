"""
CRUD operations for Execution Settings
Sprint 5.5: 3-Tier Execution Engine
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.execution_settings import ExecutionSettings, TierExecutionLog
from app.schemas.execution_settings import (
    ExecutionSettingsCreate,
    ExecutionSettingsUpdate
)


def get_execution_settings(db: Session, user_id: int) -> Optional[ExecutionSettings]:
    """
    Get execution settings for a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        ExecutionSettings if found, None otherwise
    """
    return db.query(ExecutionSettings).filter(
        ExecutionSettings.user_id == user_id
    ).first()


def create_execution_settings(
    db: Session,
    settings: ExecutionSettingsCreate
) -> ExecutionSettings:
    """
    Create new execution settings for a user.
    
    Args:
        db: Database session
        settings: Settings data
        
    Returns:
        Created ExecutionSettings
    """
    db_settings = ExecutionSettings(
        user_id=settings.user_id,
        fallback_strategy=settings.fallback_strategy,
        max_retry_per_tier=settings.max_retry_per_tier,
        timeout_per_tier_seconds=settings.timeout_per_tier_seconds,
        track_fallback_reasons=settings.track_fallback_reasons,
        track_strategy_effectiveness=settings.track_strategy_effectiveness
    )
    
    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    
    return db_settings


def update_execution_settings(
    db: Session,
    user_id: int,
    settings_update: ExecutionSettingsUpdate
) -> Optional[ExecutionSettings]:
    """
    Update execution settings for a user.
    
    Args:
        db: Database session
        user_id: User ID
        settings_update: Settings update data
        
    Returns:
        Updated ExecutionSettings if found, None otherwise
    """
    db_settings = get_execution_settings(db, user_id)
    
    if not db_settings:
        return None
    
    # Update only provided fields
    update_data = settings_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_settings, field, value)
    
    db.commit()
    db.refresh(db_settings)
    
    return db_settings


def get_or_create_execution_settings(
    db: Session,
    user_id: int
) -> ExecutionSettings:
    """
    Get execution settings for a user, or create with defaults if not exists.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        ExecutionSettings (existing or newly created)
    """
    settings = get_execution_settings(db, user_id)
    
    if not settings:
        # Create with defaults
        settings_create = ExecutionSettingsCreate(
            user_id=user_id,
            fallback_strategy="option_c",  # Default to maximum reliability
            max_retry_per_tier=1,
            timeout_per_tier_seconds=30,
            track_fallback_reasons=True,
            track_strategy_effectiveness=True
        )
        settings = create_execution_settings(db, settings_create)
    
    return settings


def delete_execution_settings(db: Session, user_id: int) -> bool:
    """
    Delete execution settings for a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        True if deleted, False if not found
    """
    db_settings = get_execution_settings(db, user_id)
    
    if not db_settings:
        return False
    
    db.delete(db_settings)
    db.commit()
    
    return True


def get_tier_distribution_stats(
    db: Session,
    user_id: Optional[int] = None,
    execution_id: Optional[int] = None
) -> dict:
    """
    Get tier distribution statistics.
    
    Args:
        db: Database session
        user_id: Optional user ID to filter by
        execution_id: Optional execution ID to filter by
        
    Returns:
        Dictionary with tier distribution statistics
    """
    query = db.query(TierExecutionLog)
    
    # Apply filters
    if execution_id:
        query = query.filter(TierExecutionLog.execution_id == execution_id)
    elif user_id:
        # Join with executions to filter by user
        from app.models.test_execution import TestExecution
        query = query.join(TestExecution).filter(TestExecution.user_id == user_id)
    
    logs = query.all()
    
    if not logs:
        return {
            "total_executions": 0,
            "tier1_success": 0,
            "tier1_failure": 0,
            "tier2_success": 0,
            "tier2_failure": 0,
            "tier3_success": 0,
            "tier3_failure": 0,
            "overall_success_rate": 0.0,
            "tier1_success_rate": 0.0,
            "tier2_success_rate": 0.0,
            "tier3_success_rate": 0.0,
            "avg_tier1_time_ms": 0.0,
            "avg_tier2_time_ms": 0.0,
            "avg_tier3_time_ms": 0.0
        }
    
    # Calculate statistics
    total = len(logs)
    tier1_success = sum(1 for log in logs if log.final_tier == 1 and log.success)
    tier1_failure = sum(1 for log in logs if log.tier1_error is not None)
    tier2_success = sum(1 for log in logs if log.final_tier == 2 and log.success)
    tier2_failure = sum(1 for log in logs if log.tier2_error is not None and log.final_tier != 2)
    tier3_success = sum(1 for log in logs if log.final_tier == 3 and log.success)
    tier3_failure = sum(1 for log in logs if log.tier3_error is not None and log.final_tier != 3)
    
    overall_success = sum(1 for log in logs if log.success)
    
    # Calculate average times
    tier1_times = [log.tier1_time_ms for log in logs if log.tier1_time_ms]
    tier2_times = [log.tier2_time_ms for log in logs if log.tier2_time_ms]
    tier3_times = [log.tier3_time_ms for log in logs if log.tier3_time_ms]
    
    return {
        "total_executions": total,
        "tier1_success": tier1_success,
        "tier1_failure": tier1_failure,
        "tier2_success": tier2_success,
        "tier2_failure": tier2_failure,
        "tier3_success": tier3_success,
        "tier3_failure": tier3_failure,
        "overall_success_rate": round(overall_success / total * 100, 2) if total > 0 else 0.0,
        "tier1_success_rate": round(tier1_success / len(tier1_times) * 100, 2) if tier1_times else 0.0,
        "tier2_success_rate": round(tier2_success / len(tier2_times) * 100, 2) if tier2_times else 0.0,
        "tier3_success_rate": round(tier3_success / len(tier3_times) * 100, 2) if tier3_times else 0.0,
        "avg_tier1_time_ms": round(sum(tier1_times) / len(tier1_times), 2) if tier1_times else 0.0,
        "avg_tier2_time_ms": round(sum(tier2_times) / len(tier2_times), 2) if tier2_times else 0.0,
        "avg_tier3_time_ms": round(sum(tier3_times) / len(tier3_times), 2) if tier3_times else 0.0
    }


def get_strategy_effectiveness_stats(
    db: Session,
    user_id: Optional[int] = None
) -> list:
    """
    Get effectiveness statistics for each strategy.
    
    Args:
        db: Database session
        user_id: Optional user ID to filter by
        
    Returns:
        List of strategy effectiveness statistics
    """
    query = db.query(TierExecutionLog)
    
    # Apply user filter if provided
    if user_id:
        from app.models.test_execution import TestExecution
        query = query.join(TestExecution).filter(TestExecution.user_id == user_id)
    
    logs = query.all()
    
    if not logs:
        return []
    
    # Group by strategy
    strategies = {}
    
    for log in logs:
        strategy = log.fallback_strategy
        
        if strategy not in strategies:
            strategies[strategy] = {
                "total": 0,
                "success": 0,
                "tier1": 0,
                "tier2": 0,
                "tier3": 0,
                "times": []
            }
        
        strategies[strategy]["total"] += 1
        
        if log.success:
            strategies[strategy]["success"] += 1
        
        if log.final_tier == 1:
            strategies[strategy]["tier1"] += 1
        elif log.final_tier == 2:
            strategies[strategy]["tier2"] += 1
        elif log.final_tier == 3:
            strategies[strategy]["tier3"] += 1
        
        strategies[strategy]["times"].append(log.total_execution_time_ms)
    
    # Calculate statistics
    results = []
    
    for strategy, data in strategies.items():
        total = data["total"]
        success = data["success"]
        
        results.append({
            "strategy": strategy,
            "total_executions": total,
            "successful_executions": success,
            "failed_executions": total - success,
            "success_rate": round(success / total * 100, 2) if total > 0 else 0.0,
            "avg_execution_time_ms": round(sum(data["times"]) / len(data["times"]), 2) if data["times"] else 0.0,
            "tier1_percentage": round(data["tier1"] / total * 100, 2) if total > 0 else 0.0,
            "tier2_percentage": round(data["tier2"] / total * 100, 2) if total > 0 else 0.0,
            "tier3_percentage": round(data["tier3"] / total * 100, 2) if total > 0 else 0.0,
            "cost_estimate": _estimate_cost(data["tier1"], data["tier2"], data["tier3"], total)
        })
    
    return results


def _estimate_cost(tier1_count: int, tier2_count: int, tier3_count: int, total: int) -> str:
    """
    Estimate cost level based on tier distribution.
    
    Args:
        tier1_count: Number of Tier 1 executions
        tier2_count: Number of Tier 2 executions
        tier3_count: Number of Tier 3 executions
        total: Total executions
        
    Returns:
        Cost estimate: "low", "medium", or "high"
    """
    if total == 0:
        return "unknown"
    
    tier3_percentage = tier3_count / total * 100
    tier2_percentage = tier2_count / total * 100
    
    if tier3_percentage > 20:
        return "high"
    elif tier2_percentage > 30 or tier3_percentage > 10:
        return "medium"
    else:
        return "low"
