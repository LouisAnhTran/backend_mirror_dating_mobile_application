
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class UserSignUpRequest(BaseModel):
    username: str=Field(
        example="louis_anh_tran")
    phonenumber: str=Field(
        example="+6597755168")
    birthday: str=Field(
        example="07/01/1998"
    )
    password: str=Field(
        example="12345678"
    )
    firstname: str=Field(
        example="louis"
    )
    lastname: str=Field(
        example="tran"
    )
    email: str=Field(
        example="louisanhtran@gmail.com"
    )


class OTPRequest(BaseModel):
    phone_number: str=Field(example="+6597755168")

class SignInByEmail(BaseModel):
    email: str=Field(example="namanhtrancong@gmail.com")
    password: str=Field(example="12345678")

class OTPVerification(BaseModel):
    phone_number: str=Field(example="+6597755168")
    otp: str=Field(example="696969")

class UserOnboardingRequest(BaseModel):
    username: str=Field(
        example="louis_anh_tran")
    phonenumber: str=Field(
        example="+6597755168")
    birthday: str=Field(
        example="07/01/1998"
    )
    password: str=Field(
        example="12345678"
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
                "role": "system",
                "content": "That makes sense—sometimes those values just develop naturally as we navigate life. Do you feel like they influence how you unwind too, like in your hobbies or when you're just relaxing? I imagine finding peace might be pretty central to how you spend your free time",
                "timestamp": "2023-07-17T12:35:10"
            },
             {
                "role": "user",
                "content": "yeah it does! I'm most relaxed alone or at home, and a lot of my hobbies are solo activities like reading",
                "timestamp": "2023-07-17T12:35:15"
            },
            {
                "role": "system",
                "content": "That sounds really peaceful. What kind of books do you usually gravitate toward? Do you find certain genres or themes that resonate with your values, or is it more about unwinding with whatever catches your interest?",
                "timestamp": "2023-07-17T12:36:30"
            },
             {
                "role": "user",
                "content": "whatever catches my interest usually. I do read serious non-fiction books like sociology, but that isn't a very relaxing activity HAHAH. so to relax I read fiction, in which fantasy and YA fiction is my go-to",
                "timestamp": "2023-07-17T12:37:03"
            },
            {
                "role": "user",
                "content": "I love play football and liverpool is my favourite club",
                "timestamp": "2023-07-17T12:37:03"
            },
        ]
    )
    category_id: Optional[int] = Field(
        default=None,  # Make it optional by providing a default value
        example=1
    )
