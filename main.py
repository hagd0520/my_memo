import os
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Request
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
templates = Jinja2Templates(directory="templates")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(200))
    hashed_password = Column(String(512))
    
    
# 회원가입 시 데이터 검증
class UserCreate(BaseModel):
    username: str
    email: str
    password: str # 해시 전 패스워드
    
    
class UserLogin(BaseModel):
    username: str
    password: str # 해시 전 패스워드


class Memo(Base):
    __tablename__ = "memo"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    content = Column(String(1000))
    
    
class MemoCreate(BaseModel):
    title: str
    content: str
    
    
class MemoUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    
    
def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()
        
        
Base.metadata.create_all(bind=engine)


# 회원 가입
@app.post("/signup")
async def signup(signup_data: UserCreate, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(signup_data.password)
    new_user = User(
        username=signup_data.username, 
        email=signup_data.email, 
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Account reated successfully", "user_id": new_user.id}
    

# 로그인    
@app.post("/login")
async def login(request: Request, signin_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == signin_data.username).first()
    if user and verify_password(signin_data.password, user.hashed_password):
        request.session["username"] = user.username
        return {"message": "Logged in successfully"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    
# 로그아웃
@app.post("/logout")
async def logout(request: Request):
    request.session.pop("username", None)
    return {"message": "Logged out successfully"}


# 메모 생성
@app.post("/memos")
async def create_memo(memo: MemoCreate, db: Session = Depends(get_db)):
    new_memo = Memo(title=memo.title, content=memo.content)
    db.add(new_memo)
    db.commit()
    db.refresh(new_memo)
    return {"id": new_memo.id, "title": new_memo.title, "content": new_memo.content}


@app.get("/memos")
async def list_memos(db: Session = Depends(get_db)):
    memos = db.query(Memo).all()
    return [{"id": memo.id, "title": memo.title, "content": memo.content} for memo in memos]


@app.put("/memos/{memo_id}")
async def update_memo(memo_id: int, memo: MemoUpdate, db: Session = Depends(get_db)):
    db_memo = db.query(Memo).filter(Memo.id == memo_id).first()
    if db_memo is None:
        return {"error": "Memo not found"}

    if memo.title is not None:
        db_memo.title = memo.title
    
    if memo.content is not None:
        db_memo.content = memo.content
    
    db.commit()
    db.refresh(db_memo)
    return {"id": db_memo.id, "title": db_memo.title, "content": db_memo.content}


# 메모 삭제
@app.delete("/memos/{memo_id}")
async def delete_memo(memo_id:int, db: Session = Depends(get_db)):
    db_memo = db.query(Memo).filter(Memo.id == memo_id).first()
    
    if db_memo is None:
        return {"error": "Memo not found"}
    
    db.delete(db_memo)
    db.commit()
    
    return {"message": "Memo deleted"}


# 기존 라우트
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/about")
async def about():
    return {"message": "이것은 마이 메모 앱의 소개 페이지입니다."}