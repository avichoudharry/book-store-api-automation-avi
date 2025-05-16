const { test, expect, request } = require('@playwright/test');

test('Signup → Login → Add → Update → Delete Book', async () => {
  const apiContext = await request.newContext();

  const user = {
    email: 'avi@jk.com',
    password: 'avi123'
  };

  await apiContext.post('http://127.0.0.1:8000/signup', {
    data: JSON.stringify(user),
    headers: { 'Content-Type': 'application/json' }
  });

  const loginResponse = await apiContext.post('http://127.0.0.1:8000/login', {
    data: JSON.stringify(user),
    headers: { 'Content-Type': 'application/json' }
  });

  expect(loginResponse.status()).toBe(200);
  const loginData = await loginResponse.json();
  const token = loginData.access_token;

  const authContext = await request.newContext({
    extraHTTPHeaders: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  const newBook = { title: 'Test Book' };
  const addRes = await authContext.post('http://127.0.0.1:8000/books', {
    data: JSON.stringify(newBook)
  });

  expect(addRes.status()).toBe(200);
  const added = await addRes.json();
  const bookId = added.id;

  const updatedBook = { title: 'Test Book - Updated' };
  const updateRes = await authContext.put(`http://127.0.0.1:8000/books/${bookId}`, {
    data: JSON.stringify(updatedBook)
  });

  expect(updateRes.status()).toBe(200);

  const deleteRes = await authContext.delete(`http://127.0.0.1:8000/books/${bookId}`);
  expect(deleteRes.status()).toBe(200);
});
