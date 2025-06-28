"""
멘토-멘티 매칭 기능 테스트
"""

import pytest
from django.test import Client
from django.contrib.auth import get_user_model
import json

from .models import Profile, Skill

User = get_user_model()


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def mentor_user():
    """멘토 사용자 생성"""
    user = User.objects.create_user(
        email="mentor@example.com", password="testpass123", role="mentor"
    )
    return user


@pytest.fixture
def mentor_profile(mentor_user):
    """멘토 프로필 생성"""
    # User 모델의 name 필드 업데이트
    mentor_user.name = "김멘토"
    mentor_user.save()

    profile = Profile.objects.create(user=mentor_user, bio="프론트엔드 멘토입니다")

    # 스킬 추가
    react_skill, _ = Skill.objects.get_or_create(name="React")
    vue_skill, _ = Skill.objects.get_or_create(name="Vue")
    profile.skills.add(react_skill, vue_skill)

    return profile


@pytest.fixture
def mentee_user():
    """멘티 사용자 생성"""
    user = User.objects.create_user(
        email="mentee@example.com", password="testpass123", role="mentee"
    )
    return user


@pytest.fixture
def mentee_profile(mentee_user):
    """멘티 프로필 생성"""
    # User 모델의 name 필드 업데이트
    mentee_user.name = "이멘티"
    mentee_user.save()

    profile = Profile.objects.create(user=mentee_user, bio="프론트엔드 학습중입니다")
    return profile


@pytest.fixture
def mentor_token(client, mentor_user):
    """멘토 JWT 토큰 생성"""
    response = client.post(
        "/api/login",
        {"email": mentor_user.email, "password": "testpass123"},
        content_type="application/json",
    )

    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture
def mentee_token(client, mentee_user):
    """멘티 JWT 토큰 생성"""
    response = client.post(
        "/api/login",
        {"email": mentee_user.email, "password": "testpass123"},
        content_type="application/json",
    )

    assert response.status_code == 200
    return response.json()["token"]


class TestMentorList:
    """멘토 리스트 조회 테스트"""

    @pytest.mark.django_db
    def test_get_mentors_success(self, client, mentee_token, mentor_profile):
        """멘토 리스트 조회 성공"""
        response = client.get(
            "/api/mentors", HTTP_AUTHORIZATION=f"Bearer {mentee_token}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        mentor_data = data[0]
        assert mentor_data["id"] == mentor_profile.user.id
        assert mentor_data["email"] == mentor_profile.user.email
        assert mentor_data["role"] == "mentor"
        assert mentor_data["profile"]["name"] == mentor_profile.user.name
        assert mentor_data["profile"]["bio"] == mentor_profile.bio
        assert len(mentor_data["profile"]["skills"]) == 2
        assert "React" in mentor_data["profile"]["skills"]
        assert "Vue" in mentor_data["profile"]["skills"]

    @pytest.mark.django_db
    def test_get_mentors_with_skill_filter(self, client, mentee_token, mentor_profile):
        """스킬 필터로 멘토 리스트 조회"""
        response = client.get(
            "/api/mentors?skill=React", HTTP_AUTHORIZATION=f"Bearer {mentee_token}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "React" in data[0]["profile"]["skills"]

    @pytest.mark.django_db
    def test_get_mentors_with_skill_filter_no_match(
        self, client, mentee_token, mentor_profile
    ):
        """매칭되지 않는 스킬로 필터링시 빈 배열 반환"""
        response = client.get(
            "/api/mentors?skill=Django", HTTP_AUTHORIZATION=f"Bearer {mentee_token}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @pytest.mark.django_db
    def test_get_mentors_order_by_name(self, client, mentee_token):
        """이름순으로 멘토 리스트 정렬"""
        # 여러 멘토 생성
        mentor1 = User.objects.create_user(
            email="mentor1@example.com",
            password="testpass123",
            role="mentor",
            name="홍길동",
        )
        Profile.objects.create(user=mentor1, bio="멘토1")

        mentor2 = User.objects.create_user(
            email="mentor2@example.com",
            password="testpass123",
            role="mentor",
            name="김철수",
        )
        Profile.objects.create(user=mentor2, bio="멘토2")

        response = client.get(
            "/api/mentors?order_by=name", HTTP_AUTHORIZATION=f"Bearer {mentee_token}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["profile"]["name"] == "김철수"  # ㄱ이 먼저
        assert data[1]["profile"]["name"] == "홍길동"  # ㅎ이 나중

    @pytest.mark.django_db
    def test_get_mentors_mentee_only(self, client, mentor_token, mentor_profile):
        """멘토는 멘토 리스트 조회 불가"""
        response = client.get(
            "/api/mentors", HTTP_AUTHORIZATION=f"Bearer {mentor_token}"
        )

        assert response.status_code == 403
        assert "Only mentees can view mentor list" in response.json()["error"]

    @pytest.mark.django_db
    def test_get_mentors_unauthorized(self, client, mentor_profile):
        """인증 없이 멘토 리스트 조회 불가"""
        response = client.get("/api/mentors")

        assert response.status_code == 401


class TestMatchRequest:
    """매칭 요청 시스템 테스트"""

    @pytest.mark.django_db
    def test_create_match_request_success(
        self, client, mentee_token, mentor_user, mentee_user
    ):
        """매칭 요청 생성 성공"""
        request_data = {
            "mentorId": mentor_user.id,
            "menteeId": mentee_user.id,
            "message": "멘토링 받고 싶어요!",
        }

        response = client.post(
            "/api/match-requests",
            json.dumps(request_data),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {mentee_token}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["mentorId"] == mentor_user.id
        assert data["menteeId"] == mentee_user.id
        assert data["message"] == "멘토링 받고 싶어요!"
        assert data["status"] == "pending"
        assert "id" in data

    @pytest.mark.django_db
    def test_create_match_request_mentor_not_found(
        self, client, mentee_token, mentee_user
    ):
        """존재하지 않는 멘토에게 요청시 에러"""
        request_data = {
            "mentorId": 999,
            "menteeId": mentee_user.id,
            "message": "멘토링 받고 싶어요!",
        }

        response = client.post(
            "/api/match-requests",
            json.dumps(request_data),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {mentee_token}",
        )

        assert response.status_code == 400
        assert "Mentor not found" in response.json()["error"]

    @pytest.mark.django_db
    def test_create_match_request_mentor_only(
        self, client, mentor_token, mentor_user, mentee_user
    ):
        """멘토는 매칭 요청 생성 불가"""
        request_data = {
            "mentorId": mentor_user.id,
            "menteeId": mentee_user.id,
            "message": "멘토링 받고 싶어요!",
        }

        response = client.post(
            "/api/match-requests",
            json.dumps(request_data),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {mentor_token}",
        )

        assert response.status_code == 403
        assert "Only mentees can create match requests" in response.json()["error"]

    @pytest.mark.django_db
    def test_get_incoming_match_requests(
        self, client, mentor_token, mentor_user, mentee_user
    ):
        """멘토가 받은 매칭 요청 목록 조회"""
        # 매칭 요청 생성
        from .models import MatchRequest

        match_request = MatchRequest.objects.create(
            mentor=mentor_user,
            mentee=mentee_user,
            message="멘토링 받고 싶어요!",
            status="pending",
        )

        response = client.get(
            "/api/match-requests/incoming", HTTP_AUTHORIZATION=f"Bearer {mentor_token}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == match_request.id
        assert data[0]["mentorId"] == mentor_user.id
        assert data[0]["menteeId"] == mentee_user.id
        assert data[0]["message"] == "멘토링 받고 싶어요!"
        assert data[0]["status"] == "pending"

    @pytest.mark.django_db
    def test_get_outgoing_match_requests(
        self, client, mentee_token, mentor_user, mentee_user
    ):
        """멘티가 보낸 매칭 요청 목록 조회"""
        from .models import MatchRequest

        match_request = MatchRequest.objects.create(
            mentor=mentor_user,
            mentee=mentee_user,
            message="멘토링 받고 싶어요!",
            status="pending",
        )

        response = client.get(
            "/api/match-requests/outgoing", HTTP_AUTHORIZATION=f"Bearer {mentee_token}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == match_request.id
        assert data[0]["mentorId"] == mentor_user.id
        assert data[0]["menteeId"] == mentee_user.id
        assert data[0]["status"] == "pending"

    @pytest.mark.django_db
    def test_accept_match_request(self, client, mentor_token, mentor_user, mentee_user):
        """매칭 요청 수락"""
        from .models import MatchRequest

        match_request = MatchRequest.objects.create(
            mentor=mentor_user,
            mentee=mentee_user,
            message="멘토링 받고 싶어요!",
            status="pending",
        )

        response = client.put(
            f"/api/match-requests/{match_request.id}/accept",
            HTTP_AUTHORIZATION=f"Bearer {mentor_token}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"

        # DB에서 상태 확인
        match_request.refresh_from_db()
        assert match_request.status == "accepted"

    @pytest.mark.django_db
    def test_reject_match_request(self, client, mentor_token, mentor_user, mentee_user):
        """매칭 요청 거절"""
        from .models import MatchRequest

        match_request = MatchRequest.objects.create(
            mentor=mentor_user,
            mentee=mentee_user,
            message="멘토링 받고 싶어요!",
            status="pending",
        )

        response = client.put(
            f"/api/match-requests/{match_request.id}/reject",
            HTTP_AUTHORIZATION=f"Bearer {mentor_token}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

        # DB에서 상태 확인
        match_request.refresh_from_db()
        assert match_request.status == "rejected"

    @pytest.mark.django_db
    def test_cancel_match_request(self, client, mentee_token, mentor_user, mentee_user):
        """매칭 요청 취소"""
        from .models import MatchRequest

        match_request = MatchRequest.objects.create(
            mentor=mentor_user,
            mentee=mentee_user,
            message="멘토링 받고 싶어요!",
            status="pending",
        )

        response = client.delete(
            f"/api/match-requests/{match_request.id}",
            HTTP_AUTHORIZATION=f"Bearer {mentee_token}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

        # DB에서 상태 확인
        match_request.refresh_from_db()
        assert match_request.status == "cancelled"

    @pytest.mark.django_db
    def test_match_request_not_found(self, client, mentor_token):
        """존재하지 않는 매칭 요청 처리"""
        response = client.put(
            "/api/match-requests/999/accept",
            HTTP_AUTHORIZATION=f"Bearer {mentor_token}",
        )

        assert response.status_code == 404
        assert "Match request not found" in response.json()["error"]
