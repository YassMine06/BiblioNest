import os
import sys
from datetime import date, timedelta
import json

# Add current directory to path
sys.path.append(os.getcwd())

from app import app, db
from models import Book, Reader, Author, Category, Loan, Reservation

def verify():
    # Configure test database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        
        # Setup Test Data
        author = Author(full_name='Test Author')
        category = Category(name='Test Category')
        db.session.add(author)
        db.session.add(category)
        db.session.commit()
        
        book = Book(
            title='Test Book',
            author_id=author.id,
            category_id=category.id,
            total_copies=5,
            available_copies=5
        )
        reader = Reader(
            first_name='Test',
            last_name='Reader',
            email='test@example.com'
        )
        db.session.add(book)
        db.session.add(reader)
        db.session.commit()
        
        client = app.test_client()
        
        print("1. Testing Add Loan...")
        custom_date = '2025-01-01'
        custom_due = '2025-01-10'
        
        res = client.post('/api/prets/add', json={
            'book_id': book.id,
            'reader_id': reader.id,
            'loan_date': custom_date,
            'due_date': custom_due
        })
        print(f"Add Loan Status: {res.status_code}, Response: {res.json}")
        
        loan = Loan.query.first()
        if loan and str(loan.loan_date) == custom_date and str(loan.due_date) == custom_due:
            print("PASS: Loan created with correct dates.")
        else:
            print(f"FAIL: Loan dates mismatch. Got loan: {loan.loan_date}, due: {loan.due_date}")
            return

        print("\n2. Testing Edit Loan...")
        new_due = '2025-02-01'
        res = client.post('/api/prets/edit', json={
            'id': loan.id,
            'book_id': book.id,
            'reader_id': reader.id,
            'loan_date': custom_date,
            'due_date': new_due
        })
        print(f"Edit Loan Status: {res.status_code}, Response: {res.json}")
        
        loan = Loan.query.get(loan.id) # Refresh
        if str(loan.due_date) == new_due:
            print("PASS: Loan edited successfully.")
        else:
            print(f"FAIL: Loan edit failed. Due date: {loan.due_date}")
            return
            
        print("\n3. Testing Return Loan...")
        res = client.post('/api/prets/return', data={'id': loan.id}) # Form data
        print(f"Return Loan Status: {res.status_code}, Response: {res.json}")
        
        loan = Loan.query.get(loan.id)
        if loan.status == 'Terminé':
            print("PASS: Loan returned.")
        else:
            print(f"FAIL: Loan return failed. Status: {loan.status}")
            return

        print("\n4. Testing Add Reservation...")
        res = client.post('/api/reservations/add', json={
            'book_id': book.id,
            'reader_id': reader.id
        })
        print(f"Add Res Status: {res.status_code}, Response: {res.json}")
        
        reservation = Reservation.query.first()
        if reservation:
            print("PASS: Reservation created.")
        else:
            print("FAIL: Reservation not created.")
            return

        print("\n5. Testing Edit Reservation...")
        # Create another reader to switch to
        reader2 = Reader(first_name='Reader2', last_name='Test', email='r2@test.com')
        db.session.add(reader2)
        db.session.commit()
        
        res = client.post('/api/reservations/edit', json={
            'id': reservation.id,
            'book_id': book.id,
            'reader_id': reader2.id
        })
        print(f"Edit Res Status: {res.status_code}, Response: {res.json}")
        
        reservation = Reservation.query.first()
        if reservation.reader_id == reader2.id:
            print("PASS: Reservation edited.")
        else:
            print(f"FAIL: Reservation edit failed. Reader ID: {reservation.reader_id}")
            return

        print("\nALL BACKEND TESTS PASSED.")

if __name__ == '__main__':
    verify()
