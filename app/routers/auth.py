from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_admin_user, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.company import Company
from app.models.user import User, user_company
from app.schemas.user import Token, UserCreate
from app.schemas.user import User as UserSchema

router = APIRouter()


class RefreshToken(BaseModel):
    refresh_token: str


class UserCreateAdmin(UserCreate):
    role: Optional[str] = 'user'
    company_id: int


@router.post('/token', response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    refresh_token_expires = timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
    extra_data = {'name': user.name}
    access_token = create_access_token(
        subject=user.email,
        expires_delta=access_token_expires,
        extra_data=extra_data,
    )
    refresh_token = create_refresh_token(
        subject=user.email,
        expires_delta=refresh_token_expires,
        extra_data=extra_data,
    )
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer',
    }


invalidated_tokens = set()


@router.post('/refresh_token', response_model=Token)
def refresh_access_token(
    refresh_token: RefreshToken,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate refresh token',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    if refresh_token.refresh_token in invalidated_tokens:
        raise credentials_exception

    try:
        payload = jwt.decode(
            refresh_token.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        email: str = payload.get('sub')
        if email is None or email != current_user.email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    invalidated_tokens.add(refresh_token.refresh_token)

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = create_access_token(
        subject=current_user.email, expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(
        subject=current_user.email, expires_delta=timedelta(days=7)
    )

    return {
        'access_token': access_token,
        'refresh_token': new_refresh_token,
        'token_type': 'bearer',
    }


@router.post('/register', response_model=UserSchema)
def register_user(
    user: UserCreateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail='Email already registered')

    if user.role not in {'admin', 'user'}:
        raise HTTPException(
            status_code=400,
            detail='Invalid role. Must be either "admin" or "user"',
        )

    # Check if the company exists
    company = db.query(Company).filter(Company.id == user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')

    # Check if the current admin user has rights to this company
    admin_company = (
        db.query(user_company)
        .filter(
            user_company.c.user_id == current_user.id,
            user_company.c.company_id == user.company_id,
            user_company.c.role == 'admin',
        )
        .first()
    )
    if not admin_company:
        raise HTTPException(
            status_code=403,
            detail='You do not have admin rights for this company',
        )

    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email, hashed_password=hashed_password, name=user.name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Add user to user_company table with specified role and company
    db.execute(
        user_company.insert().values(
            user_id=new_user.id, company_id=user.company_id, role=user.role
        )
    )
    db.commit()

    return new_user
