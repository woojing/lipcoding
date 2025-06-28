## Python Usage

### Package Management

- ONLY use uv, NEVER pip
- project initialization: uv init
- Installation: uv add package
- Running tools: uv run tool
- Upgrading: uv add --dev package --upgrade-package package
- FORBIDDEN: uv pip install, @latest syntax

# 작업 가이드라인

## 명령실행
커맨드를 실행할때 CWD를 항상 확인 합니다. django 명령어는 언제나 lipcoding 디렉토리에서 실행해야 합니다.
만약 지금 CWD가 lipcoding 이라면 그대로 manage.py를 실행하면 됩니다.
```bash
python manage.py <command>
```

## 프로젝트 설정

### 설정 구성

최초 구성시에는 uv add django django-ninja django-extensions pytest-django ruff 로 필요한 패키지를 설치합니다.

```python
INSTALLED_APPS = [
    # ...existing apps...
    'django_extensions',  # 개발 편의를 위한 도구
    'ninja',  # Django-ninja 프레임워크
    # 사용자 앱들...
]
```

## Django 앱 추가

### 앱 생성 및 설정

Django 앱을 생성할 때, 프로젝트 루트가 아닌 Django 프로젝트 루트(`lipcoding`)에 생성되도록 해야 합니다. 이렇게 하면 참조 문제를 방지할 수 있습니다.

1. `lipcoding` 디렉토리로 이동합니다:

```bash
cd lipcoding
```

2. 앱을 생성합니다:

```bash
python manage.py startapp <app_name>
```

3. 생성된 앱을 `INSTALLED_APPS`에 추가합니다. 예를 들어, `account` 앱을 생성한 경우:

```python
INSTALLED_APPS += [
    'account',  # 사용자 계정 및 인증 관련 앱
]
```

위 설정은 `lipcoding/settings.py` 파일에서 관리됩니다.

### 앱 구조 및 파일 구성

Django 앱의 구조와 주요 파일 역할에 대한 세부 내용은 [`structure.prompt.md`](./structure.prompt.md) 문서를 참조하세요.

## API 구조

### 1. 스키마 정의

데이터베이스 모델은 ModelSchema를, 요청/응답 객체는 Schema를 사용합니다:

```python
from ninja import ModelSchema, Schema

class DatabaseDetailSchema(ModelSchema):
    class Meta:
        model = DatabaseDetail
        fields = ['id', 'name', 'description']

class ExecuteQueryInputSchema(Schema):
    database_detail_id: int
    query: str
```

### 2. API 인스턴스 생성

```python
from ninja import NinjaAPI

api = NinjaAPI(
    version="1",
    servers=[{"url": "http://localhost:8000"}],
    description="API 설명"
)
```

### 3. 엔드포인트 정의

타입 힌트와 동기 코드를 사용하여 성능을 유지합니다:

```python
@api.get("/resource", response=List[ResourceSchema])
def get_resources(request):
    items = list(Resource.objects.all())
    return items

@api.get("/resource/{id}", response=ResourceSchema)
def get_resource(request, id: int):
    return get_object_or_404(Resource, id=id)
```

### 4. 응답 처리

여러 응답 유형을 딕셔너리로 정의합니다:

```python
@api.post(
    "/operation",
    response={200: SuccessSchema, 400: ErrorSchema},
    description="작업 설명"
)
def operation(request, payload: InputSchema):
    try:
        result = process_operation(payload)
        return 200, {"success": True, "data": result}
    except Exception as e:
        return 400, {"error": str(e)}
```

## pytest를 사용한 테스트

### 1. 테스트 설정

일반적인 테스트 시나리오를 위한 픽스처 생성:

```python
@pytest.fixture
def test_resource():
    with temporary_resource() as resource:
        # 테스트 리소스 설정
        yield resource
        # 필요시 정리
```

### 2. 테스트 실행

테스트 `pytest` 명령어를 사용하여 실행합니다:

```bash
pytest
```

### 3. 테스트 케이스 작성

데이터베이스 작업을 위해 django_db 마커 사용:

```python
@pytest.mark.django_db
def test_get_resource(test_resource):
    # 준비
    resource_id = test_resource.id
    
    # 실행
    response = client.get(f"/api/resource/{resource_id}")
    
    # 검증
    assert response.status_code == 200
    assert response.json()['id'] == resource_id
```


## 모범 사례

1. 요청/응답 스키마에 항상 타입 힌트 사용
2. 데이터베이스 작업 시 동기 뷰 사용
3. 태그를 사용하여 관련 엔드포인트 구성
4. 엔드포인트와 스키마에 명확한 설명 제공
5. 데이터베이스 모델에는 ModelSchema 사용하여 코드 중복 줄이기
6. 구체적인 에러 응답으로 적절한 에러 처리 구현
7. 성공과 실패 시나리오 모두에 대한 테스트 작성
8. 픽스처를 사용하여 테스트 데이터 일관성 유지
9. ruff format . 명령어로 코드 스타일 검사 및 자동 포맷팅
10. ruff check --fix . 명령어로 코드 스타일 검사 및 자동 수정

## 문서화

Django-ninja는 자동으로 OpenAPI (Swagger) 문서를 생성합니다. 다음 경로에서 접근 가능:
- Swagger UI: `/api/docs`
- OpenAPI JSON: `/api/docs.json`

문서화 개선 방법:
1. API 엔드포인트에 설명 추가
2. 스키마 정의에 예시 추가
3. 적절한 응답 타입 사용
4. 에러 시나리오 포함
