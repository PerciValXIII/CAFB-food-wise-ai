# # Use an official Python runtime as a parent image
# FROM public.ecr.aws/lambda/python:latest

# # Copy the requirements file into the container at /app
# COPY requirements.txt .

# # Install any needed packages specified in requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the entire src directory into the container at /app/src
# COPY src/ ./src/

# # Run main.handler when the container launches
# CMD ["./src/main.handler"]

FROM public.ecr.aws/lambda/python:latest
# FROM python:3.11.7
# WORKDIR /api/
# COPY . .
RUN chmod -R 777 /var/task/
# Copy function code
COPY requirements.txt .
RUN python3 -m pip install --no-cache -r requirements.txt
# Copy function code
# COPY ./main.py .
# COPY ./src ./src
COPY . .
RUN pwd
 
# WORKDIR /
# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD ["main.handler"]