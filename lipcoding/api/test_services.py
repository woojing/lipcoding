import pytest
from django.test import Client

from .models import User, Profile, Skill, MatchRequest
from .services import (
    AuthService,
    ProfileService,
    MentorService,
    MatchRequestService,
)


@pytest.mark.django_db
class TestAuthService:
    """인증 서비스 테스트"""

    def test_create_jwt_token(self):
        """JWT 토큰 생성 테스트"""
        user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            name="테스트",
            role="mentor",
        )

        token = AuthService.create_jwt_token(user)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_authenticate_user_success(self):
        """사용자 인증 성공 테스트"""
        User.objects.create_user(
            email="test@example.com",
            password="password123",
            name="테스트",
            role="mentor",
        )

        user = AuthService.authenticate_user("test@example.com", "password123")
        assert user is not None
        assert user.email == "test@example.com"

    def test_authenticate_user_wrong_password(self):
        """잘못된 비밀번호로 인증 실패 테스트"""
        User.objects.create_user(
            email="test@example.com",
            password="password123",
            name="테스트",
            role="mentor",
        )

        user = AuthService.authenticate_user("test@example.com", "wrongpassword")
        assert user is None

    def test_authenticate_user_not_exist(self):
        """존재하지 않는 사용자 인증 실패 테스트"""
        user = AuthService.authenticate_user("nonexistent@example.com", "password123")
        assert user is None

    def test_register_user_success(self):
        """사용자 등록 성공 테스트"""
        user = AuthService.register_user(
            email="new@example.com",
            password="password123",
            name="새로운사용자",
            role="mentee",
        )

        assert user.email == "new@example.com"
        assert user.name == "새로운사용자"
        assert user.role == "mentee"

    def test_register_user_duplicate_email(self):
        """중복 이메일로 등록 실패 테스트"""
        User.objects.create_user(
            email="duplicate@example.com",
            password="password123",
            name="첫번째",
            role="mentor",
        )

        with pytest.raises(ValueError, match="Email already exists"):
            AuthService.register_user(
                email="duplicate@example.com",
                password="password456",
                name="두번째",
                role="mentee",
            )


@pytest.mark.django_db
class TestProfileService:
    """프로필 서비스 테스트"""

    def test_get_or_create_profile(self):
        """프로필 조회 또는 생성 테스트"""
        user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            name="테스트",
            role="mentor",
        )

        profile = ProfileService.get_or_create_profile(user)
        assert profile.user == user

        # 두 번째 호출에서는 같은 프로필 반환
        profile2 = ProfileService.get_or_create_profile(user)
        assert profile.id == profile2.id

    def test_get_user_profile_data_mentor(self):
        """멘토 프로필 데이터 조회 테스트"""
        user = User.objects.create_user(
            email="mentor@example.com",
            password="password123",
            name="멘토",
            role="mentor",
        )

        profile = ProfileService.get_or_create_profile(user)
        profile.bio = "멘토 소개"
        profile.save()

        # 스킬 추가
        skill = Skill.objects.create(name="Python")
        profile.skills.add(skill)

        data = ProfileService.get_user_profile_data(user)

        assert data["id"] == user.id
        assert data["email"] == user.email
        assert data["role"] == "mentor"
        assert data["profile"]["name"] == "멘토"
        assert data["profile"]["bio"] == "멘토 소개"
        assert "skills" in data["profile"]
        assert "Python" in data["profile"]["skills"]

    def test_get_user_profile_data_mentee(self):
        """멘티 프로필 데이터 조회 테스트 (스킬 정보 없음)"""
        user = User.objects.create_user(
            email="mentee@example.com",
            password="password123",
            name="멘티",
            role="mentee",
        )

        profile = ProfileService.get_or_create_profile(user)
        profile.bio = "멘티 소개"
        profile.save()

        data = ProfileService.get_user_profile_data(user)

        assert data["id"] == user.id
        assert data["role"] == "mentee"
        assert "skills" not in data["profile"]

    def test_update_profile_mentor_with_skills(self):
        """멘토 프로필 업데이트 (스킬 포함) 테스트"""
        user = User.objects.create_user(
            email="mentor@example.com",
            password="password123",
            name="멘토",
            role="mentor",
        )

        update_data = {
            "name": "업데이트된멘토",
            "bio": "새로운 소개",
            "skills": ["Python", "Django", "JavaScript"],
        }

        ProfileService.update_profile(user, update_data)

        user.refresh_from_db()
        assert user.name == "업데이트된멘토"

        profile = Profile.objects.get(user=user)
        assert profile.bio == "새로운 소개"

        skill_names = [skill.name for skill in profile.skills.all()]
        assert set(skill_names) == {"Python", "Django", "JavaScript"}

    def test_update_profile_missing_required_fields(self):
        """필수 필드 누락 시 프로필 업데이트 실패 테스트"""
        user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            name="테스트",
            role="mentee",
        )

        with pytest.raises(ValueError, match="Missing required fields"):
            ProfileService.update_profile(user, {"name": "이름만있음"})

    def test_update_profile_mentor_missing_skills(self):
        """멘토 프로필 업데이트 시 스킬 누락 테스트"""
        user = User.objects.create_user(
            email="mentor@example.com",
            password="password123",
            name="멘토",
            role="mentor",
        )

        update_data = {
            "name": "멘토",
            "bio": "소개",
            # skills 누락
        }

        with pytest.raises(ValueError, match="Skills are required for mentors"):
            ProfileService.update_profile(user, update_data)


@pytest.mark.django_db
class TestMentorService:
    """멘토 서비스 테스트"""

    def test_get_mentors_basic(self):
        """기본 멘토 목록 조회 테스트"""
        # 멘토 생성
        mentor = User.objects.create_user(
            email="mentor@example.com",
            password="password123",
            name="멘토",
            role="mentor",
        )
        Profile.objects.create(user=mentor, bio="멘토 소개")

        # 멘티 생성 (결과에 포함되지 않아야 함)
        User.objects.create_user(
            email="mentee@example.com",
            password="password123",
            name="멘티",
            role="mentee",
        )

        mentors = MentorService.get_mentors()

        assert len(mentors) == 1
        assert mentors[0]["id"] == mentor.id
        assert mentors[0]["role"] == "mentor"

    def test_get_mentors_with_skill_filter(self):
        """스킬 필터링으로 멘토 목록 조회 테스트"""
        # Python 스킬을 가진 멘토
        mentor1 = User.objects.create_user(
            email="mentor1@example.com",
            password="password123",
            name="파이썬멘토",
            role="mentor",
        )
        profile1 = Profile.objects.create(user=mentor1, bio="파이썬 전문가")
        python_skill = Skill.objects.create(name="Python")
        profile1.skills.add(python_skill)

        # JavaScript 스킬을 가진 멘토
        mentor2 = User.objects.create_user(
            email="mentor2@example.com",
            password="password123",
            name="자바스크립트멘토",
            role="mentor",
        )
        profile2 = Profile.objects.create(user=mentor2, bio="자바스크립트 전문가")
        js_skill = Skill.objects.create(name="JavaScript")
        profile2.skills.add(js_skill)

        # Python으로 필터링
        mentors = MentorService.get_mentors(skill="Python")

        assert len(mentors) == 1
        assert mentors[0]["id"] == mentor1.id
        assert "Python" in mentors[0]["profile"]["skills"]


@pytest.mark.django_db
class TestMatchRequestService:
    """매칭 요청 서비스 테스트"""

    def test_create_match_request_success(self):
        """매칭 요청 생성 성공 테스트"""
        mentor = User.objects.create_user(
            email="mentor@example.com",
            password="password123",
            name="멘토",
            role="mentor",
        )

        mentee = User.objects.create_user(
            email="mentee@example.com",
            password="password123",
            name="멘티",
            role="mentee",
        )

        response_data = MatchRequestService.create_match_request(
            mentee=mentee, mentor_id=mentor.id, message="도움을 요청합니다."
        )

        assert response_data["mentorId"] == mentor.id
        assert response_data["menteeId"] == mentee.id
        assert response_data["message"] == "도움을 요청합니다."
        assert response_data["status"] == "pending"

    def test_create_match_request_mentor_not_found(self):
        """존재하지 않는 멘토로 매칭 요청 생성 실패 테스트"""
        mentee = User.objects.create_user(
            email="mentee@example.com",
            password="password123",
            name="멘티",
            role="mentee",
        )

        with pytest.raises(ValueError, match="Mentor not found"):
            MatchRequestService.create_match_request(
                mentee=mentee,
                mentor_id=999,  # 존재하지 않는 ID
                message="도움을 요청합니다.",
            )

    def test_accept_match_request_success(self):
        """매칭 요청 수락 성공 테스트"""
        mentor = User.objects.create_user(
            email="mentor@example.com",
            password="password123",
            name="멘토",
            role="mentor",
        )

        mentee = User.objects.create_user(
            email="mentee@example.com",
            password="password123",
            name="멘티",
            role="mentee",
        )

        match_request = MatchRequest.objects.create(
            mentor=mentor, mentee=mentee, message="도움 요청", status="pending"
        )

        response_data = MatchRequestService.accept_match_request(
            mentor, match_request.id
        )

        assert response_data["status"] == "accepted"

        # DB에서 확인
        match_request.refresh_from_db()
        assert match_request.status == "accepted"

    def test_accept_match_request_not_found(self):
        """존재하지 않는 매칭 요청 수락 실패 테스트"""
        mentor = User.objects.create_user(
            email="mentor@example.com",
            password="password123",
            name="멘토",
            role="mentor",
        )

        with pytest.raises(ValueError, match="Match request not found"):
            MatchRequestService.accept_match_request(mentor, 999)


@pytest.mark.django_db
class TestServicesIntegration:
    """서비스 통합 테스트 - API 엔드포인트가 서비스를 올바르게 사용하는지 확인"""

    def test_auth_service_integration_with_api(self):
        """인증 서비스와 API 통합 테스트"""
        client = Client()

        # 회원가입 (AuthService.register_user 사용)
        signup_data = {
            "email": "integration@example.com",
            "password": "password123",
            "name": "통합테스트",
            "role": "mentor",
        }
        response = client.post(
            "/api/signup", signup_data, content_type="application/json"
        )
        assert response.status_code == 201

        # 로그인 (AuthService.authenticate_user, create_jwt_token 사용)
        login_data = {"email": "integration@example.com", "password": "password123"}
        response = client.post(
            "/api/login", login_data, content_type="application/json"
        )
        assert response.status_code == 200
        assert "token" in response.json()

    def test_profile_service_integration_with_api(self):
        """프로필 서비스와 API 통합 테스트"""
        client = Client()

        # 사용자 생성 및 로그인
        user = User.objects.create_user(
            email="profile@example.com",
            password="password123",
            name="프로필테스트",
            role="mentor",
        )
        token = AuthService.create_jwt_token(user)

        # 프로필 조회 (ProfileService.get_user_profile_data 사용)
        response = client.get("/api/me", HTTP_AUTHORIZATION=f"Bearer {token}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profile@example.com"
        assert data["role"] == "mentor"
