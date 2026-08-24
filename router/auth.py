from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from models import User
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from typing import Annotated, Optional
from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt
from datetime import timedelta, datetime, timezone

router = APIRouter()

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
OAuth2_bearer = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY = '47ebe062c5d7f8c6b3ac8bdd27d32e4a52a0f79f0191b3dbb6895333577a8b00'
ALGORITHM = 'HS256'

def authenticate_user(username, password, db):
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        return False
    if bcrypt_context.verify(password, user.hash_password):
        return user
    return False

def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: Annotated[str, Depends(OAuth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        role: str = payload.get('role')

        if username is None or user_id is None:
            raise HTTPException(status_code=404, detail='User not found')

        return {'username': username, 'id': user_id, 'role': role}

    except:
        raise HTTPException(status_code=404, detail='User not found')

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.clsoe()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class CreateUser(BaseModel):
    username : str
    email : str
    password : str

class UpdateUser(BaseModel):
    username : Optional[str] = Field(default=None)
    email : Optional[str] = Field(default=None)

class UpdatePassword(BaseModel):
    current_password : str
    new_password : str

@router.post('/createuser')
def create_users(db : db_dependency, new_user : CreateUser):

    user_model = User(
        username = new_user.username,
        email = new_user.email,
        hash_password = bcrypt_context.hash(new_user.password)
    )

    db.add(user_model)
    db.commit()
    return JSONResponse(status_code=201, content={'message': 'User created successfully'})

@router.post('/login')
def login_user(db : db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):

    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    token = create_access_token(user.username, user.id, timedelta(minutes=30))

    return {'access_token': token, 'token_type': 'bearer'}

@router.put('/edituser')
def update_user(user: user_dependency, db: db_dependency, update_user: UpdateUser):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    user = db.query(User).filter(User.id == user.get('id')).first()
    update_data = update_user.model_dump(exclude_unset=True)

    for key, value in update_data.itmes():
        setattr(user, key, value)

    db.commit()

    return JSONResponse(status_code=200, content={'message': 'User updated successfully'})

@router.put('/passwordchange')
def update_password(user: user_dependency, db: db_dependency, update_password: UpdatePassword):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    user = db.query(User).filter(User.id == user.get('id')).first()

    if not bcrypt_context.verify(update_password.current_password, user.hash_password):
        raise HTTPException(status_code=401, detail='Wrong Password')

    user.hash_password = bcrypt_context(update_password.new_password)

    db.add(user)
    db.commit()

    return JSONResponse(status_code=200, content={'message': 'Password updated successfully'})