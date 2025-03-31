import boto3
from botocore.exceptions import ClientError
import json
from io import BytesIO
import base64

class S3Handler:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.s3_client = None

    def connect(self):
        try:
            self.s3_client = boto3.client('s3', 
                                          aws_access_key_id=self.aws_access_key_id,
                                          aws_secret_access_key=self.aws_secret_access_key,
                                          region_name=self.region_name)
            print("Connected to S3 successfully!")
        except ClientError as e:
            print(f"Failed to connect to S3: {e}")

    def disconnect(self):
        self.s3_client = None
        print("Disconnected from S3.")

    def upload_file(self, file_path, bucket_name, object_name):
        try:
            self.s3_client.upload_file(file_path, bucket_name, object_name)
            print(f"Uploaded {file_path} to S3 bucket {bucket_name} with key {object_name}")
            s3_path = "s3://{bucket_name}/{object_name}"
            return s3_path
        except ClientError as e:
            print(f"Failed to upload file to S3: {e}")

    def upload_file_object(self, file, bucket_name, object_name):
        try:
            import io
            contents = file.file.read()
            temp_file = io.BytesIO()
            temp_file.write(contents)
            temp_file.seek(0)
            self.s3_client.upload_fileobj(temp_file, bucket_name, object_name)
            # self.s3_client.upload_fileobj(file.file, bucket_name, object_name)
            print(f"Uploaded {file.filename} to S3 bucket {bucket_name} with key {object_name}")
            s3_path = f"s3://{bucket_name}/{object_name}"
            return s3_path
        except ClientError as e:
            print(f"Failed to upload file to S3: {e}")

    def upload_image(self, image_bytes, bucket_name, object_name):
        try:
            # Upload the image bytes to S3
            self.s3_client.put_object(Body=image_bytes, Bucket=bucket_name, Key=object_name)
            s3_path = f"s3://{bucket_name}/{object_name}"
            print(f"Uploaded image to S3: {s3_path}")
            return s3_path
        except ClientError as e:
            print(f"Failed to upload image to S3: {e}")

    def download_file(self, bucket_name, object_name, file_path):
        try:
            self.s3_client.download_file(bucket_name, object_name, file_path)
            print(f"Downloaded object {object_name} from S3 bucket {bucket_name} to {file_path}")
        except ClientError as e:
            print(f"Failed to download file from S3: {e}")

    def list_objects(self, bucket_name):
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            objects = response.get('Contents', [])
            return [obj['Key'] for obj in objects]
        except ClientError as e:
            print(f"Failed to list objects in S3 bucket: {e}")
            return []

    def delete_object(self, bucket_name, object_name):
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_name)
            print(f"Deleted object {object_name} from S3 bucket {bucket_name}")
        except ClientError as e:
            print(f"Failed to delete object from S3: {e}")

    def load_image(self, s3_path):
        try:
            response = self.s3_client.get_object(Bucket=s3_path.split('/')[2], Key='/'.join(s3_path.split('/')[3:]))
            return response['Body'].read()
        except ClientError as e:
            print(f"Failed to load image from S3: {e}")
            return None
        
    def parse_s3_path(self, s3_path):
        # Remove 's3://' prefix and split into bucket name and object key
        parts = s3_path[len('s3://'):].split('/', 1)
        bucket_name = parts[0]
        object_key = parts[1] if len(parts) > 1 else ''
        return bucket_name, object_key
    
    def store_results(self, request_id, s3_path, analysis_results):
        try:
            bucket_name = 'your-results-bucket'
            object_name = f"{request_id}.json"
            self.s3_client.put_object(Body=json.dumps(analysis_results), Bucket=bucket_name, Key=object_name)
            print(f"Stored analysis results for request ID {request_id} in S3 bucket {bucket_name} with key {object_name}")
        except ClientError as e:
            print(f"Failed to store analysis results in S3: {e}")

    def list_buckets(self):
        """List all buckets available in the AWS account"""
        try:
            response = self.s3_client.list_buckets()
            buckets = response.get('Buckets', [])
            bucket_names = [bucket['Name'] for bucket in buckets]
            print("Available buckets:")
            for bucket_name in bucket_names:
                print(bucket_name)
            return bucket_names
        except ClientError as e:
            print(f"Failed to list buckets: {e}")
            return []
        

    def create_bucket(self, bucket_name, region=None):
        """Create a new S3 bucket"""
        try:
            if region is None:
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region})
            print(f"Bucket '{bucket_name}' created successfully")
        except ClientError as e:
            print(f"Failed to create bucket: {e}")


    def list_all_objects(self, s3_uri):
        bucket_name, prefix = self.parse_s3_path(s3_uri)
        
        def list_objects_recursively(bucket_name, prefix):
            objects = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
                for obj in page.get('Contents', []):
                    objects.append(obj['Key'])
            return objects

        try:
            all_objects = list_objects_recursively(bucket_name, prefix)
            s3_uris = [f"s3://{bucket_name}/{obj}" for obj in all_objects]
            print(f"All objects in {s3_uri}:")
            for uri in s3_uris:
                print(uri)
            return s3_uris
        except ClientError as e:
            print(f"Failed to list all objects in {s3_uri}: {e}")
            return []
        
    def move_file_within_buckets(self, source_s3_uri, destination_s3_uri):
        try:
            # Parse the source and destination S3 URIs
            source_bucket, source_key = self.parse_s3_path(source_s3_uri)
            destination_bucket, destination_key = self.parse_s3_path(destination_s3_uri)

            # Copy the object to the new location
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            self.s3_client.copy(copy_source, destination_bucket, destination_key)
            print(f"Copied {source_s3_uri} to {destination_s3_uri}")

            # Delete the original object
            self.s3_client.delete_object(Bucket=source_bucket, Key=source_key)
            print(f"Deleted {source_s3_uri}")

        except ClientError as e:
            print(f"Failed to move file from {source_s3_uri} to {destination_s3_uri}: {e}")

    def read_file(self,bucket_name,file_key):
        response = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response['Body'].read()
        file_like_object = BytesIO(file_content)
        return file_like_object
    
    def read_image(self,bucket_name,file_key):
        response = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response['Body'].read()
        base64_image = base64.b64encode(file_content).decode('utf-8')
        return base64_image
    
    def extract_s3_details(s3_path):
        # Remove the "s3://" prefix
        if s3_path.startswith("s3://"):
            s3_path = s3_path[5:]
        
        # Split the path into bucket name and object key
        bucket_name, object_key = s3_path.split('/', 1)
        
        return bucket_name, object_key

    def create_presigned_url(self,bucket_name, object_name, expiration=10):

        # Generate a presigned URL for the S3 object
        #s3_client = boto3.client('s3')
        try:
            response = self.s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': bucket_name,
                                                                'Key': object_name,
                                                                'ResponseContentDisposition': 'inline',
                                                                'ResponseContentType': 'image/png'},
                                                        ExpiresIn=expiration)
        except ClientError as e:
            #logging.error(e)
            print(e)
            return None

        # The response contains the presigned URL
        return response
    
    def create_presigned_url_audio(self,bucket_name, object_name, expiration=10):

        # Generate a presigned URL for the S3 object
        #s3_client = boto3.client('s3')
        try:
            response = self.s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': bucket_name,
                                                                'Key': object_name,
                                                                'ResponseContentDisposition': 'inline',
                                                                'ResponseContentType': 'audio/wav'},
                                                        ExpiresIn=expiration)
        except ClientError as e:
            #logging.error(e)
            print(e)
            return None

        # The response contains the presigned URL
        return response
# Now, file_content holds the content of the file from S3
# You can further process or manipulate this content as needed
        
    def create_presigned_url_upload(self,bucket_name, object_name, expiration=10):

        # Generate a presigned URL for the S3 object
        #s3_client = boto3.client('s3')
        try:
            response = self.s3_client.generate_presigned_url('put_object',
                                                        Params={'Bucket': bucket_name,
                                                                'Key': object_name,
                                                                'ContentType': 'application/pdf'},
                                                                # 'ResponseContentDisposition': 'inline',
                                                                # 'ResponseContentType': 'application/pdf'},
                                                        ExpiresIn=expiration)
        except ClientError as e:
            #logging.error(e)
            print(e)
            return None

        # The response contains the presigned URL
        return response
    
    def get_s3_files_details(self,s3_paths):
        # Initialize the S3 client
        
        file_details_list = []

        for s3_path_og in s3_paths:
            # Parse the s3 path
            if not s3_path_og.startswith("s3://"):
                raise ValueError(f"Invalid S3 path: {s3_path}. Path must start with 's3://'")

            # Remove the 's3://' prefix
            s3_path = s3_path_og[5:]

            # Split the path into bucket name and key
            bucket_name, key = s3_path.split('/', 1)

            # Get the file object
            file_obj = self.s3_client.get_object(Bucket=bucket_name, Key=key)
            
            # Get the file content
            file_content = file_obj['Body'].read()
            
            # Get the file size
            file_size = file_obj['ContentLength']
            
            # Get the file name from the key
            file_name = key.split('/')[-1]
            
            file_details = {
                'file_name': file_name,
                'file_size': file_size,
                'file_content': file_content,
                's3_path':s3_path_og
            }

            file_details_list.append(file_details)
        
        return file_details_list