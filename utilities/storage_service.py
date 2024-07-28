import boto3
import base64
import mimetypes
from PIL import Image
from io import BytesIO
from typing import Optional
from fastapi import HTTPException
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

from solidus.config import config


class StorageService:
    def __init__(self):
        self.aws_access_key_id = config.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = config.get('AWS_SECRET_ACCESS_KEY')
        self.aws_region_name = config.get('AWS_REGION_NAME')
        self.aws_storage_bucket_name = config.get('AWS_STORAGE_BUCKET_NAME')

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region_name
        )

    def upload_image(self, image_base64: str, image_name: str, folder: Optional[str] = 'uploaded_images/') -> str:
        """
        Uploads an image to an S3 bucket and returns the URL of the uploaded image.

        :param image_base64: The base64-encoded image string to be uploaded.
        :param image_name: The name of the image file.
        :param folder: The folder in the S3 bucket where the image will be stored.
        :return: The URL of the uploaded image.
        """
        try:
            # Decode the base64 string
            image_data = base64.b64decode(image_base64)

            # Determine content type
            content_type, _ = mimetypes.guess_type(image_name)
            if content_type is None or not content_type.startswith("image/"):
                raise ValueError("File type not supported. Please upload an image.")

            # Define the S3 file path
            s3_file_path = folder + image_name
            
            # Upload the image to S3
            self.s3_client.upload_fileobj(
                BytesIO(image_data),
                self.aws_storage_bucket_name,
                s3_file_path,
                ExtraArgs={'ContentType': content_type}
            )
            
            # Generate the file URL
            file_url = f"https://{self.aws_storage_bucket_name}.s3.amazonaws.com/{s3_file_path}"
            return file_url
        
        except (NoCredentialsError, PartialCredentialsError) as e:
            raise HTTPException(status_code=500, detail=f"Credentials error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
