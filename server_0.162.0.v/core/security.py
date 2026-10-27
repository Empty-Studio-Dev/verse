from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

"""
the hashing process works 
by hashing an exact copy 
of the password upon login 
and comparing the two hashes
if they match the user is 
granted access
"""

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)