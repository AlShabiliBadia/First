from typing import Optional, Annotated
from pydantic import BaseModel, Field, EmailStr, ConfigDict, model_validator


class SignUp(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=100, examples=["John Doe"])]
    email: Annotated[EmailStr, Field(examples=["john@example.com"])]
    password: Annotated[str, Field(min_length=8, max_length=72, examples=["SecureP@ss123"])]
    password_confirmation: Annotated[str, Field(examples=["SecureP@ss123"])]
    turnstile_token: Annotated[Optional[str], Field(default=None, examples=["0.ABC123..."])]

    @model_validator(mode="after")
    def passwords_must_match(self):
        if self.password != self.password_confirmation:
            raise ValueError("Password and confirmation do not match")
        return self
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "password": "SecureP@ss123",
                "password_confirmation": "SecureP@ss123",
                "turnstile_token": "0.ABC123..."
            }
        }
    )


class Login(BaseModel):
    email: Annotated[EmailStr, Field(examples=["john@example.com"])]
    password: Annotated[str, Field(examples=["SecureP@ss123"])]
    turnstile_token: Annotated[Optional[str], Field(default=None, examples=["0.ABC123..."])]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john@example.com",
                "password": "SecureP@ss123"
            }
        }
    )


class Token(BaseModel):
    access_token: Annotated[str, Field(examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])]
    token_type: Annotated[str, Field(default="bearer", examples=["bearer"])]


class TokenPair(BaseModel):
    access_token: Annotated[str, Field(examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])]
    refresh_token: Annotated[str, Field(examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])]
    token_type: Annotated[str, Field(default="bearer", examples=["bearer"])]


class RefreshRequest(BaseModel):
    refresh_token: Annotated[str, Field(examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )
