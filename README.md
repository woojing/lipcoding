# 진행 상황 요약 (2025-06-28)

## 1. 프로젝트 초기화 및 패키지 설치
- uv로 다음 패키지 설치: django, django-ninja, django-extensions, pytest-django, ruff

## 2. 장고 프로젝트 및 앱 생성
- `django-admin startproject lipcoding`으로 프로젝트 생성
- `lipcoding` 폴더 내에서 `python manage.py startapp api`로 API 앱 생성

## 3. Django Ninja API 구축
- `api/api.py`에 NinjaAPI 인스턴스 및 `/api/hello` 엔드포인트 구현
- `/api/hello`는 `{ "message": "Hello, World!" }` 반환
- `urls.py`에 NinjaAPI 라우팅 추가

## 4. 설정
- `INSTALLED_APPS`에 'api', 'django_extensions', 'ninja' 추가

## 5. 테스트
- `api/test_api.py`에 pytest 기반 테스트 작성
- `pytest.ini`에 `DJANGO_SETTINGS_MODULE = lipcoding.settings` 지정
- DB 마이그레이션 후 테스트 성공적으로 통과

## 6. TDD 구현 완료 (회원가입)
- **User 모델**: 이메일 기반 커스텀 User 모델, role(mentor/mentee) 추가
- **회원가입 API**: `POST /signup` 구현 완료
- **테스트**: 회원가입 성공/실패 케이스 모두 통과
- **ValidationError 핸들러**: 422 → 400 에러 코드 변환 처리

---

# 백엔드 API 구현 계획 (TDD 접근법)

요구사항과 API 명세에 따라, **테스트 주도 개발(TDD)** 방식으로 멘토-멘티 매칭 API를 구축합니다. 각 기능은 실패하는 테스트 케이스를 먼저 작성하고, 이를 통과시키는 최소한의 코드를 구현하는 순서로 진행합니다.

## 개발 순서 및 실행 계획

### 1. 인증 (Authentication)
- **`POST /signup`**: 회원가입 ✅ **완료**
    1.  ✅ **Test:** 회원가입 실패/성공 테스트 케이스 작성.
    2.  ✅ **Implement:** `User` 모델, `SignUpSchema` 및 회원가입 API 구현.
- **`POST /login`**: 로그인 🚧 **진행 예정**
    1.  **Test:** 로그인 실패/성공 및 JWT 발급 테스트 케이스 작성.
    2.  **Implement:** 로그인 API 및 JWT 생성 로직 구현.

### 2. 사용자 프로필 (User Profile)
- **`GET /me`**: 내 정보 조회
    1.  **Test:** 인증된 사용자의 정보 조회 테스트 케이스 작성.
    2.  **Implement:** `Profile`, `Skill` 모델 및 `/me` API 구현.
- **`PUT /profile`**: 프로필 수정
    1.  **Test:** 프로필(이름, 소개, 스킬, 이미지) 수정 테스트 케이스 작성.
    2.  **Implement:** 프로필 수정 API 및 이미지 처리 로직 구현.
- **`GET /images/:role/:id`**: 프로필 이미지 조회
    1.  **Test:** 프로필 이미지 반환 테스트 케이스 작성.
    2.  **Implement:** 이미지 서빙 API 구현.

### 3. 멘토 (Mentors)
- **`GET /mentors`**: 멘토 목록 조회
    1.  **Test:** 멘토 목록 조회, 기술 스택 필터링, 이름/스킬 정렬 테스트 케이스 작성.
    2.  **Implement:** 멘토 목록 조회 API 구현.

### 4. 매칭 요청 (Match Requests)
- **`POST /match-requests`**: 매칭 요청 생성
    1.  **Test:** 멘티가 멘토에게 요청 보내기 테스트 케이스 작성.
    2.  **Implement:** `MatchRequest` 모델 및 매칭 요청 생성 API 구현.
- **`GET /match-requests/incoming`**: 받은 요청 목록 조회
    1.  **Test:** 멘토가 받은 요청 목록 조회 테스트 케이스 작성.
    2.  **Implement:** API 구현.
- **`GET /match-requests/outgoing`**: 보낸 요청 목록 조회
    1.  **Test:** 멘티가 보낸 요청 목록 조회 테스트 케이스 작성.
    2.  **Implement:** API 구현.
- **`PUT /match-requests/:id/accept`**: 요청 수락
    1.  **Test:** 멘토가 요청 수락 테스트 케이스 작성.
    2.  **Implement:** API 구현.
- **`PUT /match-requests/:id/reject`**: 요청 거절
    1.  **Test:** 멘토가 요청 거절 테스트 케이스 작성.
    2.  **Implement:** API 구현.
- **`DELETE /match-requests/:id`**: 요청 취소/삭제
    1.  **Test:** 멘티가 보낸 요청 취소 테스트 케이스 작성.
    2.  **Implement:** API 구현.

---
- 이 계획에 따라 다음 단계부터 개발을 진행합니다.
