import logging
import uuid
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from ninja import NinjaAPI, Router
from ninja.errors import ValidationError
from ninja.security import HttpBearer

from .models import Profile, User
from .schemas import LoginSchema, ProfileResponseSchema, SignUpSchema, TokenSchema

logger = logging.getLogger(__name__)


class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        logger.debug(f"Attempting authentication with token: {token}")
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"], 
                audience="lipcoding-users"
            )
            logger.debug(f"Decoded JWT payload: {payload}")
            user_id = payload.get('sub')
            if not user_id:
                logger.warning("JWT payload is missing 'sub' claim.")
                return None
            user = User.objects.get(id=user_id)
            logger.info(f"Successfully authenticated user: {user.email}")
            return user
        except jwt.ExpiredSignatureError:
            logger.warning("Authentication failed: Expired signature.")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Authentication failed: Invalid token. Error: {e}")
            return None
        except User.DoesNotExist:
            logger.warning("Authentication failed: User does not exist.")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during authentication: {e}")
            return None


api = NinjaAPI(auth=GlobalAuth())


# JWT 토큰 생성 함수
def create_jwt_token(user):
    """요구사항에 맞는 JWT 토큰 생성"""
    now = datetime.utcnow()
    exp_time = now + timedelta(hours=1)  # 1시간 유효기간

    payload = {
        # RFC 7519 표준 클레임들
        "iss": "lipcoding",  # issuer
        "sub": str(user.id),  # subject
        "aud": "lipcoding-users",  # audience
        "exp": int(exp_time.timestamp()),  # expiration time
        "nbf": int(now.timestamp()),  # not before
        "iat": int(now.timestamp()),  # issued at
        "jti": str(uuid.uuid4()),  # JWT ID

        # 커스텀 클레임들
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }

    # Django SECRET_KEY를 JWT 서명에 사용
    secret_key = settings.SECRET_KEY
    token = jwt.encode(payload, secret_key, algorithm="HS256")

    return token


# 422 에러를 400으로 변환하는 예외 핸들러
@api.exception_handler(ValidationError)
def validation_errors(request, exc):
    return JsonResponse({"error": "Invalid request data"}, status=400)


router = Router()


@router.get("/hello", auth=None)
def hello(request: HttpRequest):
    return {"message": "Hello, World!"}


@router.post("/login", response={200: TokenSchema, 400: dict, 401: dict}, auth=None)
def login(request: HttpRequest, payload: LoginSchema):
    """로그인 API - JWT 토큰 발급"""
    try:
        user = User.objects.get(email=payload.email)
        if user.check_password(payload.password):
            token = create_jwt_token(user)
            return 200, {"token": token}
        else:
            return 401, {"error": "Invalid credentials"}
    except User.DoesNotExist:
        return 401, {"error": "Invalid credentials"}


@router.post("/signup", response={201: None, 400: dict}, auth=None)
def signup(request: HttpRequest, payload: SignUpSchema):
    """회원가입 API"""
    if User.objects.filter(email=payload.email).exists():
        return 400, {"error": "Email already exists"}

    User.objects.create_user(
        email=payload.email, password=payload.password, name=payload.name, role=payload.role
    )
    return 201, None


@router.get("/me", response={200: ProfileResponseSchema, 401: dict})
def get_me(request: HttpRequest):
    """현재 로그인한 사용자의 정보 조회"""
    user = request.auth

    # Profile이 없으면 생성
    profile, created = Profile.objects.get_or_create(user=user)

    # 기본 응답 데이터
    response_data = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "profile": {
            "name": user.name,
            "bio": profile.bio,
            "imageUrl": profile.image_url,
        },
    }

    # 멘토인 경우에만 스킬 정보 포함
    if user.role == "mentor":
        response_data["profile"]["skills"] = [skill.name for skill in profile.skills.all()]

    return 200, response_data


api.add_router("/", router)
