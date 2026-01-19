"""
XPath Cache Service for Tier 2 (Hybrid Mode)
Caches extracted XPath selectors to avoid repeated LLM calls
Sprint 5.5: 3-Tier Execution Engine
"""
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.execution_settings import XPathCache as XPathCacheModel
from app.schemas.execution_settings import XPathCacheCreate, XPathCacheUpdate

logger = logging.getLogger(__name__)


class XPathCacheService:
    """
    Service for managing XPath cache for Tier 2 execution.
    
    Provides caching, validation, and self-healing capabilities for XPath selectors
    extracted via Stagehand observe().
    """
    
    def __init__(self, db: Session):
        """
        Initialize XPath cache service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.cache_ttl_hours = 168  # 7 days default TTL
    
    @staticmethod
    def generate_cache_key(page_url: str, instruction: str) -> str:
        """
        Generate a unique cache key from page URL and instruction.
        
        Args:
            page_url: URL of the page
            instruction: Natural language instruction for the element
            
        Returns:
            SHA256 hash of the URL and instruction
        """
        key_string = f"{page_url}::{instruction}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get_cached_xpath(
        self,
        page_url: str,
        instruction: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached XPath selector if available and valid.
        
        Args:
            page_url: URL of the page
            instruction: Natural language instruction for the element
            
        Returns:
            Dict with xpath and metadata if found and valid, None otherwise
        """
        cache_key = self.generate_cache_key(page_url, instruction)
        
        # Query cache
        cache_entry = self.db.query(XPathCacheModel).filter(
            and_(
                XPathCacheModel.cache_key == cache_key,
                XPathCacheModel.is_valid == True
            )
        ).first()
        
        if not cache_entry:
            logger.debug(f"[XPath Cache] ❌ Cache miss for key: {cache_key}")
            return None
        
        # Check if cache is stale
        if self._is_cache_stale(cache_entry):
            logger.info(f"[XPath Cache] ⏰ Cache stale for key: {cache_key}")
            return None
        
        # Increment hit count
        cache_entry.hit_count += 1
        self.db.commit()
        
        logger.info(
            f"[XPath Cache] ✅ Cache hit! Key: {cache_key}, "
            f"Hits: {cache_entry.hit_count}, XPath: {cache_entry.xpath}"
        )
        
        return {
            "xpath": cache_entry.xpath,
            "selector_type": cache_entry.selector_type,
            "hit_count": cache_entry.hit_count,
            "page_title": cache_entry.page_title,
            "element_text": cache_entry.element_text,
            "cache_age_hours": self._get_cache_age_hours(cache_entry)
        }
    
    def cache_xpath(
        self,
        page_url: str,
        instruction: str,
        xpath: str,
        extraction_time_ms: Optional[float] = None,
        page_title: Optional[str] = None,
        element_text: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> XPathCacheModel:
        """
        Cache an extracted XPath selector.
        
        Args:
            page_url: URL of the page
            instruction: Natural language instruction for the element
            xpath: Extracted XPath selector
            extraction_time_ms: Time taken to extract XPath (milliseconds)
            page_title: Title of the page
            element_text: Text content of the element
            extra_data: Additional data as dictionary
            
        Returns:
            Created XPathCacheModel instance
        """
        cache_key = self.generate_cache_key(page_url, instruction)
        
        # Check if entry already exists
        existing_entry = self.db.query(XPathCacheModel).filter(
            XPathCacheModel.cache_key == cache_key
        ).first()
        
        if existing_entry:
            # Update existing entry
            existing_entry.xpath = xpath
            existing_entry.extraction_time_ms = extraction_time_ms
            existing_entry.page_title = page_title
            existing_entry.element_text = element_text
            existing_entry.extra_data = json.dumps(extra_data) if extra_data else None
            existing_entry.is_valid = True
            existing_entry.validation_failures = 0
            existing_entry.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing_entry)
            
            logger.info(f"[XPath Cache] 🔄 Updated cache entry for key: {cache_key}")
            return existing_entry
        
        # Create new entry
        cache_entry = XPathCacheModel(
            page_url=page_url,
            instruction=instruction,
            cache_key=cache_key,
            xpath=xpath,
            selector_type="xpath",
            extraction_time_ms=extraction_time_ms,
            page_title=page_title,
            element_text=element_text,
            extra_data=json.dumps(extra_data) if extra_data else None,
            is_valid=True,
            validation_failures=0,
            hit_count=0
        )
        
        self.db.add(cache_entry)
        self.db.commit()
        self.db.refresh(cache_entry)
        
        logger.info(f"[XPath Cache] ✅ Created cache entry for key: {cache_key}")
        return cache_entry
    
    def invalidate_cache(
        self,
        page_url: str,
        instruction: str,
        error_message: Optional[str] = None
    ):
        """
        Invalidate a cache entry when validation fails.
        
        Args:
            page_url: URL of the page
            instruction: Natural language instruction for the element
            error_message: Optional error message for logging
        """
        cache_key = self.generate_cache_key(page_url, instruction)
        
        cache_entry = self.db.query(XPathCacheModel).filter(
            XPathCacheModel.cache_key == cache_key
        ).first()
        
        if cache_entry:
            cache_entry.validation_failures += 1
            cache_entry.last_validated = datetime.utcnow()
            
            # Invalidate if too many failures
            if cache_entry.validation_failures >= 3:
                cache_entry.is_valid = False
                logger.warning(
                    f"[XPath Cache] ❌ Invalidated cache entry after {cache_entry.validation_failures} "
                    f"failures: {cache_key}"
                )
            
            self.db.commit()
            
            if error_message:
                logger.info(f"[XPath Cache] ⚠️ Validation failed: {error_message}")
    
    def validate_and_update(
        self,
        page_url: str,
        instruction: str,
        is_valid: bool
    ):
        """
        Update cache entry validation status.
        
        Args:
            page_url: URL of the page
            instruction: Natural language instruction for the element
            is_valid: Whether the cached XPath is still valid
        """
        cache_key = self.generate_cache_key(page_url, instruction)
        
        cache_entry = self.db.query(XPathCacheModel).filter(
            XPathCacheModel.cache_key == cache_key
        ).first()
        
        if cache_entry:
            cache_entry.last_validated = datetime.utcnow()
            
            if is_valid:
                cache_entry.validation_failures = 0
                cache_entry.is_valid = True
                logger.debug(f"[XPath Cache] ✅ Validated cache entry: {cache_key}")
            else:
                cache_entry.validation_failures += 1
                if cache_entry.validation_failures >= 3:
                    cache_entry.is_valid = False
                    logger.warning(f"[XPath Cache] ❌ Invalidated cache entry: {cache_key}")
            
            self.db.commit()
    
    def clear_invalid_entries(self) -> int:
        """
        Clear all invalid cache entries.
        
        Returns:
            Number of entries deleted
        """
        deleted_count = self.db.query(XPathCacheModel).filter(
            XPathCacheModel.is_valid == False
        ).delete()
        
        self.db.commit()
        
        logger.info(f"[XPath Cache] 🧹 Cleared {deleted_count} invalid cache entries")
        return deleted_count
    
    def clear_stale_entries(self, max_age_hours: Optional[int] = None) -> int:
        """
        Clear cache entries older than max_age_hours.
        
        Args:
            max_age_hours: Maximum age in hours (default: self.cache_ttl_hours)
            
        Returns:
            Number of entries deleted
        """
        max_age = max_age_hours or self.cache_ttl_hours
        cutoff_date = datetime.utcnow() - timedelta(hours=max_age)
        
        deleted_count = self.db.query(XPathCacheModel).filter(
            XPathCacheModel.updated_at < cutoff_date
        ).delete()
        
        self.db.commit()
        
        logger.info(f"[XPath Cache] 🧹 Cleared {deleted_count} stale cache entries (older than {max_age}h)")
        return deleted_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_entries = self.db.query(XPathCacheModel).count()
        valid_entries = self.db.query(XPathCacheModel).filter(
            XPathCacheModel.is_valid == True
        ).count()
        invalid_entries = total_entries - valid_entries
        
        # Calculate total hits
        total_hits = self.db.query(
            XPathCacheModel.hit_count
        ).filter(XPathCacheModel.is_valid == True).all()
        total_hits_sum = sum(hit[0] for hit in total_hits)
        
        # Calculate average extraction time
        avg_extraction_time = self.db.query(
            XPathCacheModel.extraction_time_ms
        ).filter(
            and_(
                XPathCacheModel.is_valid == True,
                XPathCacheModel.extraction_time_ms != None
            )
        ).all()
        avg_extraction_ms = (
            sum(t[0] for t in avg_extraction_time) / len(avg_extraction_time)
            if avg_extraction_time else 0
        )
        
        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "invalid_entries": invalid_entries,
            "total_hits": total_hits_sum,
            "avg_extraction_time_ms": round(avg_extraction_ms, 2),
            "cache_hit_rate": round(total_hits_sum / max(total_entries, 1), 2)
        }
    
    def _is_cache_stale(self, cache_entry: XPathCacheModel) -> bool:
        """Check if cache entry is stale based on TTL"""
        age_hours = self._get_cache_age_hours(cache_entry)
        return age_hours > self.cache_ttl_hours
    
    def _get_cache_age_hours(self, cache_entry: XPathCacheModel) -> float:
        """Get cache entry age in hours"""
        age_delta = datetime.utcnow() - (cache_entry.updated_at or cache_entry.created_at)
        return age_delta.total_seconds() / 3600
