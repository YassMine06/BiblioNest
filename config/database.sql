-- Création de la base de données
CREATE DATABASE IF NOT EXISTS BiblioNest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE BiblioNest;

-- Table: Admins
CREATE TABLE IF NOT EXISTS Admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Authors
CREATE TABLE IF NOT EXISTS Authors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    birth_year INT,
    nationality VARCHAR(100)
);

-- Table: Categories
CREATE TABLE IF NOT EXISTS Categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Table: Books
CREATE TABLE IF NOT EXISTS Books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author_id INT NOT NULL,
    category_id INT,
    isbn VARCHAR(20) UNIQUE,
    publication_year INT,
    price DECIMAL(8,2) DEFAULT 0.00,
    total_copies INT NOT NULL DEFAULT 1,
    available_copies INT NOT NULL DEFAULT 1,
    image_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES Authors(id) ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES Categories(id) ON DELETE SET NULL,
    CHECK (available_copies <= total_copies),
    CHECK (available_copies >= 0)
);

-- Table: Readers
CREATE TABLE IF NOT EXISTS Readers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20),
    registration_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    status ENUM('Actif', 'Suspendu') NOT NULL DEFAULT 'Actif'
);

-- Table: Loans
CREATE TABLE IF NOT EXISTS Loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    reader_id INT NOT NULL,
    loan_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    due_date DATE NOT NULL,
    returned_at DATE NULL,
    status ENUM('En cours', 'Retard', 'Terminé') DEFAULT 'En cours',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES Books(id) ON DELETE RESTRICT,
    FOREIGN KEY (reader_id) REFERENCES Readers(id) ON DELETE RESTRICT
);

-- Table: Reservations
CREATE TABLE IF NOT EXISTS Reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    reader_id INT NOT NULL,
    reservation_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    expiry_date DATE NOT NULL,
    status ENUM('En attente', 'Terminée', 'Annulée') NOT NULL DEFAULT 'En attente',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES Books(id) ON DELETE CASCADE,
    FOREIGN KEY (reader_id) REFERENCES Readers(id) ON DELETE CASCADE
);

-- Table: PenaltyTypes
CREATE TABLE IF NOT EXISTS PenaltyTypes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    label VARCHAR(100) NOT NULL,
    description TEXT,
    fixed_amount DECIMAL(10,2) DEFAULT 0.00,
    daily_rate DECIMAL(5,2) DEFAULT 0.00
);

-- Table: Penalties
CREATE TABLE IF NOT EXISTS Penalties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reader_id INT NOT NULL,
    loan_id INT NULL,
    penalty_type_id INT NOT NULL,
    reason TEXT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    penalty_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    status ENUM('Payé', 'Impayé') NOT NULL DEFAULT 'Impayé',
    paid_at DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reader_id) REFERENCES Readers(id) ON DELETE CASCADE,
    FOREIGN KEY (loan_id) REFERENCES Loans(id) ON DELETE SET NULL,
    FOREIGN KEY (penalty_type_id) REFERENCES PenaltyTypes(id) ON DELETE RESTRICT
);

-- Table: Settings
CREATE TABLE IF NOT EXISTS Settings (
    id INT PRIMARY KEY,
    library_name VARCHAR(255) NOT NULL DEFAULT 'BiblioNest',
    contact_email VARCHAR(255) NOT NULL DEFAULT 'contact@biblionest.com',
    default_loan_duration INT NOT NULL DEFAULT 15,
    daily_penalty_amount DECIMAL(10,2) NOT NULL DEFAULT 5.00,
    deterioration_penalty_amount DECIMAL(10,2) NOT NULL DEFAULT 5.00,
    lost_book_penalty_amount DECIMAL(10,2) NOT NULL DEFAULT 20.00
);

-- Données initiales : Types de pénalités
INSERT INTO PenaltyTypes (id, label, description, fixed_amount, daily_rate) VALUES 
(1, 'Retard', "Pénalité par jour de retard au-delà de la date d'échéance", 0.00, 0.50),
(2, 'Détérioration', 'Livre rendu abîmé mais réparable', 5.00, 0.00),
(3, 'Perte', 'Livre perdu ou détruit (prix fixe + prix du livre à ajouter manuellement)', 20.00, 0.00)
ON DUPLICATE KEY UPDATE label=label;

-- Données initiales : Paramètres
INSERT INTO Settings (id, library_name, contact_email, default_loan_duration, daily_penalty_amount, deterioration_penalty_amount, lost_book_penalty_amount)
VALUES (1, 'BiblioNest', 'contact@biblionest.com', 15, 5.00, 5.00, 20.00)
ON DUPLICATE KEY UPDATE id=id;
