# CodePath Backend API

개발자 학습 플랫폼 CodePath의 백엔드 API 서버입니다.

## 기술 스택

- **Framework**: FastAPI 0.109+
- **Language**: Python 3.11+
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **ORM**: SQLAlchemy 2.0 (Async)
- **Authentication**: JWT (python-jose)
- **Validation**: Pydantic 2.0

## 주요 기능

### MVP 구현 범위

1. **인증 시스템**
   - 회원가입 (이메일/비밀번호)
   - 로그인
   - JWT 기반 인증
   - 토큰 갱신
   - 사용자 정보 조회

2. **문제 관리**
   - 문제 목록 조회 (페이지네이션, 필터링)
   - 문제 상세 조회
   - 난이도별 분류 (Beginner, Easy, Medium, Hard, Expert)
   - 카테고리별 분류 (Algorithm, Data Structure, String, Math 등)

3. **코드 실행 및 제출**
   - 코드 실행 (가시적 테스트 케이스)
   - 코드 제출 (모든 테스트 케이스 포함)
   - 실행 결과 및 피드백
   - 제출 기록 저장

4. **대시보드**
   - 문제 풀이 진행률
   - 난이도별 해결 통계
   - 최근 제출 기록
   - 연속 학습 일수

## 프로젝트 구조

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py          # 인증 API
│   │       │   ├── problems.py      # 문제 API
│   │       │   └── dashboard.py     # 대시보드 API
│   │       └── deps.py              # API 의존성
│   ├── core/
│   │   ├── config.py                # 설정 관리
│   │   ├── database.py              # DB 연결
│   │   ├── security.py              # 보안 유틸
│   │   └── exceptions.py            # 커스텀 예외
│   ├── models/
│   │   ├── user.py                  # User 모델
│   │   ├── problem.py               # Problem 모델
│   │   └── submission.py            # Submission 모델
│   ├── schemas/
│   │   ├── auth.py                  # 인증 스키마
│   │   ├── problem.py               # 문제 스키마
│   │   └── dashboard.py             # 대시보드 스키마
│   ├── services/
│   │   ├── auth_service.py          # 인증 서비스
│   │   ├── problem_service.py       # 문제 서비스
│   │   ├── code_execution_service.py # 코드 실행 서비스
│   │   └── dashboard_service.py     # 대시보드 서비스
│   └── main.py                      # 메인 애플리케이션
├── scripts/
│   └── seed_data.py                 # DB 시딩 스크립트
├── docker-compose.yml               # Docker 설정
├── Dockerfile                       # 컨테이너 이미지
├── requirements.txt                 # Python 의존성
├── pyproject.toml                   # Poetry 설정
└── .env                             # 환경 변수
```

## 시작하기

### 사전 요구사항

- Python 3.11 이상
- PostgreSQL 15 이상
- Redis 7 이상
- Docker & Docker Compose (선택사항)

### 1. 저장소 클론

```bash
cd /Users/junsik/Desktop/subagent-test/backend
```

### 2. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate    # Windows
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. Docker로 PostgreSQL & Redis 실행

```bash
docker-compose up -d
```

서비스 확인:
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### 5. 환경 변수 설정

`.env` 파일이 이미 생성되어 있습니다. 필요시 수정하세요.

```bash
# .env 파일 확인
cat .env
```

주요 환경 변수:
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `REDIS_URL`: Redis 연결 문자열
- `SECRET_KEY`: JWT 서명 키 (프로덕션에서 변경 필수)

### 6. 데이터베이스 시딩

테스트 데이터(사용자 및 문제)를 생성합니다:

```bash
python scripts/seed_data.py
```

생성되는 테스트 계정:
- **User**: `test@codepath.com` / `Test123!`

관리자 계정은 환경 변수로만 생성되며, 앱 시작 시 자동 부트스트랩됩니다:
- `ADMIN_EMAIL`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_FULL_NAME`

생성되는 문제:
- Two Sum (Easy)
- Reverse String (Beginner)
- Valid Parentheses (Easy)
- Fibonacci Number (Beginner)
- Maximum Subarray (Medium)

### 7. 서버 실행

```bash
# 개발 모드 (자동 재시작)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 직접 실행
python -m app.main
```

서버가 실행되면:
- API 서버: http://localhost:8000
- API 문서 (Swagger): http://localhost:8000/api/docs
- API 문서 (ReDoc): http://localhost:8000/api/redoc

## API 엔드포인트

### 인증 (Authentication)

#### 회원가입
```http
POST /api/v1/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "Password123!",
  "full_name": "Full Name"
}
```

#### 로그인
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "Password123!"
}
```

응답:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### 사용자 정보 조회
```http
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

#### 토큰 갱신
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 로그아웃
```http
POST /api/v1/auth/logout
Authorization: Bearer {access_token}
```

### 문제 (Problems)

#### 문제 목록 조회
```http
GET /api/v1/problems?page=1&page_size=20&difficulty=easy&category=algorithm
Authorization: Bearer {access_token}
```

#### 문제 상세 조회
```http
GET /api/v1/problems/{problem_id}
Authorization: Bearer {access_token}
```

#### 코드 실행 (테스트)
```http
POST /api/v1/problems/{problem_id}/run
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "code": "def solution(nums, target):\n    return [0, 1]",
  "language": "python"
}
```

#### 코드 제출
```http
POST /api/v1/problems/{problem_id}/submit
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "code": "def solution(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []",
  "language": "python"
}
```

### 대시보드 (Dashboard)

#### 대시보드 조회
```http
GET /api/v1/dashboard
Authorization: Bearer {access_token}
```

응답:
```json
{
  "user_id": "uuid",
  "username": "testuser",
  "progress": {
    "total_problems": 5,
    "solved_problems": 2,
    "attempted_problems": 3,
    "success_rate": 66.67
  },
  "solved_by_difficulty": {
    "beginner": 1,
    "easy": 1,
    "medium": 0,
    "hard": 0,
    "expert": 0
  },
  "recent_submissions": [...],
  "current_streak": 3,
  "total_submission_count": 15
}
```

## 헬스 체크

```http
GET /health
```

응답:
```json
{
  "status": "healthy",
  "app_name": "CodePath Backend",
  "version": "0.1.0",
  "environment": "development"
}
```

## 개발 가이드

### 코드 포맷팅

```bash
# Black 포맷터
black app/

# Flake8 린터
flake8 app/
```

### 타입 체크

```bash
mypy app/
```

### 데이터베이스 마이그레이션

현재 MVP는 자동 테이블 생성을 사용합니다. 프로덕션에서는 Alembic을 사용하세요.

```bash
# Alembic 초기화 (향후)
alembic init migrations

# 마이그레이션 생성
alembic revision --autogenerate -m "Initial migration"

# 마이그레이션 적용
alembic upgrade head
```

## 보안 고려사항

### MVP 단계
- ✅ JWT 기반 인증
- ✅ 비밀번호 해싱 (bcrypt)
- ✅ 비밀번호 강도 검증
- ✅ CORS 설정

### 프로덕션 추가 필요
- ⚠️ SECRET_KEY 변경 (최소 32자)
- ⚠️ HTTPS 사용
- ⚠️ Rate Limiting 구현
- ⚠️ 토큰 블랙리스트 (Redis)
- ⚠️ 코드 실행 샌드박스 (Docker)
- ⚠️ SQL Injection 방어 (이미 ORM으로 보호됨)
- ⚠️ 입력 검증 강화

## 코드 실행 보안

### 현재 (MVP)
- subprocess를 사용한 간단한 코드 실행
- 타임아웃 제한 (5초)
- 출력 크기 제한

### 프로덕션 권장
- Docker 컨테이너 기반 격리
- 리소스 제한 (CPU, 메모리)
- 네트워크 격리
- 파일 시스템 격리

## 문제 해결

### 데이터베이스 연결 오류

```bash
# PostgreSQL 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs postgres

# 재시작
docker-compose restart postgres
```

### Redis 연결 오류

```bash
# Redis 상태 확인
docker-compose ps redis

# Redis CLI 접속
docker-compose exec redis redis-cli ping
```

### 포트 충돌

다른 애플리케이션이 8000, 5432, 6379 포트를 사용 중인지 확인:

```bash
# macOS/Linux
lsof -i :8000
lsof -i :5432
lsof -i :6379
```

## 다음 단계

### Phase 2 계획
1. OAuth 인증 (Google, GitHub, Kakao)
2. 이메일 인증
3. AI 코드 리뷰 (Claude API)
4. 실무 프로젝트 기능
5. 포트폴리오 생성
6. 관리자 페이지
7. 성능 최적화 (캐싱, 인덱싱)

## 라이선스

MIT License

## 기여

이슈 및 PR은 언제든 환영합니다.

## 문의

- Email: support@codepath.com
- Docs: http://localhost:8000/api/docs
