import base64
import requests

from solidus.config import config    


class StorageService:
    def __init__(self):
        self.download_base_url = 'https://mkpl-user.dev.devsaitech.com/api/v1/ai-resource/presigned-download'
        self.upload_base_url = 'https://mkpl-user.dev.devsaitech.com/api/v1/ai-resource/presigned-upload'
        self.headers = {
            'accept': 'application/json',
            'x-publisher-key': config.get("PUBLISHER_KEY"),
            'Content-Type': 'application/json'
        }

    def generate_presigned_upload_url(self, file_name):
        data = {
            "s3Key": file_name
        }
        try:
            response = requests.post(self.upload_base_url, json=data, headers=self.headers)
            if response.status_code == 201:
                response_data = response.json()
                presigned_url = response_data['data']['presignedUrl']
                key = response_data['data']['key']
                return presigned_url, key
            else:
                print(f"Request failed. Status code: {response.status_code}")
                return None, None
        except Exception as e:
            print(f"An error occurred while generating the upload URL: {e}")
            return None, None

    def upload_image_from_base64(self, presigned_url, base64_string):
            try:
                file_data = base64.b64decode(base64_string)
                response = requests.put(presigned_url, data=file_data)

                if response.status_code == 200:
                    print("File uploaded successfully.")
                else:
                    print(f"Failed to upload file. Status code: {response.status_code}")
                    print(f"Response: {response.text}")
            except Exception as e:
                print(f"An error occurred while uploading the file: {e}")
    
    def generate_presigned_download_url(self, key):
        params = {
            's3Key': key,
        }
        try:
            response = requests.get(self.download_base_url, headers=self.headers, params=params)
            response_data = response.json()
            presigned_url = response_data.get('data', {}).get('url')
            return presigned_url
        except Exception as e:
            print(f"An error occurred while generating the download URL: {e}")
            return None