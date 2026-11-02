from models import User
from fastapi import Depends, HTTPException, status, APIRouter
from database import get_db
from schemas import CreateUser, UserOut, UpdateUserBase
from sqlalchemy.orm import Session
from core import hash
from core import get_current_user

router = APIRouter(
    prefix = "/users"
)

# create user and hash password if all data complited
@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_user(user: CreateUser, db: Session = Depends(get_db)):
    hashed_password = hash(user.password)
    user.password = hashed_password

    new_user = User(name=user.name, email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.delete(current_user) 
    db.commit()
    return None

@router.patch("/me", status_code=status.HTTP_200_OK, response_model=UserOut)
def update_my_information(payload: UpdateUserBase, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user

