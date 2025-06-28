import logging
import uuid
import base64
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import jwt
from django.conf import settings
from django.db import transaction

from .models import Profile, User, Skill, MatchRequest

logger = logging.getLogger(__name__)


class AuthService:
    """인증 관련 서비스"""

    @staticmethod
    def create_jwt_token(user: User) -> str:
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

    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[User]:
        """사용자 인증"""
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
            return None
        except User.DoesNotExist:
            return None

    @staticmethod
    def register_user(email: str, password: str, name: str, role: str) -> User:
        """사용자 등록"""
        if User.objects.filter(email=email).exists():
            raise ValueError("Email already exists")

        return User.objects.create_user(
            email=email,
            password=password,
            name=name,
            role=role,
        )


class ProfileService:
    """프로필 관련 서비스"""

    @staticmethod
    def get_or_create_profile(user: User) -> Profile:
        """프로필 조회 또는 생성"""
        profile, created = Profile.objects.get_or_create(user=user)
        return profile

    @staticmethod
    def get_user_profile_data(user: User) -> Dict[str, Any]:
        """사용자 프로필 데이터 조회"""
        profile = ProfileService.get_or_create_profile(user)

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

        return response_data

    @staticmethod
    @transaction.atomic
    def update_profile(user: User, data: Dict[str, Any]) -> Dict[str, Any]:
        """프로필 업데이트"""
        # 필수 필드 검증
        if "name" not in data or "bio" not in data:
            raise ValueError("Missing required fields: name, bio")

        # Profile 가져오기 또는 생성
        profile = ProfileService.get_or_create_profile(user)

        # 기본 프로필 정보 업데이트
        user.name = data["name"]
        user.save()

        profile.bio = data["bio"]

        # 이미지 처리 (Base64 -> DB 저장)
        if "image" in data and data["image"]:
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
                raise ValueError("Skills are required for mentors")

            # 기존 스킬 제거
            profile.skills.clear()

            # 새로운 스킬 추가
            for skill_name in data["skills"]:
                skill, created = Skill.objects.get_or_create(name=skill_name)
                profile.skills.add(skill)

        profile.save()

        return ProfileService.get_user_profile_data(user)

    @staticmethod
    def get_profile_image(role: str, user_id: int) -> tuple[bytes, str]:
        """프로필 이미지 데이터 조회"""
        # 역할 검증
        if role not in ["mentor", "mentee"]:
            raise ValueError("Invalid role")

        try:
            # 사용자와 프로필 조회
            user = User.objects.get(id=user_id, role=role)
            profile = Profile.objects.get(user=user)

            # 이미지 데이터가 없는 경우
            if not profile.image_data:
                raise ValueError("Image not found")

            return profile.image_data, profile.image_content_type

        except (User.DoesNotExist, Profile.DoesNotExist):
            raise ValueError("User or profile not found")


class MentorService:
    """멘토 관련 서비스"""

    @staticmethod
    def get_mentors(
        skill: Optional[str] = None, order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """멘토 리스트 조회"""
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

        return mentor_list


class MatchRequestService:
    """매칭 요청 관련 서비스"""

    @staticmethod
    def create_match_request(
        mentee: User, mentor_id: int, message: str
    ) -> Dict[str, Any]:
        """매칭 요청 생성"""
        # 멘토 존재 확인
        try:
            mentor = User.objects.get(id=mentor_id, role="mentor")
        except User.DoesNotExist:
            raise ValueError("Mentor not found")

        # 매칭 요청 생성
        match_request = MatchRequest.objects.create(
            mentor=mentor,
            mentee=mentee,
            message=message,
            status="pending",
        )

        return {
            "id": match_request.id,
            "mentorId": match_request.mentor.id,
            "menteeId": match_request.mentee.id,
            "message": match_request.message,
            "status": match_request.status,
        }

    @staticmethod
    def get_incoming_match_requests(mentor: User) -> List[Dict[str, Any]]:
        """들어온 매칭 요청 목록 조회"""
        match_requests = MatchRequest.objects.filter(mentor=mentor)

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

        return request_list

    @staticmethod
    def get_outgoing_match_requests(mentee: User) -> List[Dict[str, Any]]:
        """보낸 매칭 요청 목록 조회"""
        match_requests = MatchRequest.objects.filter(mentee=mentee)

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

        return request_list

    @staticmethod
    def accept_match_request(mentor: User, request_id: int) -> Dict[str, Any]:
        """매칭 요청 수락"""
        try:
            match_request = MatchRequest.objects.get(id=request_id, mentor=mentor)
        except MatchRequest.DoesNotExist:
            raise ValueError("Match request not found")

        match_request.status = "accepted"
        match_request.save()

        return {
            "id": match_request.id,
            "mentorId": match_request.mentor.id,
            "menteeId": match_request.mentee.id,
            "message": match_request.message,
            "status": match_request.status,
        }

    @staticmethod
    def reject_match_request(mentor: User, request_id: int) -> Dict[str, Any]:
        """매칭 요청 거절"""
        try:
            match_request = MatchRequest.objects.get(id=request_id, mentor=mentor)
        except MatchRequest.DoesNotExist:
            raise ValueError("Match request not found")

        match_request.status = "rejected"
        match_request.save()

        return {
            "id": match_request.id,
            "mentorId": match_request.mentor.id,
            "menteeId": match_request.mentee.id,
            "message": match_request.message,
            "status": match_request.status,
        }

    @staticmethod
    def cancel_match_request(mentee: User, request_id: int) -> Dict[str, Any]:
        """매칭 요청 취소"""
        try:
            match_request = MatchRequest.objects.get(id=request_id, mentee=mentee)
        except MatchRequest.DoesNotExist:
            raise ValueError("Match request not found")

        match_request.status = "cancelled"
        match_request.save()

        return {
            "id": match_request.id,
            "mentorId": match_request.mentor.id,
            "menteeId": match_request.mentee.id,
            "message": match_request.message,
            "status": match_request.status,
        }
