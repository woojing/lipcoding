from django.shortcuts import render
from django.http import HttpRequest


def index(request: HttpRequest):
    """메인 페이지 (로그인/회원가입)"""
    return render(request, 'frontend/index.html')


def dashboard(request: HttpRequest):
    """대시보드 페이지"""
    return render(request, 'frontend/dashboard.html')


def profile(request: HttpRequest):
    """프로필 관리 페이지"""
    return render(request, 'frontend/profile.html')


def mentors(request: HttpRequest):
    """멘토 리스트 페이지 (멘티 전용)"""
    return render(request, 'frontend/mentors.html')


def requests(request: HttpRequest):
    """매칭 요청 관리 페이지"""
    return render(request, 'frontend/requests.html')
