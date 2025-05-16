from uuid import uuid4

# In-memory book storage
books_db = {}

class Book(BaseModel):
    title: str

class BookResponse(Book):
    id: str

@app.post("/books", response_model=BookResponse)
def add_book(book: Book, token: str = Depends(oauth2_scheme)):
    if not token.endswith("-token"):
        raise HTTPException(status_code=401, detail="Invalid token")
    book_id = str(uuid4())
    books_db[book_id] = book.title
    return {"id": book_id, "title": book.title}

@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: str, updated_book: Book, token: str = Depends(oauth2_scheme)):
    if not token.endswith("-token"):
        raise HTTPException(status_code=401, detail="Invalid token")
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    books_db[book_id] = updated_book.title
    return {"id": book_id, "title": updated_book.title}

@app.delete("/books/{book_id}")
def delete_book(book_id: str, token: str = Depends(oauth2_scheme)):
    if not token.endswith("-token"):
        raise HTTPException(status_code=401, detail="Invalid token")
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    del books_db[book_id]
    return {"message": "Book deleted successfully"}
