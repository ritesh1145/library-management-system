-- Library Management System - Common Operations

-- Add a new book
INSERT INTO books (title, author, isbn, publication_year, category, shelf_location)
VALUES ('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565', 1925, 'Fiction', 'A-12');

-- Add a new member
INSERT INTO members (first_name, last_name, email, phone, address)
VALUES ('John', 'Doe', 'john.doe@example.com', '555-123-4567', '123 Main St, Anytown, USA');

-- Borrow a book
-- Step 1: Create a new loan record
INSERT INTO loans (book_id, member_id, due_date)
VALUES (1, 1, datetime('now', '+14 days'));
-- Step 2: Update book status
UPDATE books SET status = 'Borrowed' WHERE book_id = 1;

-- Return a book
-- Step 1: Update loan record
UPDATE loans 
SET return_date = CURRENT_TIMESTAMP, 
    status = 'Returned'
WHERE book_id = 1 AND member_id = 1 AND return_date IS NULL;
-- Step 2: Update book status
UPDATE books SET status = 'Available' WHERE book_id = 1;

-- Calculate fine for overdue book
UPDATE loans
SET fine_amount = (julianday(CURRENT_TIMESTAMP) - julianday(due_date)) * 0.50, -- $0.50 per day
    status = 'Overdue'
WHERE due_date < CURRENT_TIMESTAMP AND return_date IS NULL;

-- Record payment of a fine
UPDATE fines
SET payment_status = 'Paid',
    payment_date = CURRENT_TIMESTAMP
WHERE fine_id = 1;

-- Search for books by title
SELECT * FROM books WHERE title LIKE '%gatsby%';

-- Search for books by author
SELECT * FROM books WHERE author LIKE '%fitzgerald%';

-- View all books borrowed by a member
SELECT b.title, b.author, l.loan_date, l.due_date
FROM loans l
JOIN books b ON l.book_id = b.book_id
WHERE l.member_id = 1 AND l.status = 'Borrowed';

-- List all overdue books
SELECT b.title, b.author, m.first_name, m.last_name, 
       l.due_date, 
       julianday(CURRENT_TIMESTAMP) - julianday(l.due_date) as days_overdue,
       l.fine_amount
FROM loans l
JOIN books b ON l.book_id = b.book_id
JOIN members m ON l.member_id = m.member_id
WHERE l.due_date < CURRENT_TIMESTAMP AND l.return_date IS NULL;

-- Reserve a book
INSERT INTO reservations (book_id, member_id, expiry_date)
VALUES (1, 2, datetime('now', '+7 days'));

-- Cancel a reservation
UPDATE reservations
SET status = 'Cancelled'
WHERE reservation_id = 1;

-- Extend/renew a loan
UPDATE loans
SET due_date = datetime(due_date, '+14 days')
WHERE loan_id = 1;

-- Get member borrowing history
SELECT b.title, l.loan_date, l.return_date, 
       CASE 
           WHEN l.return_date IS NULL AND l.due_date < CURRENT_TIMESTAMP THEN 'Overdue'
           WHEN l.return_date IS NULL THEN 'Borrowed'
           ELSE 'Returned'
       END as status
FROM loans l
JOIN books b ON l.book_id = b.book_id
WHERE l.member_id = 1
ORDER BY l.loan_date DESC;

-- Get library statistics
SELECT 
    (SELECT COUNT(*) FROM books) as total_books,
    (SELECT COUNT(*) FROM books WHERE status = 'Available') as available_books,
    (SELECT COUNT(*) FROM books WHERE status = 'Borrowed') as borrowed_books,
    (SELECT COUNT(*) FROM members) as total_members,
    (SELECT COUNT(*) FROM loans WHERE return_date IS NULL) as active_loans,
    (SELECT COUNT(*) FROM loans WHERE due_date < CURRENT_TIMESTAMP AND return_date IS NULL) as overdue_loans,
    (SELECT SUM(fine_amount) FROM loans) as total_fines;

-- Update member information
UPDATE members
SET phone = '555-987-6543',
    email = 'john.newemail@example.com'
WHERE member_id = 1;

-- Deactivate a member
UPDATE members
SET membership_status = 'Suspended'
WHERE member_id = 1;

-- Add staff member
INSERT INTO staff (first_name, last_name, email, phone, role, username, password_hash)
VALUES ('Admin', 'User', 'admin@library.com', '555-111-2222', 'Librarian', 'admin', 
        'hashed_password_here'); -- In a real system, use proper password hashing

-- Most popular books (most borrowed)
SELECT b.title, b.author, COUNT(l.loan_id) as borrow_count
FROM books b
JOIN loans l ON b.book_id = l.book_id
GROUP BY b.book_id
ORDER BY borrow_count DESC
LIMIT 10; 