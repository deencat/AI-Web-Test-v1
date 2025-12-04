#!/usr/bin/env python3
"""
Import orphaned KB files into the database.

This script finds markdown files in uploads/kb/ that don't have
corresponding database records and imports them.
"""

import sys
from pathlib import Path
from datetime import datetime
import PyPDF2

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models.kb_document import KBDocument, KBCategory

def import_orphaned_files():
    """Import orphaned files from uploads/kb/ into the database."""
    
    db = SessionLocal()
    
    try:
        # Get the upload directory
        upload_dir = Path("uploads/kb")
        
        if not upload_dir.exists():
            print(f"[ERROR] Upload directory not found: {upload_dir}")
            return
        
        # Find all supported files (pdf, docx, txt, md)
        supported_files = []
        for ext in ['*.pdf', '*.docx', '*.txt', '*.md']:
            supported_files.extend(upload_dir.glob(ext))
        
        if not supported_files:
            print("[INFO] No supported files found in uploads/kb/")
            return
        
        print(f"[INFO] Found {len(supported_files)} files")
        
        # Get existing file paths from database to avoid duplicates
        existing_paths = {doc.file_path for doc in db.query(KBDocument).all()}
        print(f"[INFO] {len(existing_paths)} files already in database")
        
        # Get a default category (Test Cases seems appropriate based on content)
        test_category = db.query(KBCategory).filter(
            KBCategory.name == "Test Cases"
        ).first()
        
        if not test_category:
            # Fallback to any category
            test_category = db.query(KBCategory).first()
        
        if not test_category:
            print("[ERROR] No categories found in database. Please create categories first.")
            return
        
        print(f"[INFO] Using category: {test_category.name}")
        
        # Import each file
        imported = 0
        skipped = 0
        
        for file_path in supported_files:
            # Check if already in database
            # Use path relative to backend directory or just uploads/kb/filename
            rel_path = f"uploads/kb/{file_path.name}"
            
            if rel_path in existing_paths:
                print(f"  [SKIP] {file_path.name} - already in database")
                skipped += 1
                continue
            
            # Get file type from extension
            file_ext = file_path.suffix.lower().lstrip('.')
            
            # Read file content and metadata
            file_size = file_path.stat().st_size
            
            # For text-based files, read content
            content = None
            if file_ext in ['txt', 'md']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        first_line = content.split('\n')[0] if content else ""
                        # Extract title from markdown header (remove # and whitespace)
                        title = first_line.replace('#', '').strip() if first_line.startswith('#') else file_path.stem
                except Exception as e:
                    print(f"  [WARN] Could not read {file_path.name}: {e}")
                    title = file_path.stem
                    content = None
            elif file_ext == 'pdf':
                # Extract text from PDF
                try:
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        text_parts = []
                        for page in pdf_reader.pages:
                            text_parts.append(page.extract_text())
                        content = '\n\n'.join(text_parts)
                        title = file_path.stem
                        print(f"  [PDF] Extracted {len(content)} characters from {file_path.name}")
                except Exception as e:
                    print(f"  [WARN] Could not extract text from PDF {file_path.name}: {e}")
                    title = file_path.stem
                    content = None
            else:
                # For other file types (DOCX), just use filename as title
                title = file_path.stem
                content = None
            
            # Create database record
            kb_doc = KBDocument(
                title=title,
                description=f"Imported from {file_path.name}",
                filename=file_path.name,
                file_path=rel_path,
                file_type=file_ext,
                file_size=file_size,
                category_id=test_category.id,
                user_id=1,  # Admin user
                content=content,  # Store FULL content for text files, None for binary
                referenced_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(kb_doc)
            print(f"  [+] {file_path.name} - '{title}' ({file_size} bytes)")
            imported += 1
        
        # Commit all changes
        db.commit()
        
        print(f"\n[SUCCESS] Import complete!")
        print(f"  Imported: {imported}")
        print(f"  Skipped: {skipped}")
        print(f"  Total in database: {db.query(KBDocument).count()}")
        
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_orphaned_files()
