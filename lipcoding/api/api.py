import logging
import uuid
from datetime import datetime, timedelta
from typing import List

import jwt
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from ninja import NinjaAPI, Router
from ninja.errors import ValidationError
from ninja.security import HttpBearer

from .models import Profile, User, Skill, MatchRequest
from .schemas import (
    LoginSchema,
    ProfileResponseSchema,
    SignUpSchema,
    TokenSchema,
    MatchRequestCreateSchema,
    MatchRequestResponseSchema,
    ErrorResponseSchema,
)

logger = logging.getLogger(__name__)


class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        logger.debug(f"Attempting authentication with token: {token}")
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                audience="lipcoding-users",
            )
            logger.debug(f"Decoded JWT payload: {payload}")
            user_id = payload.get("sub")
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
        email=payload.email,
        password=payload.password,
        name=payload.name,
        role=payload.role,
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
        response_data["profile"]["skills"] = [
            skill.name for skill in profile.skills.all()
        ]

    return 200, response_data


@router.put("/profile", response={200: ProfileResponseSchema, 400: dict, 401: dict})
def update_profile(request: HttpRequest):
    """프로필 수정 API"""
    user = request.auth

    # JSON 데이터 파싱
    try:
        import json

        data = json.loads(request.body)
    except json.JSONDecodeError:
        return 400, {"error": "Invalid JSON data"}

    # 필수 필드 검증
    if "name" not in data or "bio" not in data:
        return 400, {"error": "Missing required fields: name, bio"}

    # Profile 가져오기 또는 생성
    profile, created = Profile.objects.get_or_create(user=user)

    # 기본 프로필 정보 업데이트
    user.name = data["name"]
    user.save()

    profile.bio = data["bio"]

    # 이미지 처리 (Base64 -> DB 저장)
    if "image" in data and data["image"]:
        import base64

        try:
            # Base64 디코딩
            image_data = base64.b64decode(data["image"])
            
            # 이미지 데이터를 DB에 저장
            profile.image_data = image_data
            profile.image_content_type = "image/jpeg"  # 기본값으로 JPEG 설정
            
            # 이미지 URL을 DB 이미지 조회 경로로 업데이트
            profile.image_url = f"/images/{user.role}/{user.id}"

        except Exception as e:
            # 이미지 처리 실패 시 기본 이미지 URL 유지
            logger.warning(f"Failed to process image for user {user.id}: {e}")
            pass

    # 멘토인 경우 스킬 처리
    if user.role == "mentor":
        if "skills" not in data:
            return 400, {"error": "Skills are required for mentors"}

        # 기존 스킬 제거
        profile.skills.clear()

        # 새로운 스킬 추가
        for skill_name in data["skills"]:
            skill, created = Skill.objects.get_or_create(name=skill_name)
            profile.skills.add(skill)

    profile.save()

    # 응답 데이터 구성
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
        response_data["profile"]["skills"] = [
            skill.name for skill in profile.skills.all()
        ]

    return 200, response_data


@router.get("/images/{role}/{user_id}", response={200: None, 404: dict, 401: dict})
def get_profile_image(request: HttpRequest, role: str, user_id: int):
    """프로필 이미지 조회 API (DB에서 이미지 데이터 반환)"""
    from django.http import HttpResponse

    # 역할 검증
    if role not in ["mentor", "mentee"]:
        return 404, {"error": "Invalid role"}

    try:
        # 사용자와 프로필 조회
        user = User.objects.get(id=user_id, role=role)
        profile = Profile.objects.get(user=user)
        
        # 이미지 데이터가 없는 경우
        if not profile.image_data:
            return 404, {"error": "Image not found"}
            
        # DB에서 이미지 데이터 반환
        response = HttpResponse(
            profile.image_data, 
            content_type=profile.image_content_type
        )
        return response
        
    except (User.DoesNotExist, Profile.DoesNotExist):
        return 404, {"error": "User or profile not found"}


@api.get(
    "/mentors",
    response={
        200: List[ProfileResponseSchema],
        403: ErrorResponseSchema,
        404: ErrorResponseSchema,
    },
    description="멘토 전체 리스트 조회 (멘티 전용)",
)
def get_mentors(request, skill: str = None, order_by: str = None):
    """멘토 리스트 조회 - 멘티만 접근 가능"""
    try:
        # 멘티만 접근 가능
        if request.auth.role != "mentee":
            return 403, {"error": "Only mentees can view mentor list"}

        # 멘토 사용자들 조회
        mentors = (
            User.objects.filter(role="mentor")
            .select_related("profile")
            .prefetch_related("profile__skills")
        )

        # 스킬 필터링
        if skill:
            mentors = mentors.filter(profile__skills__name__icontains=skill)

        # 정렬
        if order_by == "name":
            mentors = mentors.order_by("name")
        elif order_by == "skill":
            mentors = mentors.order_by("profile__skills__name")
        else:
            mentors = mentors.order_by("id")

        # 응답 데이터 구성
        mentor_list = []
        for mentor in mentors:
            if hasattr(mentor, "profile"):
                skills = [skill.name for skill in mentor.profile.skills.all()]
                image_url = (
                    f"/images/mentor/{mentor.id}" if mentor.profile.image_url else None
                )

                mentor_data = {
                    "id": mentor.id,
                    "email": mentor.email,
                    "role": mentor.role,
                    "profile": {
                        "name": mentor.name,
                        "bio": mentor.profile.bio,
                        "imageUrl": image_url,
                        "skills": skills,
                    },
                }
                mentor_list.append(mentor_data)

        return 200, mentor_list

    except Exception as e:
        logger.error(f"Error getting mentors: {e}")
        return 500, {"error": "Internal server error"}


@api.post(
    "/match-requests",
    response={
        200: MatchRequestResponseSchema,
        400: ErrorResponseSchema,
        403: ErrorResponseSchema,
    },
    description="매칭 요청 보내기 (멘티 전용)",
)
def create_match_request(request, payload: MatchRequestCreateSchema):
    """매칭 요청 생성 - 멘티만 접근 가능"""
    try:
        # 멘티만 접근 가능
        if request.auth.role != "mentee":
            return 403, {"error": "Only mentees can create match requests"}

        # 멘토 존재 확인
        try:
            mentor = User.objects.get(id=payload.mentorId, role="mentor")
        except User.DoesNotExist:
            return 400, {"error": "Mentor not found"}

        # 매칭 요청 생성
        match_request = MatchRequest.objects.create(
            mentor=mentor,
            mentee=request.auth,
            message=payload.message,
            status="pending",
        )

        return 200, {
            "id": match_request.id,
            "mentorId": match_request.mentor.id,
            "menteeId": match_request.mentee.id,
            "message": match_request.message,
            "status": match_request.status,
        }

    except Exception as e:
        logger.error(f"Error creating match request: {e}")
        return 500, {"error": "Internal server error"}


@api.get(
    "/match-requests/incoming",
    response={200: List[MatchRequestResponseSchema], 403: ErrorResponseSchema},
    description="나에게 들어온 요청 목록 (멘토 전용)",
)
def get_incoming_match_requests(request):
    """들어온 매칭 요청 목록 조회 - 멘토만 접근 가능"""
    try:
        # 멘토만 접근 가능
        if request.auth.role != "mentor":
            return 403, {"error": "Only mentors can view incoming match requests"}

        match_requests = MatchRequest.objects.filter(mentor=request.auth)

        request_list = []
        for req in match_requests:
            request_data = {
                "id": req.id,
                "mentorId": req.mentor.id,
                "menteeId": req.mentee.id,
                "message": req.message,
                "status": req.status,
            }
            request_list.append(request_data)

        return 200, request_list

    except Exception as e:
        logger.error(f"Error getting incoming match requests: {e}")
        return 500, {"error": "Internal server error"}


@api.get(
    "/match-requests/outgoing",
    response={200: List[MatchRequestResponseSchema], 403: ErrorResponseSchema},
    description="내가 보낸 요청 목록 (멘티 전용)",
)
def get_outgoing_match_requests(request):
    """보낸 매칭 요청 목록 조회 - 멘티만 접근 가능"""
    try:
        # 멘티만 접근 가능
        if request.auth.role != "mentee":
            return 403, {"error": "Only mentees can view outgoing match requests"}

        match_requests = MatchRequest.objects.filter(mentee=request.auth)

        request_list = []
        for req in match_requests:
            request_data = {
                "id": req.id,
                "mentorId": req.mentor.id,
                "menteeId": req.mentee.id,
                "message": req.message,
                "status": req.status,
            }
            request_list.append(request_data)

        return 200, request_list

    except Exception as e:
        logger.error(f"Error getting outgoing match requests: {e}")
        return 500, {"error": "Internal server error"}


@api.put(
    "/match-requests/{int:request_id}/accept",
    response={
        200: MatchRequestResponseSchema,
        404: ErrorResponseSchema,
        403: ErrorResponseSchema,
    },
    description="요청 수락 (멘토 전용)",
)
def accept_match_request(request, request_id: int):
    """매칭 요청 수락 - 멘토만 접근 가능"""
    try:
        # 멘토만 접근 가능
        if request.auth.role != "mentor":
            return 403, {"error": "Only mentors can accept match requests"}

        try:
            match_request = MatchRequest.objects.get(id=request_id, mentor=request.auth)
        except MatchRequest.DoesNotExist:
            return 404, {"error": "Match request not found"}

        match_request.status = "accepted"
        match_request.save()

        return 200, {
            "id": match_request.id,
            "mentorId": match_request.mentor.id,
            "menteeId": match_request.mentee.id,
            "message": match_request.message,
            "status": match_request.status,
        }

    except Exception as e:
        logger.error(f"Error accepting match request: {e}")
        return 500, {"error": "Internal server error"}


@api.put(
    "/match-requests/{int:request_id}/reject",
    response={
        200: MatchRequestResponseSchema,
        404: ErrorResponseSchema,
        403: ErrorResponseSchema,
    },
    description="요청 거절 (멘토 전용)",
)
def reject_match_request(request, request_id: int):
    """매칭 요청 거절 - 멘토만 접근 가능"""
    try:
        # 멘토만 접근 가능
        if request.auth.role != "mentor":
            return 403, {"error": "Only mentors can reject match requests"}

        try:
            match_request = MatchRequest.objects.get(id=request_id, mentor=request.auth)
        except MatchRequest.DoesNotExist:
            return 404, {"error": "Match request not found"}

        match_request.status = "rejected"
        match_request.save()

        return 200, {
            "id": match_request.id,
            "mentorId": match_request.mentor.id,
            "menteeId": match_request.mentee.id,
            "message": match_request.message,
            "status": match_request.status,
        }

    except Exception as e:
        logger.error(f"Error rejecting match request: {e}")
        return 500, {"error": "Internal server error"}


@api.delete(
    "/match-requests/{int:request_id}",
    response={
        200: MatchRequestResponseSchema,
        404: ErrorResponseSchema,
        403: ErrorResponseSchema,
    },
    description="요청 삭제/취소 (멘티 전용)",
)
def cancel_match_request(request, request_id: int):
    """매칭 요청 취소 - 멘티만 접근 가능"""
    try:
        # 멘티만 접근 가능
        if request.auth.role != "mentee":
            return 403, {"error": "Only mentees can cancel match requests"}

        try:
            match_request = MatchRequest.objects.get(id=request_id, mentee=request.auth)
        except MatchRequest.DoesNotExist:
            return 404, {"error": "Match request not found"}

        match_request.status = "cancelled"
        match_request.save()

        return 200, {
            "id": match_request.id,
            "mentorId": match_request.mentor.id,
            "menteeId": match_request.mentee.id,
            "message": match_request.message,
            "status": match_request.status,
        }

    except Exception as e:
        logger.error(f"Error cancelling match request: {e}")
        return 500, {"error": "Internal server error"}


api.add_router("/", router)
