document.addEventListener('DOMContentLoaded', () => {
    const booksGrid = document.getElementById('booksGrid');
    const searchInput = document.getElementById('searchInput');
    const addBookBtn = document.getElementById('addBookBtn');
    const modal = document.getElementById('bookModal');
    const closeModal = document.querySelector('.close-modal');
    const bookForm = document.getElementById('addBookForm'); // Renamed for clarity
    const modalTitle = modal.querySelector('h2');

    let isEditMode = false;
    let currentBookId = null;

    // 1. Fetch Books from Server
    function fetchBooks() {
        booksGrid.innerHTML = "<div style='grid-column: 1/-1; text-align:center'>Chargement...</div>";
        fetch('/api/livres?action=fetch')
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text || response.statusText) });
                }
                return response.json();
            })
            .then(data => {
                if (data.error) throw new Error(data.error);
                window.allBooks = data; // Store globally for search filtering
                renderBooks(data);
            })
            .catch(error => {
                console.error('Error:', error);
                booksGrid.innerHTML = `<div style='grid-column: 1/-1; text-align:center; color:red'>Erreur : ${error.message}</div>`;
            });
    }

    function renderBooks(data) {
        booksGrid.innerHTML = "";
        if (data.length === 0) {
            booksGrid.innerHTML = "<div style='grid-column: 1/-1; text-align:center'>Aucun livre trouvé.</div>";
            return;
        }

        data.forEach(book => {
            const card = document.createElement('div');
            card.className = 'book-card';

            // Image handling
            let imageHtml = '';
            if (book.image_path) {
                imageHtml = `<img src="/static/${book.image_path}" alt="${book.title}" onerror="this.onerror=null;this.parentElement.innerHTML='<div class=\'no-image-placeholder\'><i class=\'bx bx-book\'></i></div>'">`;
            } else {
                imageHtml = `<div class="no-image-placeholder"><i class='bx bx-book'></i></div>`;
            }

            card.innerHTML = `
                <div class="book-image-container">
                    ${imageHtml}
                </div>
                
                <div class="book-title" title="${book.title}">${book.title}</div>

                <div class="book-copies-info">
                    <span class="copies-label" style="margin-right: 10px;">Copies disponibles:</span>
                    <span class="copies-value ${book.available_copies > 0 ? 'available' : 'unavailable'}">
                        ${book.available_copies} / ${book.total_copies}
                    </span>
                </div>
                
                <div class="info-icon-wrapper">
                    <i class='bx bx-info-circle'></i>
                    <div class="info-tooltip">
                        <div class="tooltip-item"><strong>Auteur:</strong> ${book.author_name || book.author || 'Inconnu'}</div>
                        <div class="tooltip-item"><strong>Année:</strong> ${book.publication_year || '-'}</div>
                        <div class="tooltip-item"><strong>Catégorie:</strong> ${book.category_name || book.category || 'Non classé'}</div>
                        <div class="tooltip-item"><strong>ISBN:</strong> ${book.isbn || '-'}</div>
                        <div class="tooltip-item"><strong>Prix:</strong> ${book.price ? book.price + ' DH' : '-'}</div>
                    </div>
                </div>
                
                <div class="spacer"></div>
                
                <div class="book-actions">
                    <button class="action-btn-pill btn-edit" onclick="window.editBook(${book.id})">
                        <i class='bx bxs-pencil'></i> Modifier
                    </button>
                    <button class="action-btn-pill btn-delete" onclick="window.deleteBook(${book.id})">
                        <i class='bx bxs-trash'></i> Supprimer
                    </button>
                </div>
            `;
            booksGrid.appendChild(card);
        });
    }

    // Initial Load
    fetchBooks();

    // 2. Search Functionality
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        if (!window.allBooks) return;

        const filtered = window.allBooks.filter(book =>
            (book.title && book.title.toLowerCase().includes(term)) ||
            (book.author_name && book.author_name.toLowerCase().includes(term)) ||
            (book.isbn && book.isbn.includes(term))
        );
        renderBooks(filtered);
    });

    // 3. Modal Logic
    function openModal(mode = 'add', book = null) {
        isEditMode = mode === 'edit';
        modal.style.display = "block";

        if (isEditMode && book) {
            modalTitle.textContent = "Modifier le Livre";
            currentBookId = book.id;
            document.getElementById('title').value = book.title;
            document.getElementById('author').value = book.author_name || ''; // Note: fetches name, ideally ID, but backend handles name lookup
            document.getElementById('category').value = book.category_name || '';
            document.getElementById('isbn').value = book.isbn || '';
            document.getElementById('publication_year').value = book.publication_year || '';
            document.getElementById('price').value = book.price || '';
            document.getElementById('total_copies').value = book.total_copies || 1;
        } else {
            modalTitle.textContent = "Ajouter un Livre";
            currentBookId = null;
            bookForm.reset();
            // Clear file input manually if needed (reset() handles it usually)
        }
    }

    addBookBtn.addEventListener('click', () => {
        openModal('add');
    });

    closeModal.addEventListener('click', () => {
        modal.style.display = "none";
    });

    window.addEventListener('click', (e) => {
        if (e.target == modal) {
            modal.style.display = "none";
        }
    });

    // 4. Save Book Logic (AJAX) - Handles both Add and Edit
    bookForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = new FormData();
        formData.append('title', document.getElementById('title').value);
        formData.append('author', document.getElementById('author').value);
        formData.append('category', document.getElementById('category').value);
        formData.append('isbn', document.getElementById('isbn').value);
        formData.append('publication_year', document.getElementById('publication_year').value);
        formData.append('price', document.getElementById('price').value);
        formData.append('total_copies', document.getElementById('total_copies').value);

        const imageFile = document.getElementById('image').files[0];
        if (imageFile) {
            formData.append('image', imageFile);
        }

        let url = '/api/livres/add';
        if (isEditMode) {
            url = '/api/livres/edit';
            formData.append('id', currentBookId);
        }

        fetch(url, {
            method: 'POST',
            body: formData  // Fetch sets Content-Type to multipart/form-data automatically
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Alert optional, maybe just close
                    modal.style.display = "none";
                    bookForm.reset();
                    fetchBooks(); // Reload list
                } else {
                    alert("Erreur: " + (result.error || "Une erreur est survenue."));
                }
            })
            .catch(err => console.error(err));
    });

    // 5. Global Actions
    window.deleteBook = function (id) {
        if (confirm('Êtes-vous sûr de vouloir supprimer ce livre ?')) {
            const formData = new FormData();
            formData.append('id', id);

            fetch('/api/livres/delete', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        fetchBooks(); // Reload
                    } else {
                        alert("Erreur lors de la suppression : " + (result.error || "Une erreur inconnue est survenue."));
                    }
                })
                .catch(err => console.error(err));
        }
    }

    window.editBook = function (id) {
        const book = window.allBooks.find(b => b.id == id);
        if (book) {
            openModal('edit', book);
        }
    }
});
