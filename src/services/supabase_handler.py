from supabase import create_client, Client
import os
import requests

class SupabaseHandler:
    def __init__(self, url: str, api_key: str, bucket_name: str):
        self.supabase: Client = create_client(url, api_key)
        self.bucket_name = bucket_name
    
    # Method to insert data into a specific table
    def insert_data(self, table_name: str, data: dict):
        response = self.supabase.table(table_name).insert(data).execute()
        if response.error:
            print(f"Error inserting data: {response.error}")
        else:
            print(f"Data inserted successfully: {response.data}")
        return response.data

    # Method to retrieve data from a specific table
    def fetch_data(self, table_name: str, conditions: dict = {}):
        query = self.supabase.table(table_name).select("*")
        for column, value in conditions.items():
            query = query.eq(column, value)
        response = query.execute()
        if response.error:
            print(f"Error fetching data: {response.error}")
        else:
            print(f"Data fetched successfully: {response.data}")
        return response.data

    # Method to update data in a specific table
    def update_data(self, table_name: str, conditions: dict, new_data: dict):
        query = self.supabase.table(table_name)
        for column, value in conditions.items():
            query = query.eq(column, value)
        response = query.update(new_data).execute()
        if response.error:
            print(f"Error updating data: {response.error}")
        else:
            print(f"Data updated successfully: {response.data}")
        return response.data

    # Method to delete data from a specific table
    def delete_data(self, table_name: str, conditions: dict):
        query = self.supabase.table(table_name)
        for column, value in conditions.items():
            query = query.eq(column, value)
        response = query.delete().execute()
        if response.error:
            print(f"Error deleting data: {response.error}")
        else:
            print(f"Data deleted successfully: {response.data}")
        return response.data

    # Method to upload a file to a Supabase bucket
    def upload_file(self, file_path: str, storage_key: str):
        with open(file_path, 'rb') as file_data:
            response = self.supabase.storage.from_(self.bucket_name).upload(storage_key, file_data)
            if response.get('error'):
                print(f"Error uploading file: {response['error']['message']}")
            else:
                print(f"File uploaded successfully: {response}")
            return response

    # Method to download a file from a Supabase bucket
    def download_file(self, storage_key: str, download_path: str):
        response = self.supabase.storage.from_(self.bucket_name).download(storage_key)
        if isinstance(response, requests.Response) and response.status_code == 200:
            with open(download_path, 'wb') as f:
                f.write(response.content)
            print(f"File downloaded successfully to {download_path}")
        else:
            print(f"Error downloading file: {response}")
        return download_path

    # Method to delete a file from a Supabase bucket
    def delete_file(self, storage_key: str):
        response = self.supabase.storage.from_(self.bucket_name).remove([storage_key])
        if response.get('error'):
            print(f"Error deleting file: {response['error']['message']}")
        else:
            print(f"File deleted successfully: {response}")
        return response

# # Example usage
# # Example usage
# if __name__ == "__main__":
#     url = "https://your-supabase-url.supabase.co"
#     api_key = "your-supabase-api-key"
#     bucket_name = "your-bucket-name"

#     handler = SupabaseHandler(url, api_key, bucket_name)
    
#     # Example: Insert data into the "hoardings" table
#     hoarding_data = {
#         "location": "MG Road",
#         "width": 35,
#         "height": 21,
#         "price": 600,
#         "availability_status": "Available"
#     }
#     handler.insert_data("hoardings", hoarding_data)
    
#     # Example: Upload a file to the bucket
#     handler.upload_file("path/to/your/file.png", "hoardings/file.png")
    
#     # Example: Download a file from the bucket
#     handler.download_file("hoardings/file.png", "path/to/save/file.png")
