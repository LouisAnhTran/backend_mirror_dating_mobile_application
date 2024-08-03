from dotenv import load_dotenv
import os
import secrets
import json

from src.utils.env_variable import convert_str_to_bool

load_dotenv()

print("HELLO_WORLD")

for k,v in os.environ.items():
    print(f"env {k}: {v}")

PORT=int(os.getenv("PORT_PROD")) if not convert_str_to_bool(os.getenv("LOCAL")) else int(os.getenv("PORT_DEV"))
DATABASE_URL=os.getenv("DATABASE_URL")

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
AWS_ACCESS_KEY=os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME_DEV=os.getenv("AWS_BUCKET_NAME_DEV")
AWS_REGION_TEST=os.getenv("AWS_REGION_TEST")

# Consider using dest in future
OPENAI_CREDENTIAL_PATH = "credentials/gpt-4-secrets.json"
with open(OPENAI_CREDENTIAL_PATH) as f:
    OPENAI_CREDENTIALS = json.load(f)
    print("openai_credentials: ",OPENAI_CREDENTIALS)