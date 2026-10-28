from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from models import User, PasswordResetToken
from schemas import ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest

from core import hash, verify, generate_reset_token, hash_reset_token, reset_token_expiry, get_current_user

from utils import send_password_reset_email

router = APIRouter(
    prefix="/users", tags=["Password"]
)

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(payload: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    generic_message = {
        "message": "If an account with that email exists, a reset link has been sent."
    }
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if not user:
        return generic_message

    # delete old token this user
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.user_id).delete()

    raw_token = generate_reset_token()
    reset_row = PasswordResetToken(user_id=user.user_id, token_hash=hash_reset_token(raw_token), expires_at=reset_token_expiry())
    db.add(reset_row)
    db.commit()

    # output mail in background, cleear token dont hash
    background_tasks.add_task(send_password_reset_email, user.email, raw_token)

    return generic_message

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_hash = hash_reset_token(payload.token)
    row = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    invalid = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    if not row:
        raise invalid

    expires_at = row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        db.delete(row)
        db.commit()
        raise invalid

    user = db.query(User).filter(User.user_id == row.user_id).first()
    if not user:
        raise invalid

    user.password = hash(payload.new_password)

    # delete all token this user 
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.user_id).delete()

    db.commit()
    return {"message": "Password has been reset successfully"}

@router.patch("/me/password", status_code=status.HTTP_200_OK)
def change_password(payload: ChangePasswordRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user = db.query(User).filter(User.user_id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not verify(payload.current_password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Current password is incorrect")

    user.password = hash(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}