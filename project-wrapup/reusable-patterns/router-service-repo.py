"""
## 용도
FastAPI Router → Service → Repository 3계층 패턴.
Router: 요청/응답 변환. Service: 비즈니스 로직. Repository: DB 접근.

## 사용법
1. Repository: 순수 함수, db 세션을 첫 인자로 받음. flush만 (commit은 Service에서)
2. Service: Repository 조합 + 트랜잭션 관리 (commit/rollback)
3. Router: Depends()로 DI, Pydantic response_model로 직렬화

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
