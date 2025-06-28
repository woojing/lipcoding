from ninja import Schema
from typing import Literal, Optional, List

class SignUpSchema(Schema):
    email: str
    password: str
    name: str
    role: str

class LoginSchema(Schema):
    email: str
    password: str

class TokenSchema(Schema):
    token: str

class BaseProfileSchema(Schema):
    name: str
    bio: str
    imageUrl: str

class MentorProfileSchema(BaseProfileSchema):
    skills: List[str]

class MenteeProfileSchema(BaseProfileSchema):
    pass

class ProfileResponseSchema(Schema):
    id: int
    email: str
    role: str
    profile: dict  # Union type을 사용하여 조건부로 다른 스키마 적용
