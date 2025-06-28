from ninja import NinjaAPI, Router
from ninja.errors import ValidationError
from django.http import HttpRequest, JsonResponse
from django.contrib.auth import authenticate
from django.conf import settings
from .schemas import SignUpSchema, LoginSchema, TokenSchema
from .models import User
import jwt
import time
from datetime import datetime, timedelta
import uuid

api = NinjaAPI()

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

@router.get("/hello")
def hello(request: HttpRequest):
    return {"message": "Hello, World!"}

@router.post("/login", response={200: TokenSchema, 400: dict, 401: dict})
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

@router.post("/signup", response={201: None, 400: dict})
def signup(request: HttpRequest, payload: SignUpSchema):
    """회원가입 API"""
    if User.objects.filter(email=payload.email).exists():
        return 400, {"error": "Email already exists"}
    
    User.objects.create_user(
        email=payload.email,
        password=payload.password,
        name=payload.name,
        role=payload.role
    )
    return 201, None

api.add_router("/", router)
