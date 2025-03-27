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
AWS_REGION=os.getenv("AWS_REGION")
API_VERSION=os.getenv("API_VERSION")
TWILIO_ACCOUNT_SID=os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_PHONE_NUMBER=os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_AUTH_TOKEN=os.getenv("TWILIO_AUTH_TOKEN")
SAA_SERVICE_URL=os.getenv("SAA_SERVICE_URL")
DATABASE_URL=os.getenv("DATABASE_URL")
AWS_LAMBDA_FUNCTION_NAME="cupid_lambda_function_devtest"
secret_name = "all-ai-capstone"
AWS_ACCESS_KEY_MIRROR=os.getenv("AWS_ACCESS_KEY_MIRROR")
AWS_SECRET_ACCESS_KEY_MIRROR=os.getenv("AWS_SECRET_ACCESS_KEY_MIRROR")

# Create AWS Secrets Manager client
client = boto3.client(
    'secretsmanager',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
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
OPENAI_API_KEY=secret_dict['OPENAI_API_KEY']
PINECONE_API_KEY=secret_dict['PINECONE_API_KEY']
GPT4_OPENAI_API_KEY=secret_dict['GPT4_OPENAI_API_KEY']
GTP4_OPENAI_API_BASE=secret_dict['GTP4_OPENAI_API_BASE']

print("database url: ",DATABASE_URL)