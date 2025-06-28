Django-Ninja JWT 인증 구현 가이드

이 가이드는 Django-Ninja를 사용해 JWT(Json Web Token) 기반 인증을 구현하는 방법을 단계별로 설명합니다.


3. 환경변수 설정

루트에 .env 파일 생성 후 비밀키 추가

JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

settings.py에서 로드

import os
from dotenv import load_dotenv
load_dotenv()

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')
JWT_EXP_DELTA_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES'))

4. JWT 유틸 함수 작성

api/utils/jwt.py 생성

import jwt
from datetime import datetime, timedelta
from django.conf import settings


def create_access_token(sub: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXP_DELTA_MINUTES)
    payload = {
        'sub': sub,
        'exp': expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        raise Exception('Token expired')
    except jwt.InvalidTokenError:
        raise Exception('Invalid token')

5. 인증 스키마 및 종속성 설정

api/schemas/auth.py

from ninja.security import HttpBearer, APIKeyHeader
from ninja import Schema
from .utils.jwt import decode_access_token

class Token(Schema):
    access_token: str
    token_type: str = 'bearer'

class LoginData(Schema):
    username: str
    password: str


class JWTBearer(HttpBearer):
    def authenticate(self, request, token: str):
        try:
            payload = decode_access_token(token)
            return payload['sub']
        except Exception:
            return None

6. 로그인 및 인증 라우터 생성

api/routers/auth.py

from ninja import Router
from django.contrib.auth import authenticate
from .schemas.auth import LoginData, Token, JWTBearer
from .utils.jwt import create_access_token

router = Router()

@router.post('/login', response=Token)
def login(request, data: LoginData):
    user = authenticate(request, username=data.username, password=data.password)
    if not user:
        return {'access_token': '', 'token_type': ''}, 401
    token = create_access_token(sub=str(user.id))
    return {'access_token': token, 'token_type': 'bearer'}

@router.get('/protected', auth=JWTBearer(), response={200: str})
def protected(request):
    return f'Authenticated as user {request.auth}'

7. 메인 API 인스턴스 설정

myproject/urls.py 수정

from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from api.routers.auth import router as auth_router

api = NinjaAPI()
api.add_router('/auth/', auth_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]

8. 테스트
	1.	서버 실행

python manage.py runserver

	2.	브라우저 또는 Postman에서 다음 엔드포인트 테스트
	•	POST /api/auth/login - 사용자 인증 후 JWT 발급
	•	GET /api/auth/protected - Authorization: Bearer <token> 헤더 추가 시 접근 가능

⸻