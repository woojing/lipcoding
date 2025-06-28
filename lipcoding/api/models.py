from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        MENTOR = "mentor", "Mentor"
        MENTEE = "mentee", "Mentee"

    username = None  # username 필드 사용 안 함
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=Role.choices)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "role"]

    objects = UserManager()

    def __str__(self):
        return self.email


class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    image_url = models.URLField(
        max_length=200, blank=True, default="https://placehold.co/500x500.jpg?text=USER"
    )
    image_data = models.BinaryField(null=True, blank=True)  # Base64 이미지 데이터 저장
    image_content_type = models.CharField(max_length=50, default="image/jpeg")  # 이미지 MIME 타입
    skills = models.ManyToManyField(Skill, blank=True)

    def __str__(self):
        return f"{self.user.name}'s Profile"


class MatchRequest(models.Model):
    """멘토-멘티 매칭 요청 모델"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="incoming_match_requests",
        limit_choices_to={"role": "mentor"},
    )
    mentee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="outgoing_match_requests",
        limit_choices_to={"role": "mentee"},
    )
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("mentor", "mentee")  # 중복 요청 방지
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.mentee.name} -> {self.mentor.name} ({self.status})"
