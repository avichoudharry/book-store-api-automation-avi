import pytest
import requests
import json # You might need this if you parse JSON manually, but requests.json() handles it

BASE_URL = "http://127.0.0.1:8000" # Ensure this matches your FastAPI server's address

@pytest.fixture(scope="module")
def get_token():
    """
    Fixture to obtain a valid access token. This fixture is used in tests that
    require authentication. It ensures that we get a fresh token for each test
    session, preventing tests from interfering with each other.
    """
    # Ensure the user exists before trying to log in
    user_signup_data = {"email": "testuser@example.com", "password": "testpassword"}
    requests.post(f"{BASE_URL}/signup", json=user_signup_data) # Sign up the user first (allows 409 if exists)

    # Login using form-encoded data
    user_login_data = {"username": "testuser@example.com", "password": "testpassword"}
    response = requests.post(f"{BASE_URL}/login", data=user_login_data) # Use 'data' for form-encoded
    
    # Assert login success
    assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
    
    token_data = response.json()
    return token_data["access_token"]


def test_signup_login_and_book_flow():
    """
    This test case tests the following end-to-end flow:
    1.  Sign up a new user.
    2.  Login with the new user using form data.
    3.  Add a book using the obtained token (expecting 201 Created).
    4.  Update the added book.
    5.  Delete the added book (expecting 204 No Content).
    """
    user_email = "flowtest@example.com"
    user_password = "flowpassword"
    user_data = {"email": user_email, "password": user_password}

    # 1. Sign up
    signup_response = requests.post(f"{BASE_URL}/signup", json=user_data)
    # Expect 201 if created, or 409 if already exists from a previous run
    assert signup_response.status_code in (201, 409), f"Signup failed: {signup_response.status_code} - {signup_response.text}"

    # 2. Login (using form-encoded data as per FastAPI's /login endpoint)
    login_data = {"username": user_email, "password": user_password}
    login_response = requests.post(f"{BASE_URL}/login", data=login_data)
    assert login_response.status_code == 200, f"Login failed: {login_response.status_code} - {login_response.text}"
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Add Book (expecting 201 Created)
    new_book = {"title": "Python Automation Book"}
    add_book_response = requests.post(f"{BASE_URL}/books", json=new_book, headers=headers)
    assert add_book_response.status_code == 201, f"Failed to add book: {add_book_response.status_code} - {add_book_response.text}"
    added_book = add_book_response.json()
    book_id = added_book["id"]
    assert added_book["title"] == "Python Automation Book"

    # 4. Update Book
    updated_book_data = {"title": "Updated Book Title"}
    update_book_response = requests.put(
        f"{BASE_URL}/books/{book_id}", json=updated_book_data, headers=headers
    )
    assert update_book_response.status_code == 200, f"Failed to update book: {update_book_response.status_code} - {update_book_response.text}"
    updated_book = update_book_response.json()
    assert updated_book["title"] == "Updated Book Title"

    # 5. Delete Book (expecting 204 No Content)
    delete_book_response = requests.delete(f"{BASE_URL}/books/{book_id}", headers=headers)
    assert delete_book_response.status_code == 204, f"Failed to delete book: {delete_book_response.status_code} - {delete_book_response.text}"
    # For 204 No Content, the response body should be empty
    assert delete_book_response.text == ""


def test_read_book(get_token):
    """
    This test case tests reading a book. It depends on the get_token fixture
    to get a valid authentication token.
    """
    headers = {"Authorization": f"Bearer {get_token}"}
    
    # Add a book first to ensure there's something to read
    new_book = {"title": "Readable Book"}
    add_response = requests.post(f"{BASE_URL}/books", json=new_book, headers=headers)
    assert add_response.status_code == 201, f"Failed to add book for read test: {add_response.text}"
    added_book = add_response.json()
    book_id = added_book["id"]

    # Read the book
    read_response = requests.get(f"{BASE_URL}/books/{book_id}", headers=headers)
    assert read_response.status_code == 200, f"Failed to read book: {read_response.text}"
    read_book_data = read_response.json()
    assert read_book_data["title"] == "Readable Book"


def test_read_nonexistent_book(get_token):
    """
    This test case tests reading a non-existent book. It verifies that the API
    returns the correct error status code and message.
    """
    headers = {"Authorization": f"Bearer {get_token}"}
    nonexistent_id = "nonexistent-book-id-12345" # Ensure this ID is truly unique/non-existent
    read_response = requests.get(f"{BASE_URL}/books/{nonexistent_id}", headers=headers)
    assert read_response.status_code == 404, f"Unexpected status for non-existent book: {read_response.status_code} - {read_response.text}"
    error_data = read_response.json()
    assert "Book not found" in error_data["detail"]


def test_add_book_unauthorized():
    """
    Tests that adding a book fails without a token.
    """
    new_book = {"title": "Unauthorized Book"}
    response = requests.post(f"{BASE_URL}/books", json=new_book)
    assert response.status_code == 401, f"Expected 401, got {response.status_code} - {response.text}"
    assert "not authenticated" in response.json().get("detail", "").lower()
 # Check for common unauthorized messages


def test_add_book_invalid_token():
    """
    Tests that adding a book fails with an invalid token.
    """
    new_book = {"title": "Invalid Token Book"}
    headers = {"Authorization": "Bearer invalid_jwt_token_string"}
    response = requests.post(f"{BASE_URL}/books", json=new_book, headers=headers)
    assert response.status_code == 401, f"Expected 401, got {response.status_code} - {response.text}"
    assert "could not validate credentials" in response.json().get("detail", "").lower()


def test_login_invalid_credentials():
    """
    Tests that login fails with incorrect username/password.
    """
    invalid_login_data = {"username": "nonexistent@example.com", "password": "wrongpassword"}
    response = requests.post(f"{BASE_URL}/login", data=invalid_login_data)
    assert response.status_code == 401, f"Expected 401, got {response.status_code} - {response.text}"
    assert "incorrect email or password" in response.json().get("detail", "").lower()