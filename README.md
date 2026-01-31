# CodePath Backend

Python 학습 플랫폼 백엔드 API

## 기술 스택

- Python 3.11+ / FastAPI
- PostgreSQL / SQLAlchemy (Async)
- Redis
- uv (패키지 관리)

## 프로젝트 구조

```
app/
├── api/v1/
│   ├── endpoints/     # API 엔드포인트
│   └── deps.py        # 의존성 (인증 등)
├── core/              # 설정, DB, 보안
├── models/            # SQLAlchemy 모델
├── schemas/           # Pydantic 스키마
├── services/          # 비즈니스 로직
└── main.py
```

## 로컬 실행

```bash
# 의존성 설치
uv sync

# DB/Redis 실행
docker-compose up -d

# 서버 실행
uv run uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Docs: http://localhost:8000/api/docs
