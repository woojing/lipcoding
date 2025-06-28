from ninja import Schema
from typing import Literal

class SignUpSchema(Schema):
    email: str
    password: str
    name: str
    role: Literal['mentor', 'mentee']

class LoginSchema(Schema):
    email: str
    password: str

class TokenSchema(Schema):
    token: str
