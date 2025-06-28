from ninja import Schema
from typing import Optional, List


import re


class SignUpSchema(Schema):
    email: str
    password: str
    name: str
    role: str

    @staticmethod
    def validate_email(email: str) -> bool:
        # 간단한 이메일 정규식
        return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None

    @classmethod
    def __validate__(cls, value):
        # ninja의 커스텀 유효성 검사 훅
        if not cls.validate_email(value["email"]):
            raise ValueError("유효하지 않은 이메일 형식입니다.")
        # 역할 유효성 검사
        if value["role"] not in ["mentor", "mentee"]:
            raise ValueError("role 값은 mentor 또는 mentee만 허용됩니다.")
        return value


class LoginSchema(Schema):
    email: Optional[str] = None
    password: Optional[str] = None


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


class BaseProfileUpdateSchema(Schema):
    name: str
    bio: str
    image: Optional[str] = None  # BASE64 encoded string


class MentorProfileUpdateSchema(BaseProfileUpdateSchema):
    skills: List[str]


class MenteeProfileUpdateSchema(BaseProfileUpdateSchema):
    pass


# 매칭 요청 관련 스키마
class MatchRequestCreateSchema(Schema):
    mentorId: int
    menteeId: int
    message: str

    @classmethod
    def __validate__(cls, value):
        # 메시지 길이 제한 (예: 500자)
        if "message" in value and len(value["message"]) > 500:
            raise ValueError("메시지는 500자 이내여야 합니다.")
        return value


class MatchRequestResponseSchema(Schema):
    id: int
    mentorId: int
    menteeId: int
    message: str
    status: str


class ErrorResponseSchema(Schema):
    error: str
