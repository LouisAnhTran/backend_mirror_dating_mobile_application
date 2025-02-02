from dotenv import load_dotenv
import os
import secrets
import boto3
from botocore.exceptions import ClientError
import json

load_dotenv()

LOCAL=bool(int(os.getenv("LOCAL","0")))
PORT=int(os.getenv("PORT"))
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES"))
AWS_ACCESS_KEY=os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME_DEV=os.getenv("AWS_BUCKET_NAME_DEV")
AWS_REGION=os.getenv("AWS_REGION_TEST")
PINECONE_INDEX_PDF=os.getenv("PINECONE_INDEX_PDF")
PINECONE_VECTOR_DIMENSION=os.getenv("PINECONE_VECTOR_DIMENSION")
PINECONE_INDEX_ALL_AI=os.getenv("PINECONE_INDEX_ALL_AI")
API_VERSION=os.getenv("API_VERSION")
TWILIO_ACCOUNT_SID=os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_PHONE_NUMBER=os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_AUTH_TOKEN=os.getenv("TWILIO_AUTH_TOKEN")

secret_name = "all-ai-capstone"
region_name = "ap-southeast-1"

# Create a Secrets Manager client
session = boto3.session.Session()
client = session.client(
    service_name='secretsmanager',
    region_name=region_name
)

try:
    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
except ClientError as e:
    # For a list of exceptions thrown, see
    # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    raise e

secret = get_secret_value_response['SecretString']

secret_dict=json.loads(secret)

# import secret from aws secret manager
DATABASE_URL=secret_dict['DATABASE_URL']
OPENAI_API_KEY=secret_dict['OPENAI_API_KEY']
PINECONE_API_KEY=secret_dict['PINECONE_API_KEY']
GPT4_OPENAI_API_KEY=secret_dict['GPT4_OPENAI_API_KEY']
GTP4_OPENAI_API_BASE=secret_dict['GTP4_OPENAI_API_BASE']

print("GPT4: ",GPT4_OPENAI_API_KEY)