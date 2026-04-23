import cloudinary
import cloudinary.uploader
from app.core.config import settings

if settings.CLOUDINARY_CLOUD_NAME:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )

async def upload_image(file):
    """
    Upload an image to Cloudinary and return the secure URL.
    """
    if not settings.CLOUDINARY_CLOUD_NAME:
        # Fallback for development if keys are not set
        return "https://via.placeholder.com/500"

    upload_result = cloudinary.uploader.upload(file)
    return upload_result.get("secure_url")
