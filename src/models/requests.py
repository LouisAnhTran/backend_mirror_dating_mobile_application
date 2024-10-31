
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

class UserSignUpRequest(BaseModel):
    username: str=Field(example="louis_anh_tran")
    email: str=Field(example="namanhtrancong@gmail.com")
    password: str=Field(example="12345678")

class OTPRequest(BaseModel):
    phone_number: str=Field(example="+6597755168")

class OTPVerification(BaseModel):
    phone_number: str=Field(example="+6597755168")
    otp: str=Field(example="696969")

class UserOnboardingRequest(BaseModel):
    username: str=Field(
        example="Louis Anh Tran")
    email_address: str=Field(
        example="namanhtrancong@gmail.com")
    industry: str=Field(
        example="Information Technology"
    )

class UserSignInRequest(BaseModel):
    username: str=Field(example="louis_anh_tran")
    password: str=Field(example="12345678")

class FetchChatMessagesRequest(BaseModel):
    filename: str=Field(
        example="e_casptone_doc.pdf"
    )

class SingleChatMessageRequest(BaseModel):
    role:  str=Field(
        example="user"
    )
    content: str=Field(
        example="Tell me the overview of this document"
    )
    timestamp: datetime = Field(
        example="2023-07-17T12:34:56"
    )

class ChatMessagesRequest(BaseModel):
    list_of_messages: List[SingleChatMessageRequest] = Field(
        example=[
            {
                "role": "user",
                "content": "Tell me the overview of this document",
                "timestamp": "2023-07-17T12:34:56"
            },
            {
                "role": "system",
                "content": "The document is about is Programming language concept and compiler design",
                "timestamp": "2023-07-17T12:35:10"
            },
             {
                "role": "user",
                "content": "What is the compiler relationship to Programming language concept",
                "timestamp": "2023-07-17T12:35:15"
            }
        ]
    )