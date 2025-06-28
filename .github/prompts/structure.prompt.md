# Django 앱 구조 및 파일 구성

Django 앱은 다음과 같은 구조로 구성하며, 비즈니스 로직을 services.py로 분리합니다:

```
app_name/
├── __init__.py
├── admin.py          # 관리자 인터페이스 설정
├── apps.py           # 앱 설정
├── models.py         # 데이터 모델 (DB 스키마)
├── services.py       # 비즈니스 로직 캡슐화
├── views.py          # HTTP 요청-응답 처리 (템플릿 렌더링)
├── api.py            # REST API 엔드포인트 (선택적)
├── forms.py          # 폼 정의 (필요시)
├── signals.py        # 시그널 핸들러 (필요시)
├── urls.py           # URL 라우팅
├── helpers.py        # 유틸리티 함수 (필요시)
├── constants.py      # 상수 정의 (필요시)
├── managers.py       # 커스텀 모델 매니저 (필요시)
├── templates/        # 앱 관련 템플릿
│   └── app_name/
│       └── *.html
├── static/           # 정적 파일
│   └── app_name/
│       ├── css/
│       ├── js/
│       └── img/
├── fixtures/         # 테스트 데이터
│   └── *.json
└── tests/            # 테스트
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    ├── test_services.py
    └── test_api.py
```

## 주요 파일 역할 및 작성 방식

### 1. models.py: 데이터 모델 정의

데이터베이스 스키마를 정의하며, 간단한 검증과 기본 메소드만 포함합니다:

```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Resource(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']
```

### 2. services.py: 비즈니스 로직 캡슐화

모델과 뷰 사이의 비즈니스 로직을 분리하여 관리합니다:

```python
from .models import Resource
from django.db import transaction

def create_resource(name, owner, **kwargs):
    """리소스 생성 로직"""
    with transaction.atomic():
        resource = Resource.objects.create(
            name=name,
            owner=owner,
            **kwargs
        )
        # 추가 로직 수행 (알림 전송, 로깅 등)
        return resource

def update_resource(resource_id, **data):
    """리소스 업데이트 로직"""
    resource = Resource.objects.get(id=resource_id)
    for key, value in data.items():
        setattr(resource, key, value)
    resource.save()
    return resource
```

### 3. views.py: HTTP 요청-응답 처리

HTTP 요청을 처리하고 서비스 레이어를 호출하여 비즈니스 로직을 실행합니다:

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Resource
from .services import create_resource
from .forms import ResourceForm

@login_required
def create_resource_view(request):
    if request.method == "POST":
        form = ResourceForm(request.POST)
        if form.is_valid():
            # 서비스 계층에 비즈니스 로직 위임
            create_resource(
                name=form.cleaned_data['name'],
                owner=request.user,
                **form.cleaned_data
            )
            return redirect('resource_list')
    else:
        form = ResourceForm()
    
    return render(request, 'app_name/create_resource.html', {'form': form})
```

### 4. api.py: REST API 엔드포인트

Django Ninja를 사용하여 REST API 엔드포인트를 정의합니다:

```python
from ninja import Router
from django.shortcuts import get_object_or_404
from .services import create_resource
from .models import Resource
from .schemas import ResourceInSchema, ResourceOutSchema

router = Router()

@router.post("/resources/", response=ResourceOutSchema)
def create_resource(request, payload: ResourceInSchema):
    resource = create_resource(
        name=payload.name,
        owner=request.user,
        **payload.dict()
    )
    return resource

@router.get("/resources/{resource_id}", response=ResourceOutSchema)
def get_resource(request, resource_id: int):
    resource = get_object_or_404(Resource, id=resource_id)
    return resource
```

### 5. forms.py: 폼 정의

사용자 입력을 검증하고 처리하기 위한 폼을 정의합니다:

```python
from django import forms
from .models import Resource

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['name']
        
    def clean_name(self):
        name = self.cleaned_data['name']
        # 커스텀 검증 로직
        if len(name) < 3:
            raise forms.ValidationError("이름은 3글자 이상이어야 합니다.")
        return name
```

### 6. urls.py: URL 라우팅

앱의 URL 패턴을 정의합니다:

```python
from django.urls import path
from . import views

app_name = 'app_name'

urlpatterns = [
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/create/', views.create_resource_view, name='create_resource'),
    path('resources/<int:resource_id>/', views.resource_detail, name='resource_detail'),
]
```

### 7. admin.py: 관리자 인터페이스 설정

Django 관리자 페이지에서 모델을 관리할 수 있도록 설정합니다:

```python
from django.contrib import admin
from .models import Resource

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'owner']
    list_filter = ['created_at']
    search_fields = ['name', 'owner__username']
```

### 8. signals.py: 모델 시그널 처리

모델 이벤트에 대한 핸들러를 정의합니다:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Resource

@receiver(post_save, sender=Resource)
def resource_created(sender, instance, created, **kwargs):
    if created:
        # 리소스 생성 후 실행할 작업
        pass
```

## 테스트 구조화

테스트는 기능별로 파일을 분리하고 명확한 네이밍 규칙을 따릅니다:

```python
# tests/test_services.py
import pytest
from ..models import Resource
from ..services import create_resource

@pytest.mark.django_db
def test_create_resource():
    # Given
    user = mixer.blend('auth.User')
    resource_data = {"name": "Test Resource"}
    
    # When
    resource = create_resource(
        name=resource_data["name"],
        owner=user
    )
    
    # Then
    assert resource.name == resource_data["name"]
    assert resource.owner == user
```
