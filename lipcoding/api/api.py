from ninja import NinjaAPI, Router
from ninja.errors import ValidationError
from django.http import HttpRequest, JsonResponse
from .schemas import SignUpSchema
from .models import User

api = NinjaAPI()

# 422 에러를 400으로 변환하는 예외 핸들러
@api.exception_handler(ValidationError)
def validation_errors(request, exc):
    return JsonResponse({"error": "Invalid request data"}, status=400)

router = Router()

@router.get("/hello")
def hello(request: HttpRequest):
    return {"message": "Hello, World!"}

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
