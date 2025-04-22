#!/usr/bin/env python3
import sqlite3
import os
import datetime
from tabulate import tabulate

class LibraryManagementSystem:
    def __init__(self, db_name='library.db'):
        """Initialize the library management system with the database."""
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        
        # Create database if it doesn't exist
        if not os.path.exists(db_name):
            self.setup_database()
        else:
            self.connect()
    
    def connect(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self.cursor = self.conn.cursor()
    
    def setup_database(self):
        """Create the database and tables if they don't exist."""
        self.connect()
        
        # Read SQL schema from file
        with open('database_schema.sql', 'r') as f:
            schema_script = f.read()
            
        # Execute schema script
        self.cursor.executescript(schema_script)
        self.conn.commit()
        print("Database initialized successfully.")
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def add_book(self, title, author, isbn, publication_year, category, shelf_location):
        """Add a new book to the library."""
        try:
            self.cursor.execute(
                """INSERT INTO books (title, author, isbn, publication_year, category, shelf_location)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (title, author, isbn, publication_year, category, shelf_location)
            )
            self.conn.commit()
            return True, "Book added successfully."
        except sqlite3.Error as e:
            return False, f"Error adding book: {e}"
    
    def add_member(self, first_name, last_name, email, phone, address):
        """Add a new member to the library."""
        try:
            self.cursor.execute(
                """INSERT INTO members (first_name, last_name, email, phone, address)
                   VALUES (?, ?, ?, ?, ?)""",
                (first_name, last_name, email, phone, address)
            )
            self.conn.commit()
            return True, "Member added successfully."
        except sqlite3.Error as e:
            return False, f"Error adding member: {e}"
    
    def search_books(self, search_term, search_by='title'):
        """Search for books by title, author, or ISBN."""
        try:
            if search_by == 'title':
                self.cursor.execute("SELECT * FROM books WHERE title LIKE ?", (f'%{search_term}%',))
            elif search_by == 'author':
                self.cursor.execute("SELECT * FROM books WHERE author LIKE ?", (f'%{search_term}%',))
            elif search_by == 'isbn':
                self.cursor.execute("SELECT * FROM books WHERE isbn LIKE ?", (f'%{search_term}%',))
            else:
                return False, "Invalid search parameter"
            
            books = self.cursor.fetchall()
            if not books:
                return False, "No books found."
            
            # Convert result to list of dictionaries
            result = []
            for book in books:
                book_dict = dict(book)
                result.append(book_dict)
            
            return True, result
        except sqlite3.Error as e:
            return False, f"Error searching books: {e}"
    
    def checkout_book(self, book_id, member_id, days=14):
        """Check out a book to a member."""
        try:
            # Check if book is available
            self.cursor.execute("SELECT status FROM books WHERE book_id = ?", (book_id,))
            book = self.cursor.fetchone()
            
            if not book:
                return False, "Book not found."
            
            if book['status'] != 'Available':
                return False, f"Book is not available. Current status: {book['status']}"
            
            # Check if member exists
            self.cursor.execute("SELECT member_id FROM members WHERE member_id = ?", (member_id,))
            member = self.cursor.fetchone()
            
            if not member:
                return False, "Member not found."
            
            # Calculate due date
            due_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Add loan record
            self.cursor.execute(
                """INSERT INTO loans (book_id, member_id, due_date)
                   VALUES (?, ?, ?)""",
                (book_id, member_id, due_date)
            )
            
            # Update book status
            self.cursor.execute(
                """UPDATE books SET status = 'Borrowed'
                   WHERE book_id = ?""",
                (book_id,)
            )
            
            self.conn.commit()
            return True, f"Book checked out successfully. Due date: {due_date}"
        except sqlite3.Error as e:
            return False, f"Error checking out book: {e}"
    
    def return_book(self, book_id, member_id):
        """Return a borrowed book."""
        try:
            # Check if loan exists
            self.cursor.execute(
                """SELECT loan_id, due_date FROM loans
                   WHERE book_id = ? AND member_id = ? AND return_date IS NULL""",
                (book_id, member_id)
            )
            loan = self.cursor.fetchone()
            
            if not loan:
                return False, "No active loan found for this book and member."
            
            # Calculate fine if overdue
            due_date = datetime.datetime.strptime(loan['due_date'], '%Y-%m-%d %H:%M:%S')
            now = datetime.datetime.now()
            
            fine_amount = 0
            if now > due_date:
                days_overdue = (now - due_date).days
                fine_amount = days_overdue * 0.50  # $0.50 per day
            
            # Update loan record
            self.cursor.execute(
                """UPDATE loans
                   SET return_date = ?, status = 'Returned', fine_amount = ?
                   WHERE loan_id = ?""",
                (now.strftime('%Y-%m-%d %H:%M:%S'), fine_amount, loan['loan_id'])
            )
            
            # Update book status
            self.cursor.execute(
                """UPDATE books SET status = 'Available'
                   WHERE book_id = ?""",
                (book_id,)
            )
            
            self.conn.commit()
            
            msg = "Book returned successfully."
            if fine_amount > 0:
                msg += f" Fine for overdue: ${fine_amount:.2f}"
            
            return True, msg
        except sqlite3.Error as e:
            return False, f"Error returning book: {e}"
    
    def get_member_loans(self, member_id):
        """Get all loans for a specific member."""
        try:
            self.cursor.execute(
                """SELECT b.title, b.author, l.loan_date, l.due_date, l.return_date, l.status, l.fine_amount
                   FROM loans l
                   JOIN books b ON l.book_id = b.book_id
                   WHERE l.member_id = ?
                   ORDER BY l.loan_date DESC""",
                (member_id,)
            )
            
            loans = self.cursor.fetchall()
            if not loans:
                return False, "No loans found for this member."
            
            # Convert result to list of dictionaries
            result = []
            for loan in loans:
                loan_dict = dict(loan)
                result.append(loan_dict)
            
            return True, result
        except sqlite3.Error as e:
            return False, f"Error getting member loans: {e}"
    
    def get_overdue_books(self):
        """Get all overdue books."""
        try:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.cursor.execute(
                """SELECT b.title, b.author, m.first_name, m.last_name, l.due_date, 
                          julianday(?) - julianday(l.due_date) as days_overdue,
                          l.fine_amount
                   FROM loans l
                   JOIN books b ON l.book_id = b.book_id
                   JOIN members m ON l.member_id = m.member_id
                   WHERE l.due_date < ? AND l.return_date IS NULL""",
                (now, now)
            )
            
            overdue = self.cursor.fetchall()
            if not overdue:
                return False, "No overdue books found."
            
            # Convert result to list of dictionaries
            result = []
            for item in overdue:
                item_dict = dict(item)
                result.append(item_dict)
            
            return True, result
        except sqlite3.Error as e:
            return False, f"Error getting overdue books: {e}"
    
    def get_statistics(self):
        """Get library statistics."""
        try:
            self.cursor.execute(
                """SELECT 
                       (SELECT COUNT(*) FROM books) as total_books,
                       (SELECT COUNT(*) FROM books WHERE status = 'Available') as available_books,
                       (SELECT COUNT(*) FROM books WHERE status = 'Borrowed') as borrowed_books,
                       (SELECT COUNT(*) FROM members) as total_members,
                       (SELECT COUNT(*) FROM loans WHERE return_date IS NULL) as active_loans,
                       (SELECT COUNT(*) FROM loans WHERE due_date < CURRENT_TIMESTAMP AND return_date IS NULL) as overdue_loans,
                       (SELECT SUM(fine_amount) FROM loans) as total_fines"""
            )
            
            stats = dict(self.cursor.fetchone())
            return True, stats
        except sqlite3.Error as e:
            return False, f"Error getting statistics: {e}"

def display_menu():
    """Display the main menu options."""
    print("\n===== Library Management System =====")
    print("1. Add a new book")
    print("2. Add a new member")
    print("3. Search for books")
    print("4. Check out a book")
    print("5. Return a book")
    print("6. View member's loans")
    print("7. List overdue books")
    print("8. View library statistics")
    print("9. Exit")
    print("=====================================")
    return input("Enter your choice (1-9): ")

def main():
    lib = LibraryManagementSystem()
    
    while True:
        choice = display_menu()
        
        if choice == '1':
            # Add a new book
            title = input("Enter title: ")
            author = input("Enter author: ")
            isbn = input("Enter ISBN: ")
            year = input("Enter publication year: ")
            category = input("Enter category: ")
            shelf = input("Enter shelf location: ")
            
            success, message = lib.add_book(title, author, isbn, year, category, shelf)
            print(message)
            
        elif choice == '2':
            # Add a new member
            first_name = input("Enter first name: ")
            last_name = input("Enter last name: ")
            email = input("Enter email: ")
            phone = input("Enter phone: ")
            address = input("Enter address: ")
            
            success, message = lib.add_member(first_name, last_name, email, phone, address)
            print(message)
            
        elif choice == '3':
            # Search for books
            search_term = input("Enter search term: ")
            search_by = input("Search by (title/author/isbn): ").lower()
            
            success, result = lib.search_books(search_term, search_by)
            
            if success:
                print("\nSearch Results:")
                headers = ["ID", "Title", "Author", "Status", "Shelf"]
                table_data = [[b['book_id'], b['title'], b['author'], b['status'], b['shelf_location']] for b in result]
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
            else:
                print(result)
                
        elif choice == '4':
            # Check out a book
            book_id = input("Enter book ID: ")
            member_id = input("Enter member ID: ")
            days = input("Enter loan period in days (default 14): ")
            
            if not days:
                days = 14
            else:
                days = int(days)
                
            success, message = lib.checkout_book(book_id, member_id, days)
            print(message)
            
        elif choice == '5':
            # Return a book
            book_id = input("Enter book ID: ")
            member_id = input("Enter member ID: ")
            
            success, message = lib.return_book(book_id, member_id)
            print(message)
            
        elif choice == '6':
            # View member's loans
            member_id = input("Enter member ID: ")
            
            success, result = lib.get_member_loans(member_id)
            
            if success:
                print("\nMember Loans:")
                headers = ["Title", "Author", "Loan Date", "Due Date", "Return Date", "Status", "Fine"]
                table_data = [
                    [
                        l['title'], 
                        l['author'], 
                        l['loan_date'], 
                        l['due_date'], 
                        l['return_date'] if l['return_date'] else "-", 
                        l['status'],
                        f"${l['fine_amount']:.2f}" if l['fine_amount'] else "-"
                    ] 
                    for l in result
                ]
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
            else:
                print(result)
                
        elif choice == '7':
            # List overdue books
            success, result = lib.get_overdue_books()
            
            if success:
                print("\nOverdue Books:")
                headers = ["Title", "Author", "Member", "Due Date", "Days Overdue", "Fine"]
                table_data = [
                    [
                        o['title'], 
                        o['author'], 
                        f"{o['first_name']} {o['last_name']}", 
                        o['due_date'], 
                        int(o['days_overdue']), 
                        f"${o['fine_amount']:.2f}" if o['fine_amount'] else "-"
                    ] 
                    for o in result
                ]
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
            else:
                print(result)
                
        elif choice == '8':
            # View library statistics
            success, stats = lib.get_statistics()
            
            if success:
                print("\nLibrary Statistics:")
                for key, value in stats.items():
                    if key == 'total_fines' and value:
                        print(f"{key.replace('_', ' ').title()}: ${value:.2f}")
                    else:
                        print(f"{key.replace('_', ' ').title()}: {value or 0}")
            else:
                print(stats)
                
        elif choice == '9':
            # Exit
            lib.close()
            print("Thank you for using Library Management System. Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 