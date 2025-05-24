const express = require('express');
const bodyParser = require('body-parser');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = 8000;
const JWT_SECRET = 'secret123';

app.use(bodyParser.json());

const users = {};
const books = {};

// Signup
app.post('/signup', (req, res) => {
  const { email, password } = req.body;
  if (users[email]) return res.status(409).json({ message: 'User already exists' });
  users[email] = password;
  res.status(201).json({ message: 'User registered' });
});

// Login
app.post('/login', (req, res) => {
  const { email, password } = req.body;
  if (users[email] !== password) return res.status(401).json({ message: 'Invalid credentials' });
  const token = jwt.sign({ email }, JWT_SECRET, { expiresIn: '1h' });
  res.json({ token });
});

// Auth Middleware
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  
  if (!token) return res.status(403).json({ message: 'No token provided' });

  jwt.verify(token, SECRET_KEY, (err, user) => {
    if (err) return res.status(403).json({ message: 'Invalid token' });
    req.user = user;
    next();
  });
}


// Add Book
app.post('/books', authenticateToken, (req, res) => {
  const id = uuidv4();
  const title = req.body.title;
  books[id] = title;
  res.json({ id, title });
});

// Update Book
app.put('/books/:id', authenticateToken, (req, res) => {
  const { id } = req.params;
  if (!books[id]) return res.status(404).json({ message: 'Book not found' });
  books[id] = req.body.title;
  res.json({ id, title: books[id] });
});

// Delete Book
app.delete('/books/:id', authenticateToken, (req, res) => {
  const { id } = req.params;
  if (!books[id]) return res.status(404).json({ message: 'Book not found' });
  delete books[id];
  res.json({ message: 'Book deleted' });
});

app.listen(PORT, () => {
  console.log(`Backend running at http://localhost:${PORT}`);
});
