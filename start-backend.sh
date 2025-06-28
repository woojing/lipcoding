#!/bin/bash

# 멘토-멘티 매칭 시스템 - 백엔드 서버 실행 스크립트
# 포트: 8080

echo "🚀 백엔드 서버를 시작합니다..."
echo "📍 포트: 8080"
echo "🔗 API 엔드포인트: http://localhost:8080/api"
echo "📚 API 문서: http://localhost:8080/docs"
echo ""

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화 (uv 사용)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
if [ -d ".venv" ]; then
    echo "🔧 가상환경을 활성화합니다..."
    source .venv/bin/activate
else
    echo "❌ 가상환경을 찾을 수 없습니다. 다음 명령으로 설치해주세요:"
    exit 1
fi

# Django 프로젝트 디렉토리로 이동
cd lipcoding

# 데이터베이스 마이그레이션 확인
echo "🔍 데이터베이스 마이그레이션을 확인합니다..."
python manage.py migrate --check > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📊 데이터베이스 마이그레이션을 실행합니다..."
    python manage.py migrate
fi

# 백엔드 서버 실행
echo "🎯 Django 백엔드 서버를 시작합니다..."
echo "⏹️  중지하려면 Ctrl+C를 누르세요"
echo ""

# 환경 변수 설정
export DJANGO_SETTINGS_MODULE=lipcoding.settings

# Django 개발 서버 실행 (8080 포트)
python manage.py runserver 8080
