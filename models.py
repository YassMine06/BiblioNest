from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'Admins'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='Admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Author(db.Model):
    __tablename__ = 'Authors'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    birth_year = db.Column(db.Integer)
    nationality = db.Column(db.String(100))
    books = db.relationship('Book', backref='author', lazy=True, cascade="all, delete-orphan")

class Category(db.Model):
    __tablename__ = 'Categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    books = db.relationship('Book', backref='category', lazy=True)

class Book(db.Model):
    __tablename__ = 'Books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('Authors.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('Categories.id'))
    isbn = db.Column(db.String(20), unique=True)
    publication_year = db.Column(db.Integer)
    price = db.Column(db.Numeric(8, 2), default=0.00)
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)
    image_path = db.Column(db.String(255))
    # status is a generated column in SQL, we can handle it as a property in Python
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships with cascade delete
    loans = db.relationship('Loan', backref='book', lazy=True, cascade="all, delete-orphan")
    reservations = db.relationship('Reservation', backref='book', lazy=True, cascade="all, delete-orphan")
    
    __table_args__ = (
        db.CheckConstraint('available_copies <= total_copies', name='check_available_not_exceed_total'),
        db.CheckConstraint('available_copies >= 0', name='check_available_positive'),
    )

    @property
    def status(self):
        return 'Disponible' if self.available_copies > 0 else 'Emprunté'

class Reader(db.Model):
    __tablename__ = 'Readers'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    registration_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(Enum('Actif', 'Suspendu'), nullable=False, default='Actif')
    loans = db.relationship('Loan', backref='reader', lazy=True, cascade="all, delete-orphan")
    reservations = db.relationship('Reservation', backref='reader', lazy=True, cascade="all, delete-orphan")
    penalties = db.relationship('Penalty', backref='reader', lazy=True, cascade="all, delete-orphan")

class Loan(db.Model):
    __tablename__ = 'Loans'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('Books.id'), nullable=False)
    reader_id = db.Column(db.Integer, db.ForeignKey('Readers.id'), nullable=False)
    loan_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    returned_at = db.Column(db.Date)
    status = db.Column(Enum('En cours', 'Retard', 'Terminé'), default='En cours')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationship with cascade delete for penalties
    penalties = db.relationship('Penalty', backref='loan', lazy=True, cascade="all, delete-orphan")

class Reservation(db.Model):
    __tablename__ = 'Reservations'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('Books.id'), nullable=False)
    reader_id = db.Column(db.Integer, db.ForeignKey('Readers.id'), nullable=False)
    reservation_date = db.Column(db.Date, nullable=False, default=date.today)
    expiry_date = db.Column(db.Date, nullable=False)
    status = db.Column(Enum('En attente', 'Terminée', 'Annulée', 'Active'), nullable=False, default='En attente')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PenaltyType(db.Model):
    __tablename__ = 'PenaltyTypes'
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    fixed_amount = db.Column(db.Numeric(10, 2), default=0.00)
    daily_rate = db.Column(db.Numeric(5, 2), default=0.00)

class Penalty(db.Model):
    __tablename__ = 'Penalties'
    id = db.Column(db.Integer, primary_key=True)
    reader_id = db.Column(db.Integer, db.ForeignKey('Readers.id'), nullable=False)
    loan_id = db.Column(db.Integer, db.ForeignKey('Loans.id'))
    penalty_type_id = db.Column(db.Integer, db.ForeignKey('PenaltyTypes.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    penalty_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(Enum('Payé', 'Impayé'), nullable=False, default='Impayé')
    paid_at = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    penalty_type = db.relationship('PenaltyType', backref='penalties')

class Setting(db.Model):
    __tablename__ = 'Settings'
    id = db.Column(db.Integer, primary_key=True)
    library_name = db.Column(db.String(255), nullable=False, default='BiblioNest')
    contact_email = db.Column(db.String(255), nullable=False, default='contact@biblionest.com')
    default_loan_duration = db.Column(db.Integer, nullable=False, default=15)
    daily_penalty_amount = db.Column(db.Numeric(10, 2), nullable=False, default=5.00)
    deterioration_penalty_amount = db.Column(db.Numeric(10, 2), nullable=False, default=5.00)
    lost_book_penalty_amount = db.Column(db.Numeric(10, 2), nullable=False, default=20.00)
