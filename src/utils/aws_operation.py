import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi import HTTPException
from io import BytesIO
import logging

from src.config import AWS_BUCKET_NAME_DEV


def get_file(s3_client,doc_key):
    try:
        response = s3_client.list_objects_v2(Bucket=AWS_BUCKET_NAME_DEV, Prefix='louis_anh_tran/')
        
        for obj in response.get('Contents', []):
            print("object_aws: ",obj['Key'])

        # Download file from S3
        response = s3_client.get_object(
            Bucket=AWS_BUCKET_NAME_DEV,
            Key=doc_key
        )

        logging.info("response_from_s3: ",response)
        
        # Return the file content

        return BytesIO(response['Body'].read()),response['Body'].read()
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            raise HTTPException(status_code=404, detail=f"File '{doc_key}' not found in S3")
        else:
            raise HTTPException(status_code=500, detail=f"AWS S3 error: {error_code}")
    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
    
