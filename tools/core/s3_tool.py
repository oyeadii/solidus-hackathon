import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from fastapi import UploadFile, HTTPException
from io import BytesIO
from typing import Optional
from solidus.config import settings
from solidus.config import config


#Env credentials
AWS_ACCESS_KEY_ID = config.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION_NAME = config.get('AWS_REGION_NAME')
AWS_STORAGE_BUCKET_NAME = config.get('AWS_STORAGE_BUCKET_NAME')


s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION_NAME
)

def upload_image_to_s3(image: UploadFile, folder: Optional[str] = 'uploaded_images/') -> str:
    """
    Uploads an image to an S3 bucket and returns the URL of the uploaded image.

    :param image: The image file to be uploaded.
    :param folder: The folder in the S3 bucket where the image will be stored.
    :return: The URL of the uploaded image.
    """
    try:
        # Check if the uploaded file is an image
        if not image.content_type.startswith("image/"):
            raise ValueError("File type not supported. Please upload an image.")
        
        # Define the S3 file path
        s3_file_path = folder + image.filename
        
        # Upload the image to S3
        s3_client.upload_fileobj(
            image.file,
            AWS_STORAGE_BUCKET_NAME,
            s3_file_path,
            ExtraArgs={'ContentType': image.content_type}
        )
        
        # Generate the file URL
        file_url = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{s3_file_path}"
        return file_url
    
    except (NoCredentialsError, PartialCredentialsError) as e:
        raise HTTPException(status_code=500, detail=f"Credentials error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# if _name_ == "_main_":
#     example_image = UploadFile(filename="example.png", content_type="image/png", file=open("path_to_image.png", "rb"))
#     print(upload_image_to_s3(example_image))