"""File upload service for Knowledge Base documents."""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from app.models.kb_document import FileType


class FileUploadService:
    """Service for handling file uploads."""
    
    def __init__(self):
        self.upload_dir = Path("uploads/kb")
        self.max_size = 10 * 1024 * 1024  # 10MB
        self.allowed_types = {
            "application/pdf": FileType.PDF,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCX,
            "text/plain": FileType.TXT,
            "text/markdown": FileType.MD,
        }
        self.allowed_extensions = {".pdf", ".docx", ".txt", ".md"}
        
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_file(self, file: UploadFile) -> Tuple[str, FileType, int]:
        """
        Save uploaded file to disk.
        
        Args:
            file: Uploaded file
            
        Returns:
            Tuple of (file_path, file_type, file_size)
            
        Raises:
            HTTPException: If file validation fails
        """
        # Validate file
        file_type, file_size = await self._validate_file(file)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.upload_dir / unique_filename
        
        # Save file
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        
        return str(file_path), file_type, file_size
    
    async def extract_text(self, file_path: str, file_type: FileType) -> Optional[str]:
        """
        Extract text content from uploaded file.
        
        Args:
            file_path: Path to the file
            file_type: Type of file
            
        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            if file_type == FileType.TXT or file_type == FileType.MD:
                return await self._extract_text_from_txt(file_path)
            elif file_type == FileType.PDF:
                return await self._extract_text_from_pdf(file_path)
            elif file_type == FileType.DOCX:
                return await self._extract_text_from_docx(file_path)
            return None
        except Exception as e:
            # Log error but don't fail - content extraction is optional
            print(f"Warning: Text extraction failed for {file_path}: {str(e)}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from disk.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Warning: Failed to delete file {file_path}: {str(e)}")
            return False
    
    # Private methods
    
    async def _validate_file(self, file: UploadFile) -> Tuple[FileType, int]:
        """Validate uploaded file."""
        # Check filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            )
        
        # Read file content for validation
        content = await file.read()
        file_size = len(content)
        
        # Reset file position
        await file.seek(0)
        
        # Check file size
        if file_size > self.max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {self.max_size / (1024*1024):.1f}MB"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Determine file type from extension (more reliable than MIME type)
        file_type_map = {
            ".pdf": FileType.PDF,
            ".docx": FileType.DOCX,
            ".txt": FileType.TXT,
            ".md": FileType.MD,
        }
        
        file_type = file_type_map.get(file_extension)
        if not file_type:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        return file_type, file_size
    
    async def _extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT/MD file."""
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
            return content.strip()
    
    async def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            from PyPDF2 import PdfReader
            
            # PDF extraction is synchronous
            reader = PdfReader(file_path)
            text_parts = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n\n".join(text_parts).strip()
        except Exception as e:
            print(f"PDF extraction error: {str(e)}")
            return ""
    
    async def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            from docx import Document
            
            # DOCX extraction is synchronous
            doc = Document(file_path)
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            return "\n\n".join(text_parts).strip()
        except Exception as e:
            print(f"DOCX extraction error: {str(e)}")
            return ""

