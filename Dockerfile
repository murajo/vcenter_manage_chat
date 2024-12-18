FROM python:3.12

# Replace these with your own OpenAi & vCenter Manage API details
# These are placeholders and should be overwritten in your environment setup
ENV OPENAI_API_KEY='<your-openai-api-key>'
ENV VCENTER_API_MANAGEE_URL='<your-vcenter-manage-api-url>'
ENV VERIFY_SSL='False' 

WORKDIR /app

COPY src/ ./src/
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./src/app.py"]