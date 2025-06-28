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

class ProfileSchema(Schema):
    name: str
    bio: str
    imageUrl: str
    skills: list[str] = None

class ProfileResponseSchema(Schema):
    id: int
    email: str
    role: str
    profile: ProfileSchema
