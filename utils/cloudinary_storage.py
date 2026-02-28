"""
Cloudinary storage backend for Django.
Replaces DigitalOcean Spaces with Cloudinary for image hosting.
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import Storage
from django.conf import settings
import os
import uuid
from urllib.parse import urljoin


class CloudinaryStorage(Storage):
    """
    Django storage backend for Cloudinary.
    Handles image uploads, deletions, and URL generation.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configure Cloudinary from settings
        cloudinary.config(
            cloud_name=getattr(settings, 'CLOUDINARY_CLOUD_NAME', ''),
            api_key=getattr(settings, 'CLOUDINARY_API_KEY', ''),
            api_secret=getattr(settings, 'CLOUDINARY_API_SECRET', ''),
            secure=True
        )
    
    def _open(self, name, mode='rb'):
        """
        Cloudinary doesn't support direct file opening.
        This method returns None as files are accessed via URLs.
        """
        return None
    
    def _save(self, name, content):
        """
        Save file to Cloudinary.
        
        Args:
            name: Original filename
            content: File content (UploadedFile or file-like object)
            
        Returns:
            Cloudinary public_id (without folder prefix for storage)
        """
        # Reset file pointer to beginning
        if hasattr(content, 'seek'):
            content.seek(0)
        
        if isinstance(content, UploadedFile):
            file_content = content.read()
            content_type = getattr(content, 'content_type', None)
        else:
            file_content = content.read()
            content_type = None
        
        # Extract file extension for format detection
        file_ext = os.path.splitext(name)[1].lower().lstrip('.')
        format_mapping = {
            'jpg': 'jpg',
            'jpeg': 'jpg', 
            'png': 'png',
            'gif': 'gif',
            'webp': 'webp',
            'svg': 'svg'
        }
        
        # Generate unique public ID (without folder)
        public_id = self._generate_public_id(name)
        
        # Get folder from settings
        folder = getattr(settings, 'CLOUDINARY_FOLDER', 'media')
        
        # Upload to Cloudinary
        upload_options = {
            'public_id': public_id,
            'resource_type': 'image',
            'overwrite': False,
            'folder': folder,
            'use_filename': False,
            'unique_filename': False,
        }
        
        # Set format if detected
        if file_ext in format_mapping:
            upload_options['format'] = format_mapping[file_ext]
        
        # Add content type if available
        if content_type and '/' in content_type:
            detected_format = content_type.split('/')[-1]
            if detected_format in format_mapping.values():
                upload_options['format'] = detected_format
        
        try:
            result = cloudinary.uploader.upload(
                file_content,
                **upload_options
            )
            # Return the public_id with folder prefix for storage
            # This will be used for retrieval
            return f"{folder}/{public_id}"
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to upload {name} to Cloudinary: {str(e)}")
            raise Exception(f"Failed to upload {name} to Cloudinary: {str(e)}")
    
    def _generate_public_id(self, filename):
        """
        Generate a unique public ID for Cloudinary.
        Uses the existing upload helper functions from models.py.
        """
        # Import the upload functions from models
        from providers.models import sanitize_filename
        
        # Sanitize filename
        sanitized = sanitize_filename(filename)
        name_without_ext = os.path.splitext(sanitized)[0]
        
        # Generate unique ID
        unique_id = str(uuid.uuid4())[:8]
        return f"{name_without_ext}_{unique_id}"
    
    def delete(self, name):
        """
        Delete file from Cloudinary.
        Silently handles errors to prevent cascading failures.
        """
        if not name:
            return
        
        try:
            # Extract public ID from the name/path
            public_id = self._extract_public_id(name)
            if public_id:
                cloudinary.uploader.destroy(public_id, resource_type='image', invalidate=True)
        except cloudinary.exceptions.NotFound:
            # File doesn't exist, nothing to delete
            pass
        except Exception as e:
            # Log error but don't raise to prevent crashes
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to delete {name} from Cloudinary: {str(e)}")
    
    def _extract_public_id(self, name):
        """
        Extract Cloudinary public ID from the stored name.
        Handles both full paths and simple public IDs.
        """
        if not name:
            return None
        
        # Get folder from settings
        folder = getattr(settings, 'CLOUDINARY_FOLDER', 'media')
        
        # If name starts with folder, it's already in the correct format
        if name.startswith(f"{folder}/"):
            # Remove file extension if present
            return os.path.splitext(name)[0]
        
        # If name is a full Cloudinary URL, extract public_id
        if 'cloudinary.com' in name:
            # Extract public_id from URL
            # URL format: https://res.cloudinary.com/{cloud_name}/image/upload/v{version}/{folder}/{public_id}.{ext}
            parts = name.split('/')
            if len(parts) >= 2:
                # Get the last part (filename with extension)
                filename = parts[-1]
                # Remove extension
                public_id = os.path.splitext(filename)[0]
                # Check if folder is in the path
                if len(parts) >= 3 and parts[-2] == folder.split('/')[-1]:
                    return f"{folder}/{public_id}"
                return f"{folder}/{public_id}"
        
        # If name is just a filename or simple public_id
        # Remove file extension and add folder
        public_id = os.path.splitext(name)[0]
        
        # Check if it already contains folder structure
        if '/' in public_id and not public_id.startswith(folder):
            # It might be a subfolder structure, keep it
            return public_id
        elif public_id.startswith(folder):
            return public_id
        else:
            # Add folder prefix
            return f"{folder}/{public_id}"
    
    def exists(self, name):
        """
        Check if file exists in Cloudinary.
        """
        if not name:
            return False
        
        try:
            public_id = self._extract_public_id(name)
            if not public_id:
                return False
            
            # Try to get resource info
            cloudinary.api.resource(public_id, resource_type='image')
            return True
        except cloudinary.exceptions.NotFound:
            return False
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Error checking existence of {name}: {str(e)}")
            return False
    
    def url(self, name):
        """
        Get the public URL for a Cloudinary resource.
        Returns secure HTTPS URL with automatic format optimization.
        """
        if not name:
            return ''
        
        try:
            # Extract the public_id (includes folder)
            public_id = self._extract_public_id(name)
            if not public_id:
                return ''
            
            # Build URL with minimal transformations
            # Keep it simple to avoid 404 errors
            options = {
                'secure': True,
                'resource_type': 'image',
                'quality': 'auto:good',  # Automatic quality optimization
                'crop': 'limit',  # Don't enlarge, only shrink if needed
                'width': 2000,
                'height': 2000
            }
            
            # Generate URL using cloudinary.CloudinaryImage
            from cloudinary import CloudinaryImage
            cloudinary_image = CloudinaryImage(public_id)
            url = cloudinary_image.build_url(**options)
            
            return url
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to generate URL for {name}: {str(e)}")
            # Return empty string instead of raising exception
            return ''
    
    def get_available_name(self, name, max_length=None):
        """
        Generate a unique filename for Cloudinary upload.
        """
        return self._generate_public_id(name)
    
    def size(self, name):
        """
        Get file size from Cloudinary.
        """
        if not name:
            return 0
        
        try:
            public_id = self._extract_public_id(name)
            if not public_id:
                return 0
            
            resource = cloudinary.api.resource(public_id, resource_type='image')
            return resource.get('bytes', 0)
        except cloudinary.exceptions.NotFound:
            return 0
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Error getting size for {name}: {str(e)}")
            return 0


class CloudinaryMediaStorage(CloudinaryStorage):
    """
    Specialized Cloudinary storage for media files.
    Includes default transformations for optimization.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default transformations for media files
        self.default_transformations = {
            'quality': 'auto:good',
            'fetch_format': 'auto',
            'crop': 'limit',
            'width': 2000,
            'height': 2000
        }
    
    def url(self, name):
        """
        Get URL with default transformations for media files.
        """
        if not name:
            return ''
        
        try:
            public_id = self._extract_public_id(name)
            if not public_id:
                return ''
            
            # Apply default transformations (without fetch_format)
            options = {
                'secure': True,
                'resource_type': 'image',
                'quality': 'auto:good',
                'crop': 'limit',
                'width': 2000,
                'height': 2000
            }
            
            # Generate URL using cloudinary.CloudinaryImage
            from cloudinary import CloudinaryImage
            cloudinary_image = CloudinaryImage(public_id)
            url = cloudinary_image.build_url(**options)
            
            return url
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to generate media URL for {name}: {str(e)}")
            return ''


class CloudinaryThumbnailStorage(CloudinaryStorage):
    """
    Specialized Cloudinary storage for thumbnails.
    Applies thumbnail transformations.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Thumbnail transformations
        self.thumbnail_transformations = {
            'quality': 'auto:good',
            'fetch_format': 'auto',
            'crop': 'fill',
            'width': 300,
            'height': 300,
            'gravity': 'auto'
        }
    
    def url(self, name):
        """
        Get URL with thumbnail transformations.
        """
        if not name:
            return ''
        
        try:
            public_id = self._extract_public_id(name)
            if not public_id:
                return ''
            
            # Apply thumbnail transformations (without fetch_format)
            options = {
                'secure': True,
                'resource_type': 'image',
                'quality': 'auto:good',
                'crop': 'fill',
                'width': 300,
                'height': 300,
                'gravity': 'auto'
            }
            
            # Generate URL using cloudinary.CloudinaryImage
            from cloudinary import CloudinaryImage
            cloudinary_image = CloudinaryImage(public_id)
            url = cloudinary_image.build_url(**options)
            
            return url
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to generate thumbnail URL for {name}: {str(e)}")
            return ''
