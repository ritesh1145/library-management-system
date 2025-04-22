from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import sqlite3
import os
import json
import time
from forms import MemberForm, LoanForm
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'library_management_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_NAME = 'library.db'

def get_db_connection():
    """Connect to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Initialize the database if it doesn't exist."""
    if not os.path.exists(DB_NAME):
        conn = get_db_connection()
        with open('database_schema.sql', 'r') as f:
            schema_script = f.read()
        conn.executescript(schema_script)
        conn.commit()
        conn.close()
        print("Database initialized successfully.")
        
        # Add some sample data
        add_sample_data()

def add_sample_data():
    """Add sample books and members to the database."""
    conn = get_db_connection()
    
    # Sample books
    books = [
        ('To Kill a Mockingbird', 'Harper Lee', '9780061120084', 1960, 'Fiction', 'A-1'),
        ('1984', 'George Orwell', '9780451524935', 1949, 'Fiction', 'A-2'),
        ('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565', 1925, 'Fiction', 'A-3'),
        ('Pride and Prejudice', 'Jane Austen', '9780141439518', 1813, 'Classic', 'B-1'),
        ('The Hobbit', 'J.R.R. Tolkien', '9780547928227', 1937, 'Fantasy', 'B-2')
    ]
    
    for book in books:
        conn.execute(
            """INSERT INTO books (title, author, isbn, publication_year, category, shelf_location)
               VALUES (?, ?, ?, ?, ?, ?)""",
            book
        )
    
    # Sample members
    members = [
        ('John', 'Doe', 'john.doe@example.com', '555-123-4567', '123 Main St, Anytown'),
        ('Jane', 'Smith', 'jane.smith@example.com', '555-987-6543', '456 Oak St, Othertown'),
        ('Bob', 'Johnson', 'bob.johnson@example.com', '555-555-5555', '789 Pine St, Somewhere')
    ]
    
    for member in members:
        conn.execute(
            """INSERT INTO members (first_name, last_name, email, phone, address)
               VALUES (?, ?, ?, ?, ?)""",
            member
        )
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Render the homepage."""
    return render_template('index.html')

# Books
@app.route('/books')
def books():
    """Display all books."""
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    return render_template('books.html', books=books)

@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    """Add a new book."""
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        publication_year = request.form['publication_year']
        category = request.form['category']
        shelf_location = request.form['shelf_location']
        
        conn = get_db_connection()
        
        # Try to add the book, if it fails due to duplicate ISBN, modify the ISBN and try again
        try:
            conn.execute(
                """INSERT INTO books (title, author, isbn, publication_year, category, shelf_location)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (title, author, isbn, publication_year, category, shelf_location)
            )
            conn.commit()
            flash('Book added successfully', 'success')
        except sqlite3.IntegrityError:
            # If there's a duplicate ISBN, add a timestamp to make it unique
            modified_isbn = f"{isbn}_{int(time.time())}"
            conn.execute(
                """INSERT INTO books (title, author, isbn, publication_year, category, shelf_location)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (title, author, modified_isbn, publication_year, category, shelf_location)
            )
            conn.commit()
            flash(f'Book added with modified ISBN: {modified_isbn}', 'success')
        
        conn.close()
        return redirect(url_for('books'))
        
    return render_template('add_book.html')

@app.route('/books/search')
def search_books():
    """Search for books."""
    query = request.args.get('query', '')
    search_by = request.args.get('search_by', 'title')
    
    if not query:
        return redirect(url_for('books'))
    
    conn = get_db_connection()
    
    if search_by == 'title':
        books = conn.execute("SELECT * FROM books WHERE title LIKE ?", (f'%{query}%',)).fetchall()
    elif search_by == 'author':
        books = conn.execute("SELECT * FROM books WHERE author LIKE ?", (f'%{query}%',)).fetchall()
    elif search_by == 'isbn':
        books = conn.execute("SELECT * FROM books WHERE isbn LIKE ?", (f'%{query}%',)).fetchall()
    else:
        books = []
    
    conn.close()
    
    return render_template('books.html', books=books, search_query=query, search_by=search_by)

# Members
@app.route('/members')
def members():
    """Display all members."""
    conn = get_db_connection()
    members = conn.execute('SELECT * FROM members').fetchall()
    conn.close()
    return render_template('members.html', members=members)

@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    """Add a new member."""
    form = MemberForm()
    
    if form.validate_on_submit():
        # Handle form submission
        first_name = form.name.data.split()[0] if form.name.data and ' ' in form.name.data else form.name.data
        last_name = ' '.join(form.name.data.split()[1:]) if form.name.data and ' ' in form.name.data else ''
        email = form.email.data
        phone = form.phone.data
        address = form.address.data
        
        conn = get_db_connection()
        conn.execute(
            """INSERT INTO members (first_name, last_name, email, phone, address)
               VALUES (?, ?, ?, ?, ?)""",
            (first_name, last_name, email, phone, address)
        )
        conn.commit()
        conn.close()
        
        flash('Member added successfully', 'success')
        return redirect(url_for('members'))
        
    return render_template('add_member.html', form=form)

@app.route('/members/<int:member_id>')
def member_details(member_id):
    """Display member details and loans."""
    conn = get_db_connection()
    member = conn.execute('SELECT * FROM members WHERE member_id = ?', (member_id,)).fetchone()
    
    # Get active loans
    loans = conn.execute(
        """SELECT b.book_id, b.title, b.author, l.loan_date, l.due_date, l.status, l.fine_amount
           FROM loans l
           JOIN books b ON l.book_id = b.book_id
           WHERE l.member_id = ? AND l.return_date IS NULL
           ORDER BY l.due_date""",
        (member_id,)
    ).fetchall()
    
    # Get loan history
    history = conn.execute(
        """SELECT b.title, b.author, l.loan_date, l.return_date, l.status, l.fine_amount
           FROM loans l
           JOIN books b ON l.book_id = b.book_id
           WHERE l.member_id = ? AND l.return_date IS NOT NULL
           ORDER BY l.loan_date DESC""",
        (member_id,)
    ).fetchall()
    
    conn.close()
    
    if not member:
        flash('Member not found', 'error')
        return redirect(url_for('members'))
        
    return render_template('member_details.html', member=member, loans=loans, history=history)

# Loans
@app.route('/loans')
def loans():
    """Display all active loans."""
    conn = get_db_connection()
    active_loans = conn.execute(
        """SELECT l.loan_id, b.title, b.author, m.first_name, m.last_name, l.loan_date, l.due_date, l.status, l.fine_amount
           FROM loans l
           JOIN books b ON l.book_id = b.book_id
           JOIN members m ON l.member_id = m.member_id
           WHERE l.return_date IS NULL
           ORDER BY l.due_date"""
    ).fetchall()
    conn.close()
    return render_template('loans.html', loans=active_loans)

@app.route('/loans/add', methods=['GET', 'POST'])
def add_loan():
    """Check out a book to a member."""
    form = LoanForm()
    
    # Get list of all books and members, not just available ones
    conn = get_db_connection()
    all_books = conn.execute("SELECT book_id, title, author, isbn FROM books").fetchall()
    all_members = conn.execute("SELECT member_id, first_name, last_name, membership_status FROM members").fetchall()
    
    # Populate form choices with all books, not just available ones
    form.book_id.choices = [(book['book_id'], f"{book['title']} by {book['author']} (ISBN: {book['isbn']})") for book in all_books]
    form.member_id.choices = [(member['member_id'], f"{member['first_name']} {member['last_name']} ({member['membership_status']})") for member in all_members]
    
    # Default dates
    today = datetime.now().date()
    form.issue_date.data = form.issue_date.data or today
    form.due_date.data = form.due_date.data or (today + timedelta(days=30))  # Extended to 30 days
    
    if form.validate_on_submit():
        book_id = form.book_id.data
        member_id = form.member_id.data
        issue_date = form.issue_date.data
        due_date = form.due_date.data
        notes = form.notes.data
        
        # Add loan record regardless of book status
        conn.execute(
            """INSERT INTO loans (book_id, member_id, issue_date, due_date, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (book_id, member_id, issue_date, due_date, notes)
        )
        
        # Update book status to 'Borrowed'
        conn.execute("UPDATE books SET status = 'Borrowed' WHERE book_id = ?", (book_id,))
        
        conn.commit()
        conn.close()
        
        flash('Book checked out successfully', 'success')
        return redirect(url_for('loans'))
    
    conn.close()
    return render_template('add_loan.html', form=form, books=all_books, members=all_members, today=today.strftime('%Y-%m-%d'), default_due_date=(today + timedelta(days=30)).strftime('%Y-%m-%d'))

@app.route('/loans/return', methods=['POST'])
def return_book():
    """Return a borrowed book."""
    loan_id = request.form['loan_id']
    
    conn = get_db_connection()
    
    # Get loan details
    loan = conn.execute(
        """SELECT loan_id, book_id, member_id, due_date
           FROM loans
           WHERE loan_id = ? AND return_date IS NULL""",
        (loan_id,)
    ).fetchone()
    
    if not loan:
        flash('Loan not found or already returned', 'error')
        conn.close()
        return redirect(url_for('loans'))
    
    # Calculate fine if overdue
    due_date = datetime.strptime(loan['due_date'], '%Y-%m-%d %H:%M:%S')
    now = datetime.now()
    
    fine_amount = 0
    if now > due_date:
        days_overdue = (now - due_date).days
        fine_amount = days_overdue * 0.50  # $0.50 per day
    
    # Update loan record
    conn.execute(
        """UPDATE loans
           SET return_date = ?, status = 'Returned', fine_amount = ?
           WHERE loan_id = ?""",
        (now.strftime('%Y-%m-%d %H:%M:%S'), fine_amount, loan_id)
    )
    
    # Update book status
    conn.execute(
        """UPDATE books SET status = 'Available'
           WHERE book_id = ?""",
        (loan['book_id'],)
    )
    
    conn.commit()
    conn.close()
    
    msg = "Book returned successfully."
    if fine_amount > 0:
        msg += f" Fine for overdue: ${fine_amount:.2f}"
    
    flash(msg, 'success')
    return redirect(url_for('loans'))

# Overdue books
@app.route('/overdue')
def overdue():
    """Display all overdue books."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    overdue_books = conn.execute(
        """SELECT l.loan_id, b.title, b.author, m.first_name, m.last_name, l.due_date, 
                  julianday(?) - julianday(l.due_date) as days_overdue,
                  (julianday(?) - julianday(l.due_date)) * 0.50 as fine_amount
           FROM loans l
           JOIN books b ON l.book_id = b.book_id
           JOIN members m ON l.member_id = m.member_id
           WHERE l.due_date < ? AND l.return_date IS NULL""",
        (now, now, now)
    ).fetchall()
    
    # Add data for the charts
    # Membership type data (placeholder data since we don't have real data)
    membership_type_data = [5, 3, 8, 2]  # Student, Faculty, Standard, Premium
    
    # Days overdue data
    days_overdue_data = [0, 0, 0, 0]  # 1-7 days, 8-14 days, 15-30 days, 31+ days
    for book in overdue_books:
        days = int(book['days_overdue'])
        if days <= 7:
            days_overdue_data[0] += 1
        elif days <= 14:
            days_overdue_data[1] += 1
        elif days <= 30:
            days_overdue_data[2] += 1
        else:
            days_overdue_data[3] += 1
    
    # Overdue trend data (last 6 weeks)
    # In a real application, this would be calculated from actual data
    time_labels = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"]
    overdue_trend_data = [3, 5, 2, 7, 4, 6]  # Sample data
    
    # Frequent overdue members (sample data)
    frequent_overdue_members = [
        {'name': 'John Doe', 'membership_type': 'Standard', 'overdue_count': 3, 'total_fines': 12.50},
        {'name': 'Jane Smith', 'membership_type': 'Premium', 'overdue_count': 2, 'total_fines': 5.00},
        {'name': 'Bob Johnson', 'membership_type': 'Student', 'overdue_count': 1, 'total_fines': 2.50}
    ]
    
    conn.close()
    
    return render_template('overdue.html', 
                          overdue=overdue_books, 
                          membership_type_data=membership_type_data,
                          days_overdue_data=days_overdue_data,
                          time_labels=time_labels,
                          overdue_trend_data=overdue_trend_data,
                          frequent_overdue_members=frequent_overdue_members)

# API endpoints for AJAX
@app.route('/api/stats')
def api_stats():
    """Get library statistics in JSON format."""
    conn = get_db_connection()
    
    stats = conn.execute(
        """SELECT 
               (SELECT COUNT(*) FROM books) as total_books,
               (SELECT COUNT(*) FROM books WHERE status = 'Available') as available_books,
               (SELECT COUNT(*) FROM books WHERE status = 'Borrowed') as borrowed_books,
               (SELECT COUNT(*) FROM members) as total_members,
               (SELECT COUNT(*) FROM loans WHERE return_date IS NULL) as active_loans,
               (SELECT COUNT(*) FROM loans WHERE due_date < CURRENT_TIMESTAMP AND return_date IS NULL) as overdue_loans,
               (SELECT SUM(fine_amount) FROM loans) as total_fines"""
    ).fetchone()
    
    conn.close()
    
    stats_dict = dict(stats)
    if stats_dict['total_fines'] is None:
        stats_dict['total_fines'] = 0
    
    return jsonify(stats_dict)

@app.route('/dashboard')
def dashboard():
    """Display the library dashboard with statistics."""
    return render_template('dashboard.html')

@app.route('/overdue/reminder/all')
def overdue_reminder_all():
    """Send reminders to all members with overdue books."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    overdue_loans = conn.execute(
        """SELECT l.loan_id, b.title, m.first_name, m.last_name, m.email, l.due_date
           FROM loans l
           JOIN books b ON l.book_id = b.book_id
           JOIN members m ON l.member_id = m.member_id
           WHERE l.due_date < ? AND l.return_date IS NULL""",
        (now,)
    ).fetchall()
    conn.close()
    
    # In a real application, you would send actual emails here
    message = f"Reminder emails would be sent to {len(overdue_loans)} members with overdue books."
    flash(message, 'success')
    return redirect(url_for('overdue'))

@app.route('/overdue/export')
def export_overdue():
    """Export overdue books list as CSV."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    overdue_books = conn.execute(
        """SELECT b.title, b.author, m.first_name, m.last_name, m.email, l.due_date,
                  julianday(?) - julianday(l.due_date) as days_overdue,
                  (julianday(?) - julianday(l.due_date)) * 0.50 as fine_amount
           FROM loans l
           JOIN books b ON l.book_id = b.book_id
           JOIN members m ON l.member_id = m.member_id
           WHERE l.due_date < ? AND l.return_date IS NULL""",
        (now, now, now)
    ).fetchall()
    conn.close()
    
    # In a real application, you would generate a CSV file
    message = f"Export feature would generate a CSV with {len(overdue_books)} overdue books."
    flash(message, 'success')
    return redirect(url_for('overdue'))

@app.route('/loan/<int:loan_id>/remind')
def send_reminder(loan_id):
    """Send reminder for a specific overdue loan."""
    conn = get_db_connection()
    loan = conn.execute(
        """SELECT l.loan_id, b.title, m.first_name, m.last_name, m.email, l.due_date
           FROM loans l
           JOIN books b ON l.book_id = b.book_id
           JOIN members m ON l.member_id = m.member_id
           WHERE l.loan_id = ?""",
        (loan_id,)
    ).fetchone()
    conn.close()
    
    if not loan:
        flash('Loan not found', 'error')
        return redirect(url_for('overdue'))
    
    # In a real application, you would send an actual email here
    message = f"Reminder would be sent to {loan['first_name']} {loan['last_name']} about overdue book: {loan['title']}"
    flash(message, 'success')
    return redirect(url_for('overdue'))

@app.route('/loan/<int:loan_id>/extend', methods=['GET', 'POST'])
def extend_loan(loan_id):
    """Extend the due date for a loan."""
    conn = get_db_connection()
    loan = conn.execute("SELECT * FROM loans WHERE loan_id = ?", (loan_id,)).fetchone()
    
    if not loan:
        flash('Loan not found', 'error')
        conn.close()
        return redirect(url_for('overdue'))
    
    if request.method == 'POST':
        # Extend loan by 7 days
        current_due_date = datetime.strptime(loan['due_date'], '%Y-%m-%d %H:%M:%S')
        new_due_date = current_due_date + timedelta(days=7)
        
        conn.execute(
            "UPDATE loans SET due_date = ? WHERE loan_id = ?",
            (new_due_date.strftime('%Y-%m-%d %H:%M:%S'), loan_id)
        )
        conn.commit()
        conn.close()
        
        flash('Loan period extended by 7 days', 'success')
        return redirect(url_for('overdue'))
    
    # For simplicity, extending by default without showing a form
    current_due_date = datetime.strptime(loan['due_date'], '%Y-%m-%d %H:%M:%S')
    new_due_date = current_due_date + timedelta(days=7)
    
    conn.execute(
        "UPDATE loans SET due_date = ? WHERE loan_id = ?",
        (new_due_date.strftime('%Y-%m-%d %H:%M:%S'), loan_id)
    )
    conn.commit()
    conn.close()
    
    flash('Loan period extended by 7 days', 'success')
    return redirect(url_for('overdue'))

@app.route('/loan/<int:loan_id>')
def view_loan(loan_id):
    """View details of a specific loan."""
    conn = get_db_connection()
    loan = conn.execute(
        """SELECT l.*, b.title, b.author, m.first_name, m.last_name
           FROM loans l
           JOIN books b ON l.book_id = b.book_id
           JOIN members m ON l.member_id = m.member_id
           WHERE l.loan_id = ?""",
        (loan_id,)
    ).fetchone()
    conn.close()
    
    if not loan:
        flash('Loan not found', 'error')
        return redirect(url_for('overdue'))
    
    # In a real application, you would render a template with loan details
    flash(f"Viewing loan details for: {loan['title']} borrowed by {loan['first_name']} {loan['last_name']}", 'info')
    return redirect(url_for('overdue'))

@app.route('/book_statistics')
def book_statistics():
    """Display statistics about books in the library."""
    conn = get_db_connection()
    
    # Get data for various book statistics
    stats = conn.execute(
        """SELECT 
               (SELECT COUNT(*) FROM books) as total_books,
               (SELECT COUNT(*) FROM books WHERE status = 'Available') as available_books,
               (SELECT COUNT(*) FROM books WHERE status = 'Borrowed') as borrowed_books,
               (SELECT COUNT(DISTINCT category) FROM books) as category_count"""
    ).fetchone()
    
    # Get book categories distribution
    categories = conn.execute(
        """SELECT category, COUNT(*) as count 
           FROM books 
           GROUP BY category 
           ORDER BY count DESC"""
    ).fetchall()
    
    # Get most borrowed books
    popular_books = conn.execute(
        """SELECT b.title, b.author, COUNT(l.loan_id) as borrow_count
           FROM books b
           JOIN loans l ON b.book_id = l.book_id
           GROUP BY b.book_id
           ORDER BY borrow_count DESC
           LIMIT 10"""
    ).fetchall()
    
    conn.close()
    
    return render_template('book_statistics.html', 
                          stats=stats, 
                          categories=categories, 
                          popular_books=popular_books)

@app.route('/member_statistics')
def member_statistics():
    """Display statistics about library members."""
    conn = get_db_connection()
    
    # Get general member statistics
    stats = conn.execute(
        """SELECT 
               (SELECT COUNT(*) FROM members) as total_members,
               (SELECT COUNT(DISTINCT membership_status) FROM members) as status_count"""
    ).fetchone()
    
    # Get membership status distribution
    membership_statuses = conn.execute(
        """SELECT membership_status, COUNT(*) as count 
           FROM members 
           GROUP BY membership_status 
           ORDER BY count DESC"""
    ).fetchall()
    
    # Get members with most loans
    active_members = conn.execute(
        """SELECT m.first_name, m.last_name, COUNT(l.loan_id) as loan_count
           FROM members m
           JOIN loans l ON m.member_id = l.member_id
           GROUP BY m.member_id
           ORDER BY loan_count DESC
           LIMIT 10"""
    ).fetchall()
    
    # Get members with overdue books
    members_with_overdue = conn.execute(
        """SELECT m.first_name, m.last_name, COUNT(l.loan_id) as overdue_count, SUM(l.fine_amount) as total_fines
           FROM members m
           JOIN loans l ON m.member_id = l.member_id
           WHERE l.due_date < datetime('now') AND l.return_date IS NULL
           GROUP BY m.member_id
           ORDER BY overdue_count DESC"""
    ).fetchall()
    
    conn.close()
    
    return render_template('member_statistics.html', 
                          stats=stats, 
                          membership_statuses=membership_statuses, 
                          active_members=active_members,
                          members_with_overdue=members_with_overdue)

@app.route('/generate_overdue_report', methods=['POST'])
def generate_overdue_report():
    """Generate a report of overdue books based on specified parameters."""
    report_type = request.form.get('report_type', 'summary')
    report_format = request.form.get('report_format', 'pdf')
    date_range = request.form.get('date_range', 'current')
    include_member_details = 'include_member_details' in request.form
    include_charts = 'include_charts' in request.form
    
    # This would normally generate an actual report file
    # For this demonstration, we'll just flash a message
    
    report_types = {
        'summary': 'Summary Report',
        'detailed': 'Detailed Report',
        'financial': 'Financial Impact Report'
    }
    
    report_formats = {
        'pdf': 'PDF',
        'excel': 'Excel',
        'csv': 'CSV'
    }
    
    date_ranges = {
        'current': 'Currently Overdue',
        'last_30': 'Last 30 Days',
        'last_90': 'Last 90 Days',
        'all_time': 'All Time'
    }
    
    flash(f"Generated a {report_types[report_type]} in {report_formats[report_format]} format for {date_ranges[date_range]} overdue books.", 'success')
    return redirect(url_for('overdue'))

# Initialize the database before the first request
@app.before_first_request
def before_first_request():
    init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 