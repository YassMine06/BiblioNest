from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, Admin, Book, Reader, Loan, Setting, Author, Category, Reservation, Penalty, PenaltyType
from werkzeug.security import check_password_hash
import os
from datetime import date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biblionest.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialize database and seed admin
with app.app_context():
    db.create_all()
    # Seed default admin if none exists
    if not Admin.query.filter_by(username='admin').first():
        from werkzeug.security import generate_password_hash
        default_admin = Admin(
            name='Administrateur',
            username='admin',
            role='Super Admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(default_admin)
        
    # Seed default settings if none exist
    if not Setting.query.get(1):
        default_settings = Setting(
            id=1,
            library_name='BiblioNest',
            contact_email='contact@biblionest.com',
            default_loan_duration=15,
            daily_penalty_amount=1.00,
            deterioration_penalty_amount=5.00,
            lost_book_penalty_amount=20.00
        )
        db.session.add(default_settings)
        
    # Seed default penalty types if none exist
    if not PenaltyType.query.filter_by(label='Retard').first():
        db.session.add(PenaltyType(label='Retard', description='Pénalité pour retour tardif', daily_rate=1.00))
    if not PenaltyType.query.filter_by(label='Détérioration').first():
        db.session.add(PenaltyType(label='Détérioration', description='Pénalité pour livre abîmé', fixed_amount=5.00))
    if not PenaltyType.query.filter_by(label='Perte').first():
        db.session.add(PenaltyType(label='Perte', description='Pénalité pour livre perdu', fixed_amount=20.00))
        
    db.session.commit()

@app.before_request
def check_login():
    public_routes = ['login', 'static']
    if 'user_id' not in session and request.endpoint not in public_routes:
        return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        # In a real app, use check_password_hash. 
        # The PHP app used password_verify, so we assume password_hash is compatible with bcrypt.
        # For now, let's try to match the PHP logic.
        if admin and check_password_hash(admin.password_hash, password):
            session['user_id'] = admin.id
            session['user_name'] = admin.name
            session['user_role'] = admin.role
            return redirect(url_for('dashboard'))
        else:
            error = "Nom d'utilisateur ou mot de passe incorrect."
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    from datetime import date
    total_books = Book.query.count()
    total_readers = Reader.query.count()
    total_overdue = Loan.query.filter(Loan.returned_at == None, Loan.due_date < date.today()).count()
    active_loans = Loan.query.filter(Loan.returned_at == None).count()
    
    recent_activities = Loan.query.order_by(Loan.id.desc()).limit(5).all()
    
    setting = Setting.query.get(1)
    lib_name = setting.library_name if setting else 'BiblioNest'

    # --- Data for Charts ---
    
    # 1. Books per Category
    # We need a list of labels (Category Names) and data (Count)
    categories = Category.query.all()
    cat_names = []
    cat_counts = []
    for cat in categories:
        count = Book.query.filter_by(category_id=cat.id).count()
        if count > 0: # Only show categories with books
            cat_names.append(cat.name)
            cat_counts.append(count)
            
    # 2. Loan Status Distribution (Pie Chart)
    # Available vs Borrowed (Active Loans) vs Overdue
    # Note: 'active_loans' includes overdue ones in the count usually, so we split them
    borrowed_not_overdue = Loan.query.filter(Loan.returned_at == None, Loan.due_date >= date.today()).count()
    # total_overdue is already calculated above
    # available_count is the sum of available_copies of all books
    available_stock = db.session.query(db.func.sum(Book.available_copies)).scalar() or 0

    # 3. New Graph: Loans Over Time (Last 7 Days)
    from datetime import timedelta
    from sqlalchemy import func
    
    dates_labels = []
    loans_data = []
    
    today = date.today()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        dates_labels.append(day.strftime("%d/%m"))
        # Count loans created on 'day'
        # Assuming Loan.loan_date is a Date object or comparison works
        day_count = Loan.query.filter(func.date(Loan.loan_date) == day).count()
        loans_data.append(day_count)

    return render_template('dashboard.html', 
                           total_books=total_books, 
                           total_readers=total_readers, 
                           total_overdue=total_overdue, 
                           active_loans=active_loans,
                           recent_activities=recent_activities,
                           lib_name=lib_name,
                           date=date,
                           # Chart Data
                           cat_names=cat_names,
                           cat_counts=cat_counts,
                           chart_available=available_stock,
                           chart_borrowed=borrowed_not_overdue,
                           chart_overdue=total_overdue,
                           # New Line Chart Data
                           dates_labels=dates_labels,
                           loans_data=loans_data)

@app.route('/livres', methods=['GET'])
def list_books():
    return render_template('livres.html')

@app.route('/api/livres', methods=['GET'])
def get_books():
    action = request.args.get('action', 'fetch')
    if action == 'fetch':
        books = Book.query.all()
        result = []
        for book in books:
            result.append({
                'id': book.id,
                'title': book.title,
                'author_name': book.author.full_name if book.author else 'N/A',
                'category_name': book.category.name if book.category else 'N/A',
                'isbn': book.isbn,
                'publication_year': book.publication_year,
                'price': float(book.price),
                'total_copies': book.total_copies,
                'available_copies': book.available_copies,
                'status': book.status,
                'image_path': book.image_path
            })
        return jsonify(result)
    return jsonify({'error': 'Invalid action'}), 400

@app.route('/api/livres/add', methods=['POST'])
def add_book():
    try:
        from werkzeug.utils import secure_filename
        import os
        
        # Handle form data instead of JSON
        data = request.form
        file = request.files.get('image')
        
        image_path = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Make unique filename
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            save_path = os.path.join('static', 'img', 'books', filename)
            # Ensure safe path - absolute path mapping
            abs_save_path = os.path.join(app.root_path, save_path)
            file.save(abs_save_path)
            image_path = f"img/books/{filename}"

        # Handle author (lookup or create)
        author_name = data.get('author')
        author = Author.query.filter_by(full_name=author_name).first()
        if not author:
            author = Author(full_name=author_name)
            db.session.add(author)
            db.session.flush()
            
        # Handle category
        cat_name = data.get('category')
        category = Category.query.filter_by(name=cat_name).first()
        if not category:
            category = Category(name=cat_name)
            db.session.add(category)
            db.session.flush()
            
        new_book = Book(
            title=data.get('title'),
            author_id=author.id,
            category_id=category.id,
            isbn=data.get('isbn'),
            publication_year=data.get('publication_year'),
            price=data.get('price'),
            total_copies=data.get('total_copies'),
            available_copies=data.get('total_copies'), # Initial equals total
            image_path=image_path
        )
        db.session.add(new_book)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/livres/edit', methods=['POST'])
def edit_book():
    try:
        from werkzeug.utils import secure_filename
        import os
        
        data = request.form
        book = Book.query.get(data.get('id'))
        if not book:
            return jsonify({'success': False, 'error': 'Book not found'})
            
        # Handle image upload
        file = request.files.get('image')
        if file and file.filename:
            filename = secure_filename(file.filename)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            save_path = os.path.join('static', 'img', 'books', filename)
            abs_save_path = os.path.join(app.root_path, save_path)
            file.save(abs_save_path)
            book.image_path = f"img/books/{filename}"
            
        # Handle author
        author_name = data.get('author')
        author = Author.query.filter_by(full_name=author_name).first()
        if not author:
            author = Author(full_name=author_name)
            db.session.add(author)
            db.session.flush()
            
        # Handle category
        cat_name = data.get('category')
        category = Category.query.filter_by(name=cat_name).first()
        if not category:
            category = Category(name=cat_name)
            db.session.add(category)
            db.session.flush()
            
        book.title = data.get('title')
        book.author_id = author.id
        book.category_id = category.id
        book.isbn = data.get('isbn')
        book.publication_year = data.get('publication_year')
        book.price = data.get('price')
        
        # Handle total_copies change and update available_copies accordingly
        new_total = int(data.get('total_copies'))
        old_total = book.total_copies
        
        if new_total != old_total:
            # Calculate how many copies are currently loaned out
            loaned_copies = old_total - book.available_copies
            
            # Update total and recalculate available
            book.total_copies = new_total
            book.available_copies = max(0, new_total - loaned_copies)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/livres/delete', methods=['POST'])
def delete_book():
    book_id = request.form.get('id')
    book = Book.query.get(book_id)
    if book:
        try:
            db.session.delete(book)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'Book not found'})

@app.route('/lecteurs', methods=['GET'])
def list_readers():
    return render_template('lecteurs.html')

@app.route('/api/lecteurs', methods=['GET'])
def get_readers():
    try:
        action = request.args.get('action', 'fetch')
        if action == 'fetch':
            readers = Reader.query.all()
            result = []
            for reader in readers:
                try:
                    reg_date = reader.registration_date.strftime('%Y-%m-%d') if reader.registration_date else 'N/A'
                    result.append({
                        'id': reader.id,
                        'first_name': reader.first_name or 'N/A',
                        'last_name': reader.last_name or 'N/A',
                        'email': reader.email or 'N/A',
                        'phone': reader.phone,
                        'registration_date': reg_date,
                        'status': str(reader.status) if reader.status else 'Actif'
                    })
                except Exception as row_error:
                    print(f"Error processing reader {reader.id}: {row_error}")
                    continue
            return jsonify(result)
        return jsonify({'error': 'Invalid action'}), 400
    except Exception as e:
        print(f"API Readers Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lecteurs/add', methods=['POST'])
def add_reader():
    data = request.get_json()
    try:
        new_reader = Reader(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            status=data.get('status', 'Actif')
        )
        db.session.add(new_reader)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/lecteurs/edit', methods=['POST'])
def edit_reader():
    data = request.get_json()
    try:
        reader = Reader.query.get(data.get('id'))
        if not reader:
            return jsonify({'success': False, 'error': 'Reader not found'})
            
        reader.first_name = data.get('first_name')
        reader.last_name = data.get('last_name')
        reader.email = data.get('email')
        reader.phone = data.get('phone')
        reader.status = data.get('status')
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/lecteurs/delete', methods=['POST'])
def delete_reader():
    reader_id = request.form.get('id')
    reader = Reader.query.get(reader_id)
    if reader:
        try:
            db.session.delete(reader)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'Reader not found'})

@app.route('/prets', methods=['GET'])
def list_loans():
    return render_template('prets.html')

@app.route('/api/prets', methods=['GET'])
def get_loans():
    action = request.args.get('action', 'fetch')
    if action == 'fetch':
        # Get all loans with related reader and book info
        loans = Loan.query.filter(Loan.status != 'Terminé').order_by(Loan.id.desc()).all()
        result = []
        for loan in loans:
            result.append({
                'id': loan.id,
                'book_id': loan.book_id,
                'reader_id': loan.reader_id,
                'book_title': loan.book.title if loan.book else 'N/A',
                'reader_name': f"{loan.reader.first_name} {loan.reader.last_name}" if loan.reader else 'N/A',
                'loan_date': loan.loan_date.strftime('%Y-%m-%d'),
                'due_date': loan.due_date.strftime('%Y-%m-%d'),
                'returned_at': loan.returned_at.strftime('%Y-%m-%d') if loan.returned_at else None,
                'status': loan.status
            })
        return jsonify(result)
    elif action == 'fetch_options':
        # For the modal dropdowns
        from models import Book, Reader
        available_books = Book.query.filter(Book.available_copies > 0).all()
        readers = Reader.query.filter_by(status='Actif').all()
        
        return jsonify({
            'books': [{'id': b.id, 'title': b.title, 'available_copies': b.available_copies} for b in available_books],
            'readers': [{'id': r.id, 'full_name': f"{r.first_name} {r.last_name}"} for r in readers]
        })
    return jsonify({'error': 'Invalid action'}), 400

@app.route('/api/prets/add', methods=['POST'])
def add_loan():
    data = request.get_json()
    try:
        from datetime import datetime
        book = Book.query.get(data.get('book_id'))
        if not book or book.available_copies <= 0:
            return jsonify({'success': False, 'error': 'Livre non disponible'})
            
        loan_date = datetime.strptime(data.get('loan_date'), '%Y-%m-%d').date() if data.get('loan_date') else date.today()
        due_date = datetime.strptime(data.get('due_date'), '%Y-%m-%d').date() if data.get('due_date') else None
        
        # Fallback due date if not provided
        if not due_date:
            from datetime import timedelta
            due_date = loan_date + timedelta(days=15)

        new_loan = Loan(
            book_id=data.get('book_id'),
            reader_id=data.get('reader_id'),
            loan_date=loan_date,
            due_date=due_date,
            status='En cours'
        )
        book.available_copies -= 1
        db.session.add(new_loan)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/prets/edit', methods=['POST'])
def edit_loan():
    data = request.get_json()
    try:
        loan = Loan.query.get(data.get('id'))
        if not loan:
            return jsonify({'success': False, 'error': 'Loan not found'})
            
        loan.book_id = data.get('book_id')
        loan.reader_id = data.get('reader_id')
        
        from datetime import datetime
        if data.get('loan_date'):
            loan.loan_date = datetime.strptime(data.get('loan_date'), '%Y-%m-%d').date()
        if data.get('due_date'):
            loan.due_date = datetime.strptime(data.get('due_date'), '%Y-%m-%d').date()
            
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/prets/return', methods=['POST'])
def return_loan():
    loan_id = request.form.get('id')
    loan = Loan.query.get(loan_id)
    if loan:
        if loan.status == 'Terminé':
             return jsonify({'success': False, 'error': 'Déjà retourné'})
             
        try:
            from datetime import date
            return_date = date.today()
            loan.status = 'Terminé'
            loan.returned_at = return_date
            loan.book.available_copies += 1
            
            # Check if loan is overdue and create penalty
            if return_date > loan.due_date:
                days_overdue = (return_date - loan.due_date).days
                # Calculate penalty: 5 DH per day overdue (you can adjust this)
                penalty_amount = days_overdue * 5.0
                
                # Create penalty record
                penalty = Penalty(
                    reader_id=loan.reader_id,
                    loan_id=loan.id,
                    penalty_type_id=1,  # Assuming 1 is "Retard de retour"
                    reason=f"Retour en retard de {days_overdue} jour(s)",
                    amount=penalty_amount,
                    penalty_date=return_date,
                    status='Impayé'
                )
                db.session.add(penalty)
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'Loan not found'})

@app.route('/api/prets/delete', methods=['POST'])
def delete_loan():
    loan_id = request.form.get('id')
    loan = Loan.query.get(loan_id)
    if loan:
        try:
            # If deleted while "En cours", return the book copy
            if loan.status != 'Terminé':
                loan.book.available_copies += 1
            db.session.delete(loan)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'Loan not found'})

@app.route('/api/settings', methods=['GET'])
def get_settings():
    setting = Setting.query.get(1)
    if setting:
        return jsonify({
            'library_name': setting.library_name,
            'default_loan_duration': setting.default_loan_duration
        })
    return jsonify({'error': 'Settings not found'}), 404

@app.route('/retours', methods=['GET'])
def list_returns():
    return render_template('retours.html')

@app.route('/api/retours', methods=['GET'])
def get_returns():
    action = request.args.get('action', 'fetch')
    if action == 'fetch':
        # Get only finished loans
        returns = Loan.query.filter_by(status='Terminé').order_by(Loan.returned_at.desc()).all()
        result = []
        for r in returns:
            days_late = (r.returned_at - r.due_date).days if r.returned_at and r.due_date else 0
            result.append({
                'id': r.id,
                'book_title': r.book.title if r.book else 'N/A',
                'reader_name': f"{r.reader.first_name} {r.reader.last_name}" if r.reader else 'N/A',
                'returned_at': r.returned_at.strftime('%Y-%m-%d') if r.returned_at else 'N/A',
                'days_late': max(0, days_late),
                'status': 'Rendu'
            })
        return jsonify(result)
    return jsonify({'error': 'Invalid action'}), 400

@app.route('/reservations', methods=['GET'])
def list_reservations():
    return render_template('reservations.html')

@app.route('/api/reservations', methods=['GET'])
def get_reservations():
    action = request.args.get('action', 'fetch')
    if action == 'fetch':
        try:
            reservations = Reservation.query.order_by(Reservation.id.desc()).all()
            result = []
            for r in reservations:
                # Safely handle dates (might be string or date object depending on SQLite driver/data)
                res_date = r.reservation_date
                if hasattr(res_date, 'strftime'):
                    res_date = res_date.strftime('%Y-%m-%d')
                
                exp_date = r.expiry_date
                if hasattr(exp_date, 'strftime'):
                    exp_date = exp_date.strftime('%Y-%m-%d')
                
                book_title = r.book.title if r.book else 'Livre inconnu'
                reader_name = f"{r.reader.first_name} {r.reader.last_name}" if r.reader else 'Lecteur inconnu'
                
                # Normalize status for frontend compatibility
                status = r.status
                if status == 'Active':
                    status = 'En attente'
                
                # Check if book is now available
                book_available = r.book.available_copies > 0 if r.book else False

                result.append({
                    'id': r.id,
                    'book_id': r.book_id,
                    'reader_id': r.reader_id,
                    'book_title': book_title,
                    'reader_name': reader_name,
                    'reservation_date': res_date,
                    'expiry_date': exp_date,
                    'status': status,
                    'book_available': book_available
                })
            return jsonify(result)
        except Exception as e:
            import traceback
            traceback.print_exc() # Print to console
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Invalid action'}), 400

@app.route('/api/reservations/add', methods=['POST'])
def add_reservation():
    data = request.get_json()
    try:
        from datetime import date, timedelta
        
        # Check if book exists and has no available copies
        book = Book.query.get(data.get('book_id'))
        if not book:
            return jsonify({'success': False, 'error': 'Livre introuvable'})
        
        if book.available_copies > 0:
            return jsonify({'success': False, 'error': 'Ce livre a des copies disponibles. Veuillez emprunter directement au lieu de réserver.'})
        
        new_res = Reservation(
            book_id=data.get('book_id'),
            reader_id=data.get('reader_id'),
            reservation_date=date.today(),
            expiry_date=date.today() + timedelta(days=3), # Default 3 days
            status='En attente'
        )
        db.session.add(new_res)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reservations/edit', methods=['POST'])
def edit_reservation():
    data = request.get_json()
    try:
        res = Reservation.query.get(data.get('id'))
        if not res:
            return jsonify({'success': False, 'error': 'Reservation not found'})
            
        res.book_id = data.get('book_id')
        res.reader_id = data.get('reader_id')
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reservations/complete', methods=['POST'])
def complete_reservation():
    res_id = request.form.get('id')
    res = Reservation.query.get(res_id)
    if res:
        try:
            res.status = 'Terminée'
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'Reservation not found'})

@app.route('/api/reservations/cancel', methods=['POST'])
def cancel_reservation():
    res_id = request.form.get('id')
    res = Reservation.query.get(res_id)
    if res:
        try:
            res.status = 'Annulée'
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'Reservation not found'})

@app.route('/api/reservations/delete', methods=['POST'])
def delete_reservation():
    res_id = request.form.get('id')
    res = Reservation.query.get(res_id)
    if res:
        try:
            db.session.delete(res)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'Reservation not found'})

@app.route('/api/reservations/convert', methods=['POST'])
def convert_reservation():
    res_id = request.form.get('id')
    res = Reservation.query.get(res_id)
    if res and res.status in ['Terminée', 'Active', 'En attente']:
        try:
            from datetime import date, timedelta
            if res.book.available_copies <= 0:
                return jsonify({'success': False, 'error': 'Livre non disponible actuellement'})
                
            new_loan = Loan(
                book_id=res.book_id,
                reader_id=res.reader_id,
                loan_date=date.today(),
                due_date=date.today() + timedelta(days=15),
                status='En cours'
            )
            res.book.available_copies -= 1
            db.session.delete(res)
            db.session.add(new_loan)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'Reservation not found or not active'})

@app.route('/penalites', methods=['GET'])
def list_penalties():
    return render_template('penalites.html')

@app.route('/api/penalites', methods=['GET'])
def get_penalties():
    action = request.args.get('action', 'fetch')
    if action == 'fetch':
        penalties = Penalty.query.order_by(Penalty.id.desc()).all()
        result = []
        for p in penalties:
            result.append({
                'id': p.id,
                'reader_name': f"{p.reader.first_name} {p.reader.last_name}" if p.reader else 'N/A',
                'reason': p.reason,
                'amount': float(p.amount),
                'status': p.status,
                'penalty_type': p.penalty_type.label if p.penalty_type else 'N/A'
            })
        return jsonify(result)
    elif action == 'fetch_types':
        types = PenaltyType.query.all()
        return jsonify([{
            'id': t.id,
            'label': t.label,
            'fixed_amount': float(t.fixed_amount or 0),
            'daily_rate': float(t.daily_rate or 0)
        } for t in types])
    elif action == 'fetch_readers':
        from models import Reader
        readers = Reader.query.order_by(Reader.last_name).all()
        return jsonify([{
            'id': r.id, 
            'full_name': f"{r.first_name} {r.last_name}"
        } for r in readers])
    return jsonify({'error': 'Invalid action'}), 400

@app.route('/api/penalites/add', methods=['POST'])
def add_penalty():
    data = request.get_json()
    try:
        new_penalty = Penalty(
            reader_id=data.get('reader_id'),
            penalty_type_id=data.get('penalty_type_id'),
            reason=data.get('reason'),
            amount=data.get('amount'),
            status='Impayé'
        )
        db.session.add(new_penalty)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/penalites/edit', methods=['POST'])
def edit_penalty():
    data = request.get_json()
    try:
        p = Penalty.query.get(data.get('id'))
        if not p:
            return jsonify({'success': False, 'error': 'Penalty not found'})
        p.reader_id = data.get('reader_id')
        p.penalty_type_id = data.get('penalty_type_id')
        p.reason = data.get('reason')
        p.amount = data.get('amount')
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/penalites/delete', methods=['POST'])
def delete_penalty():
    pen_id = request.form.get('id')
    penalty = Penalty.query.get(pen_id)
    if penalty:
        try:
            db.session.delete(penalty)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'Penalty not found'})

@app.route('/api/penalites/pay', methods=['POST'])
def pay_penalty():
    pen_id = request.form.get('id')
    penalty = Penalty.query.get(pen_id)
    if penalty:
        try:
            from datetime import date
            penalty.status = 'Payé'
            penalty.paid_at = date.today()
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
@app.route('/parametres', methods=['GET'])
def list_settings():
    setting = Setting.query.get(1)
    return render_template('parametres.html', setting=setting)

@app.route('/api/settings/update', methods=['POST'])
def update_settings():
    data = request.get_json()
    try:
        setting = Setting.query.get(1)
        if not setting:
            setting = Setting(id=1)
            db.session.add(setting)
            
        setting.library_name = data.get('library_name')
        setting.contact_email = data.get('contact_email')
        setting.default_loan_duration = int(data.get('default_loan_duration'))
        setting.daily_penalty_amount = float(data.get('daily_penalty_amount'))
        setting.deterioration_penalty_amount = float(data.get('deterioration_penalty_amount'))
        setting.lost_book_penalty_amount = float(data.get('lost_book_penalty_amount'))
        
        # Sync with PenaltyTypes
        retard_type = PenaltyType.query.filter_by(label='Retard').first()
        if retard_type:
            retard_type.daily_rate = setting.daily_penalty_amount
            
        deterioration_type = PenaltyType.query.filter_by(label='Détérioration').first()
        if deterioration_type:
            deterioration_type.fixed_amount = setting.deterioration_penalty_amount
            
        lost_type = PenaltyType.query.filter_by(label='Perte').first()
        if lost_type:
            lost_type.fixed_amount = setting.lost_book_penalty_amount
            
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings/resync', methods=['POST'])
def resync_stocks():
    try:
        books = Book.query.all()
        for book in books:
            active_loans = Loan.query.filter(Loan.book_id == book.id, Loan.status.in_(['En cours', 'Retard'])).count()
            book.available_copies = max(0, book.total_copies - active_loans)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/generate_report')
def generate_report():
    import csv
    from io import StringIO
    from flask import Response
    from datetime import date

    # StringIO to write CSV data
    si = StringIO()
    cw = csv.writer(si)

    # Add BOM for Excel
    si.write('\ufeff')

    cw.writerow(['RAPPORT BIBLIONEST - ' + date.today().strftime('%d/%m/%Y')])
    cw.writerow([])

    try:
        total_books = Book.query.count()
        total_readers = Reader.query.count()
        active_loans = Loan.query.filter(Loan.returned_at == None).count()
        overdue = Loan.query.filter(Loan.returned_at == None, Loan.due_date < date.today()).count()

        cw.writerow(['Statistiques Globales'])
        cw.writerow(['Total Livres', 'Total Lecteurs', 'Prêts Actifs', 'Retards'])
        cw.writerow([total_books, total_readers, active_loans, overdue])
        cw.writerow([])

        cw.writerow(['Prêts en retard'])
        cw.writerow(['Lecteur', 'Livre', 'Date Prêt', 'Échéance', 'Jours de Retard'])
        
        overdue_loans = Loan.query.filter(Loan.returned_at == None, Loan.due_date < date.today()).all()
        for loan in overdue_loans:
            days_late = (date.today() - loan.due_date).days
            cw.writerow([
                f"{loan.reader.first_name} {loan.reader.last_name}" if loan.reader else 'N/A',
                loan.book.title if loan.book else 'N/A',
                loan.loan_date.strftime('%Y-%m-%d'),
                loan.due_date.strftime('%Y-%m-%d'),
                days_late
            ])
        cw.writerow([])

        cw.writerow(['État des Stocks'])
        cw.writerow(['Titre', 'ISBN', 'Total', 'Disponible', 'Statut'])
        books = Book.query.order_by(Book.available_copies.asc()).all()
        for b in books:
            cw.writerow([b.title, b.isbn, b.total_copies, b.available_copies, b.status])

    except Exception as e:
        cw.writerow(['Erreur lors de la génération du rapport : ' + str(e)])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=rapport_biblionest_" + date.today().strftime('%Y-%m-%d') + ".csv"}
    )


@app.route('/api/chart-data')
def chart_data():
    period = request.args.get('period', 'week')
    from sqlalchemy import func
    from datetime import timedelta
    
    labels = []
    data = []
    today = date.today()
    
    if period == 'week':
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            labels.append(day.strftime("%d/%m"))
            count = Loan.query.filter(func.date(Loan.loan_date) == day).count()
            data.append(count)
            
    elif period == 'month':
        for i in range(29, -1, -1):
            day = today - timedelta(days=i)
            labels.append(day.strftime("%d/%m"))
            count = Loan.query.filter(func.date(Loan.loan_date) == day).count()
            data.append(count)
            
    elif period == 'year':
        # Last 12 months
        for i in range(11, -1, -1):
            # Calculate target month and year safely
            # Note: months are 1-12
            total_months = today.month - i
            year = today.year
            month = total_months
            
            while month <= 0:
                month += 12
                year -= 1
                
            labels.append(f"{month:02d}/{year}")
            count = Loan.query.filter(
                func.extract('month', Loan.loan_date) == month,
                func.extract('year', Loan.loan_date) == year
            ).count()
            data.append(count)
            
    return jsonify({'labels': labels, 'data': data})

# Admin Management Routes
@app.route('/admins', methods=['GET', 'POST'])
def list_admins():
    if request.method == 'POST':
        try:
            from werkzeug.security import generate_password_hash
            name = request.form.get('name')
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role', 'Admin')
            
            # Check if username already exists
            existing = Admin.query.filter_by(username=username).first()
            if existing:
                flash('Ce nom d\'utilisateur existe déjà')
                return redirect(url_for('list_admins'))
            
            new_admin = Admin(
                name=name,
                username=username,
                password_hash=generate_password_hash(password),
                role=role
            )
            db.session.add(new_admin)
            db.session.commit()
            flash('Administrateur ajouté avec succès')
            return redirect(url_for('list_admins'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}')
            return redirect(url_for('list_admins'))
    
    # GET request
    admins = Admin.query.all()
    return render_template('admins.html', admins=admins)

@app.route('/admins/delete/<int:admin_id>')
def delete_admin(admin_id):
    admin = Admin.query.get(admin_id)
    if admin:
        # Prevent deleting the last admin
        if Admin.query.count() <= 1:
            flash('Impossible de supprimer le dernier administrateur')
            return redirect(url_for('list_admins'))
        
        try:
            db.session.delete(admin)
            db.session.commit()
            flash('Administrateur supprimé')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}')
    return redirect(url_for('list_admins'))

if __name__ == '__main__':
    app.run(debug=True)
