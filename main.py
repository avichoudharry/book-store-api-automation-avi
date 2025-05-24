from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel  
from uuid import uuid4
import jwt
from passlib.context import CryptContext

app = FastAPI()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory stores (replace with a real database in production)
users_db = {} # Stores hashed passwords
books_db = {}

# JWT Configuration
SECRET_KEY = "mysecretkey_super_secure_and_long_random_string" # In production, load from environment variable
ALGORITHM = "HS256"

# OAuth2 Password Bearer (tokenUrl should point to your login endpoint)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login") # Corrected tokenUrl to /login

class UserCreate(BaseModel): # Renamed for clarity in signup
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class Book(BaseModel):
    title: str

class BookResponse(BaseModel): # Explicitly define all fields for clarity
    id: str
    title: str

# --- User Management Endpoints ---
@app.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate):
    if user.email in users_db:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    
    # Hash the password before storing
    hashed_password = pwd_context.hash(user.password)
    users_db[user.email] = hashed_password
    
    return {"message": "User created successfully"}

@app.post("/login", response_model=Token)
def login(username: str = Form(...), password: str = Form(...)):
    stored_hashed_password = users_db.get(username)
    
    if not stored_hashed_password or not pwd_context.verify(password, stored_hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token
    to_encode = {"sub": username}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": encoded_jwt, "token_type": "bearer"}

# --- Dependency to get current authenticated user ---
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        
        # In a real app, you might fetch the user from a database here
        if username not in users_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return username # Return the username (email)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- Book Endpoints ---
@app.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def add_book(book: Book, current_user_email: str = Depends(get_current_user)):
    """Adds a new book to the in-memory database."""
    book_id = str(uuid4())
    books_db[book_id] = book.title
    return BookResponse(id=book_id, title=book.title)

@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: str, current_user_email: str = Depends(get_current_user)):
    """Retrieves a book by its ID."""
    if book_id not in books_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return BookResponse(id=book_id, title=books_db[book_id])

@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: str, updated_book: Book, current_user_email: str = Depends(get_current_user)):
    """Updates an existing book."""
    if book_id not in books_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    books_db[book_id] = updated_book.title
    return BookResponse(id=book_id, title=updated_book.title)

@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: str, current_user_email: str = Depends(get_current_user)):
    """Deletes a book."""
    if book_id not in books_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    del books_db[book_id]
    return # 204 No Content should return an empty body