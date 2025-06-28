import logging
from typing import List

from django.http import HttpRequest, JsonResponse
from ninja import NinjaAPI, Router
from ninja.errors import ValidationError
from ninja.security import HttpBearer
import jwt
from django.conf import settings

from .models import User
from .schemas import (
    LoginSchema,
    ProfileResponseSchema,
    SignUpSchema,
    TokenSchema,
    MatchRequestCreateSchema,
    MatchRequestResponseSchema,
    ErrorResponseSchema,
)
from .services import (
    AuthService,
    ProfileService,
    MentorService,
    MatchRequestService,
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


api = NinjaAPI(
    title="멘토-멘티 매칭 API",
    version="1.0.0",
    description="멘토와 멘티를 매칭하는 시스템의 REST API",
    openapi_url="/openapi.json",  # OpenAPI JSON 파일 엔드포인트
    docs_url="/docs",  # Swagger UI 엔드포인트 (기본값)
    auth=GlobalAuth(),
)


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
    # 필수 필드 누락 시 400 반환
    if not payload.email or not payload.password:
        return 400, {"error": "이메일과 비밀번호는 필수입니다."}
    user = AuthService.authenticate_user(payload.email, payload.password)
    if user:
        token = AuthService.create_jwt_token(user)
        return 200, {"token": token}
    else:
        return 401, {"error": "Invalid credentials"}


@router.post("/signup", response={201: None, 400: dict}, auth=None)
def signup(request: HttpRequest, payload: SignUpSchema):
    """회원가입 API"""
    try:
        AuthService.register_user(
            email=payload.email,
            password=payload.password,
            name=payload.name,
            role=payload.role,
        )
        return 201, None
    except ValueError as e:
        return 400, {"error": str(e)}


@router.get("/me", response={200: ProfileResponseSchema, 401: dict})
def get_me(request: HttpRequest):
    """현재 로그인한 사용자의 정보 조회"""
    user = request.auth
    response_data = ProfileService.get_user_profile_data(user)
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

    try:
        response_data = ProfileService.update_profile(user, data)
        return 200, response_data
    except ValueError as e:
        return 400, {"error": str(e)}


@router.get("/images/{role}/{user_id}", response={200: None, 404: dict, 401: dict})
def get_profile_image(request: HttpRequest, role: str, user_id: int):
    """프로필 이미지 조회 API (DB에서 이미지 데이터 반환)"""
    from django.http import HttpResponse

    try:
        image_data, content_type = ProfileService.get_profile_image(role, user_id)
        response = HttpResponse(image_data, content_type=content_type)
        return response
    except ValueError as e:
        return 404, {"error": str(e)}


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

        mentor_list = MentorService.get_mentors(skill=skill, order_by=order_by)
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

        response_data = MatchRequestService.create_match_request(
            mentee=request.auth, mentor_id=payload.mentorId, message=payload.message
        )
        return 200, response_data

    except ValueError as e:
        return 400, {"error": str(e)}
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

        request_list = MatchRequestService.get_incoming_match_requests(request.auth)
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

        request_list = MatchRequestService.get_outgoing_match_requests(request.auth)
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

        response_data = MatchRequestService.accept_match_request(
            request.auth, request_id
        )
        return 200, response_data

    except ValueError as e:
        return 404, {"error": str(e)}
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

        response_data = MatchRequestService.reject_match_request(
            request.auth, request_id
        )
        return 200, response_data

    except ValueError as e:
        return 404, {"error": str(e)}
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

        response_data = MatchRequestService.cancel_match_request(
            request.auth, request_id
        )
        return 200, response_data

    except ValueError as e:
        return 404, {"error": str(e)}
    except Exception as e:
        logger.error(f"Error cancelling match request: {e}")
        return 500, {"error": "Internal server error"}


api.add_router("/", router)
