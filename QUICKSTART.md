# CodePath Backend - 빠른 시작 가이드

## 5분 안에 시작하기

### 1단계: Docker로 데이터베이스 실행 (30초)

```bash
cd /Users/junsik/Desktop/subagent-test/backend
docker-compose up -d
```

확인:
```bash
docker-compose ps
```

### 2단계: Python 가상환경 및 의존성 설치 (2분)

```bash
# 가상환경 생성
python3.11 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 3단계: 데이터베이스 초기화 및 시딩 (30초)

```bash
python scripts/seed_data.py
```

성공 메시지가 나타나면 완료입니다!

### 4단계: 서버 실행 (즉시)

```bash
uvicorn app.main:app --reload
```

서버가 실행되면:
- API: http://localhost:8000
- 문서: http://localhost:8000/api/docs

## 테스트하기

### 1. 브라우저에서 API 문서 열기

http://localhost:8000/api/docs

### 2. 로그인하기

Swagger UI에서:
1. `POST /api/v1/auth/login` 엔드포인트 클릭
2. "Try it out" 클릭
3. 다음 내용 입력:

```json
{
  "email": "test@codepath.com",
  "password": "Test123!"
}
```

4. "Execute" 클릭
5. 응답에서 `access_token` 복사

### 3. 인증 설정

Swagger UI 우측 상단:
1. "Authorize" 버튼 클릭
2. `Bearer {복사한_토큰}` 입력
3. "Authorize" 클릭

### 4. 문제 목록 조회

`GET /api/v1/problems` 엔드포인트:
1. "Try it out" 클릭
2. "Execute" 클릭
3. 5개의 테스트 문제 확인

### 5. 코드 실행하기

`POST /api/v1/problems/{problem_id}/run`:
1. 문제 ID 입력 (문제 목록에서 복사)
2. 다음 코드 입력:

```json
{
  "code": "def solution(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []",
  "language": "python"
}
```

3. "Execute" 클릭
4. 테스트 결과 확인

## 테스트 계정

| Email | Password | Role |
|-------|----------|------|
| admin@codepath.com | Admin123! | Admin |
| test@codepath.com | Test123! | User |
| john@example.com | John123! | User |

## 주요 엔드포인트

### 인증
- `POST /api/v1/auth/signup` - 회원가입
- `POST /api/v1/auth/login` - 로그인
- `GET /api/v1/auth/me` - 내 정보
- `POST /api/v1/auth/refresh` - 토큰 갱신

### 문제
- `GET /api/v1/problems` - 문제 목록
- `GET /api/v1/problems/{id}` - 문제 상세
- `POST /api/v1/problems/{id}/run` - 코드 실행
- `POST /api/v1/problems/{id}/submit` - 코드 제출

### 대시보드
- `GET /api/v1/dashboard` - 대시보드

## 문제 해결

### 포트 8000이 사용 중
```bash
# 다른 포트로 실행
uvicorn app.main:app --reload --port 8001
```

### PostgreSQL 연결 오류
```bash
# Docker 컨테이너 재시작
docker-compose restart postgres

# 로그 확인
docker-compose logs postgres
```

### 의존성 설치 오류
```bash
# pip 업그레이드
pip install --upgrade pip

# 다시 설치
pip install -r requirements.txt
```

## 다음 단계

- [전체 문서 읽기](README.md)
- [API 계약서 확인](/Users/junsik/Desktop/subagent-test/docs/api/api-contract.md)
- [TRD 문서 확인](/Users/junsik/Desktop/subagent-test/docs/trd/backend-trd.md)

## 개발 팁

### 자동 재시작
`--reload` 옵션으로 코드 변경 시 자동 재시작됩니다.

### 로그 확인
```bash
# FastAPI 로그는 콘솔에 출력됩니다
```

### 데이터베이스 초기화
```bash
# 기존 데이터 삭제 후 재생성
python scripts/seed_data.py
```

### Docker 중지
```bash
docker-compose down
```

### Docker 데이터 삭제
```bash
docker-compose down -v
```
