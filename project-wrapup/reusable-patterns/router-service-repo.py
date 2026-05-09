"""
## 용도
FastAPI Router → Service → Repository 3계층 분리 패턴.
테스트 용이성과 관심사 분리를 동시에 달성. 수정 필요 (모델/스키마 교체).

## 언제 쓰는가
FastAPI 프로젝트에서 API 코드가 10개 이상의 엔드포인트를 가질 때.
비즈니스 로직과 DB 접근을 분리하여 단위 테스트를 쉽게 하고 싶을 때.

## 전제조건
- FastAPI + SQLAlchemy 설정 완료
- Pydantic 스키마 정의 (request/response 모델)

## 의존성
- fastapi: Depends, APIRouter
- sqlalchemy.orm: Session
- pydantic: BaseModel (스키마)

## 통합 포인트
- repositories/ 디렉토리: 순수 함수, db 세션 첫 인자, flush만 수행
- services/ 디렉토리: repository 조합 + 트랜잭션(commit/rollback) 관리
- routers/ 디렉토리: DI로 서비스 주입, Pydantic response_model 직렬화
- 이 패턴으로 874개 테스트 달성 (프로젝트 실적)

## 주의사항
- Repository는 commit 금지 — flush만 수행. commit 책임은 Service에
- Router에 비즈니스 로직 작성 금지 — Router는 요청/응답 변환만
- Service에서 직접 db.query() 사용 금지 — Repository를 통해서만

## 출처
stock-dashboard/backend/api/repositories/user_repo.py
stock-dashboard/backend/api/services/auth_service.py
stock-dashboard/backend/api/routers/auth.py
"""

# --- Repository (함수형) ---
# flush만 수행 → 호출 측에서 commit 관리
def create_user(db, *, email: str, password_hash: str, nickname: str | None = None):
    user = User(email=email, password_hash=password_hash, nickname=nickname)
    db.add(user)
    db.flush()
    return user

def get_by_id(db, user_id):
    return db.query(User).filter(User.id == user_id).first()

def delete_user(db, user_id):
    db.query(User).filter(User.id == user_id).delete()
    db.flush()


# --- Service ---
# 비즈니스 로직 + 트랜잭션
def signup(db, *, email, password, nickname=None):
    existing = user_repo.get_by_email(db, email)
    if existing:
        raise HTTPException(409, "Email already registered")
    hashed = hash_password(password)
    user = user_repo.create_user(db, email=email, password_hash=hashed, nickname=nickname)
    db.commit()
    return user


# --- Router ---
# 요청/응답 변환 + DI
# @router.post("/signup", response_model=UserResponse, status_code=201)
# def signup(body: SignupRequest, db: Session = Depends(get_db)):
#     user = auth_service.signup(db, email=body.email, password=body.password)
#     return UserResponse.model_validate(user)
