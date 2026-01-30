"""MinIO storage integration with local filesystem fallback"""
from minio import Minio
from minio.error import S3Error
from app.core.config import settings
import io
import os
from pathlib import Path
from typing import Optional

class LocalStorageService:
    """Local filesystem storage service for dev (no MinIO required)"""
    def __init__(self, base_path: Optional[str] = None):
        if base_path is None:
            base_path = os.getenv("STORAGE_PATH")
        if base_path is None:
            project_root = Path(__file__).parent.parent.parent
            base_path = str(project_root / "backend" / "uploads")
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.available = True
    
    def upload_file(self, file_data: bytes, file_key: str, content_type: str) -> str:
        """
        Upload a file to local filesystem.
        Creates directory structure if missing.
        Returns file_key (same as input).
        """
        # Sanitize file_key to prevent directory traversal
        safe_key = file_key.replace("..", "").replace("\\", "/")
        # Split into folder and filename
        parts = safe_key.split("/")
        folder = "/".join(parts[:-1]) if len(parts) > 1 else ""
        filename = parts[-1]
        
        # Create folder directory if needed
        if folder:
            folder_path = self.base_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            file_path = folder_path / filename
        else:
            file_path = self.base_path / filename
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return file_key
    
    def get_file_path(self, file_key: str) -> str:
        """Return absolute path for the saved file"""
        safe_key = file_key.replace("..", "").replace("\\", "/")
        parts = safe_key.split("/")
        if len(parts) > 1:
            folder = "/".join(parts[:-1])
            filename = parts[-1]
            file_path = self.base_path / folder / filename
        else:
            file_path = self.base_path / safe_key
        return str(file_path.absolute())
    
    def get_public_url(self, file_key: str) -> str:
        """Return public URL for the file (API endpoint path)"""
        return f"/api/v1/files/{file_key}"
    
    def open_file(self, file_key: str):
        """Open the local file for streaming (returns file-like object)"""
        file_path = self.get_file_path(file_key)
        return open(file_path, 'rb')
    
    def file_exists(self, file_key: str) -> bool:
        """Check if a file exists"""
        file_path = Path(self.get_file_path(file_key))
        return file_path.exists()
    
    def get_file(self, file_key: str) -> bytes:
        """Download a file from local filesystem"""
        file_path = Path(self.get_file_path(file_key))
        
        if not file_path.exists():
            raise Exception(f"File not found: {file_key}")
        
        with open(file_path, 'rb') as f:
            return f.read()
    
    def delete_file(self, file_key: str):
        """Delete a file from local filesystem"""
        file_path = Path(self.get_file_path(file_key))
        
        if file_path.exists():
            file_path.unlink()
    
    def get_file_url(self, file_key: str, expires_seconds: int = 3600) -> str:
        """Get a URL for a file (returns API endpoint path)"""
        return self.get_public_url(file_key)

class StorageService:
    def __init__(self):
        self.available = False
        self.bucket = settings.MINIO_BUCKET
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=False  # Set to True if using HTTPS
            )
            self._ensure_bucket()
            self.available = True
        except Exception as e:
            print(f"Warning: MinIO not available: {e}")
            print("File storage will be disabled. Start MinIO to enable file uploads.")
            self.client = None
    
    def _ensure_bucket(self):
        """Ensure the bucket exists"""
        if not hasattr(self, 'client') or self.client is None:
            return
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as e:
            print(f"Warning: Could not ensure bucket exists: {e}")
            self.available = False
    
    def upload_file(self, file_data: bytes, file_key: str, content_type: str) -> str:
        """Upload a file to MinIO and return the file key"""
        if not self.available:
            raise Exception("MinIO is not available. Please start MinIO server.")
        try:
            file_stream = io.BytesIO(file_data)
            self.client.put_object(
                self.bucket,
                file_key,
                file_stream,
                length=len(file_data),
                content_type=content_type
            )
            return file_key
        except Exception as e:
            raise Exception(f"Failed to upload file: {e}")
    
    def file_exists(self, file_key: str) -> bool:
        """Check if a file exists in MinIO"""
        if not self.available:
            return False
        try:
            self.client.stat_object(self.bucket, file_key)
            return True
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            raise
        except Exception:
            return False
    
    def get_file(self, file_key: str) -> bytes:
        """Download a file from MinIO"""
        if not self.available:
            raise Exception("MinIO is not available. Please start MinIO server.")
        try:
            response = self.client.get_object(self.bucket, file_key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            raise Exception(f"Failed to get file: {e}")
    
    def delete_file(self, file_key: str):
        """Delete a file from MinIO"""
        if not self.available:
            return
        try:
            self.client.remove_object(self.bucket, file_key)
        except Exception as e:
            raise Exception(f"Failed to delete file: {e}")
    
    def get_file_url(self, file_key: str, expires_seconds: int = 3600) -> str:
        """Get a presigned URL for a file"""
        if not self.available:
            raise Exception("MinIO is not available. Please start MinIO server.")
        try:
            return self.client.presigned_get_object(
                self.bucket,
                file_key,
                expires=expires_seconds
            )
        except Exception as e:
            raise Exception(f"Failed to generate URL: {e}")

# Initialize storage service based on USE_MINIO config
_storage_service = None

def get_storage_service():
    """Get storage service based on USE_MINIO config flag"""
    global _storage_service
    if _storage_service is None:
        if settings.USE_MINIO:
            # Try to initialize MinIO
            try:
                _storage_service = StorageService()
                if not _storage_service.available:
                    print("WARNING: USE_MINIO=True but MinIO connection failed, falling back to local storage")
                    _storage_service = LocalStorageService()
                else:
                    print("Using MinIO storage")
            except Exception as e:
                print(f"WARNING: Failed to initialize MinIO ({e}), falling back to local storage")
                _storage_service = LocalStorageService()
        else:
            print("Using local filesystem storage (USE_MINIO=False)")
            _storage_service = LocalStorageService(base_path=os.getenv("STORAGE_PATH"))
    return _storage_service

storage_service = get_storage_service()

