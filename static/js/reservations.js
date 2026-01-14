document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('resTableBody');
    const modal = document.getElementById('resModal');
    const btn = document.getElementById('addResBtn');
    const close = document.querySelector('.close-modal');
    const form = document.getElementById('addResForm');
    const bookSelect = document.getElementById('bookSelect');
    const readerSelect = document.getElementById('readerSelect');

    // 1. Fetch Reservations from Server
    function fetchReservations() {
        tableBody.innerHTML = "<tr><td colspan='6' style='text-align:center'>Chargement...</td></tr>";
        fetch('/api/reservations?action=fetch')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                if (!Array.isArray(data)) {
                    throw new Error("Format de réponse invalide");
                }
                window.allReservations = data;
                renderTable(data);
            })
            .catch(error => {
                console.error('Error:', error);
                tableBody.innerHTML = "<tr><td colspan='6' style='text-align:center; color:red'>Erreur de chargement.</td></tr>";
            });
    }

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR');
    }

    function renderTable(data) {
        tableBody.innerHTML = "";
        if (data.length === 0) {
            tableBody.innerHTML = "<tr><td colspan='6' style='text-align:center'>Aucune réservation.</td></tr>";
            return;
        }

        data.forEach(item => {
            const row = document.createElement('tr');

            let statusClass = '';
            if (item.status === 'En attente') statusClass = 'badge-warning';
            else if (item.status === 'Terminée') statusClass = 'badge-success';
            else statusClass = 'badge-retard'; // Annulée

            let actionBtn = `
                <div class="action-buttons">
                    ${item.status === 'En attente' ? `
                        <button class="action-btn" onclick="completeReservation(${item.id})" title="Marquer comme prête" style="background-color: transparent;">
                            <i class='bx bx-check' style='color: green; font-size: 1.4rem;'></i>
                        </button>
                    ` : ''}
                    ${item.status === 'Terminée' ? `
                        <button class="action-btn" onclick="createLoan(${item.id})" title="Convertir en prêt" style="background-color: transparent;">
                            <i class='bx bx-transfer' style='color: #007bff; font-size: 1.4rem;'></i>
                        </button>
                    ` : ''}
                    <button class="action-btn edit" onclick="editReservation(${item.id})" title="Modifier">
                        <i class='bx bx-edit' style='color: blue;'></i>
                    </button>
                    <button class="action-btn delete" onclick="deleteReservation(${item.id})" title="Supprimer">
                        <i class='bx bx-trash' style='color: red;'></i>
                    </button>
                </div>
            `;

            row.innerHTML = `
                <td>${item.book_title || 'N/A'}</td>
                <td>${item.reader_name || 'N/A'}</td>
                <td>${formatDate(item.reservation_date)}</td>
                <td>${formatDate(item.expiry_date)}</td>
                <td><span class="status ${statusClass}">${item.status}</span></td>
                <td>${actionBtn}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    // Initial Load
    fetchReservations();

    // 2. Populate Dropdowns
    function populateSelects() {
        return Promise.all([
            fetch('/api/livres?action=fetch').then(r => r.json()),
            fetch('/api/lecteurs?action=fetch').then(r => r.json())
        ]).then(([books, readers]) => {
            bookSelect.innerHTML = '<option value="">Choisir un livre...</option>';
            books.forEach(book => {
                if (book.available_copies === 0) {
                    bookSelect.innerHTML += `<option value="${book.id}">${book.title}</option>`;
                }
            });

            readerSelect.innerHTML = '<option value="">Choisir un lecteur...</option>';
            readers.forEach(reader => {
                readerSelect.innerHTML += `<option value="${reader.id}">${reader.first_name} ${reader.last_name}</option>`;
            });
        }).catch(err => console.error('Error loading data:', err));
    }

    // 3. Modal Logic
    // Listener updated in specific logic block below

    close.addEventListener('click', () => {
        modal.style.display = "none";
    });

    window.addEventListener('click', (e) => {
        if (e.target == modal) {
            modal.style.display = "none";
        }
    });

    let isEditing = false;
    let currentId = null;

    // 4. Add/Edit Reservation Logic
    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const resData = {
            book_id: parseInt(bookSelect.value),
            reader_id: parseInt(readerSelect.value),
            id: currentId // Only used for edit
        };

        if (!resData.book_id || !resData.reader_id) {
            alert("Veuillez sélectionner un livre et un lecteur.");
            return;
        }

        const url = isEditing ? '/api/reservations/edit' : '/api/reservations/add';

        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(resData)
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    alert(isEditing ? "Réservation modifiée !" : "Réservation ajoutée !");
                    modal.style.display = "none";
                    form.reset();
                    fetchReservations();
                } else {
                    alert("Erreur: " + (result.error || 'Erreur inconnue'));
                }
            })
            .catch(err => console.error(err));
    });

    // Helper: Reset Modal
    function resetModal() {
        isEditing = false;
        currentId = null;
        form.reset();
        document.querySelector('.modal-content h2').innerText = 'Ajouter une Réservation';
    }

    // Update Btn Listener
    btn.addEventListener('click', () => {
        resetModal();
        populateSelects();
        modal.style.display = "block";
    });

    // Edit Function
    window.editReservation = function (id) {
        const item = window.allReservations.find(r => r.id == id);
        if (!item) return;

        resetModal();
        isEditing = true;
        currentId = id;
        document.querySelector('.modal-content h2').innerText = 'Modifier la Réservation';

        populateSelects(); // Usually async, but we might have data cached or we just wait. 
        // Ideally wait for selects to populate then set values. 
        // For simplicity calling it then setting timeout or just setting values if options exist.
        // Better approach: populateSelects returns promise.

        // Since populateSelects is async, let's just trigger it and wait a bit or attach logic.
        // Rewriting populateSelects to return promise would be best but let's just assume data is there if called before or we force it.
        // Actually populateSelects fetches fresh data every time.

        // Let's modify populateSelects to take a callback? 
        // Or just rely on the fact that if options are there we set them. 

        // FIX: Let's fetch selects first then set values.
        Promise.all([
            fetch('/api/livres?action=fetch').then(r => r.json()),
            fetch('/api/lecteurs?action=fetch').then(r => r.json())
        ]).then(([books, readers]) => {
            bookSelect.innerHTML = '<option value="">Choisir un livre...</option>';
            books.forEach(b => {
                if (b.available_copies === 0 || b.id === item.book_id) {
                    bookSelect.innerHTML += `<option value="${b.id}">${b.title}</option>`;
                }
            });

            readerSelect.innerHTML = '<option value="">Choisir un lecteur...</option>';
            readers.forEach(r => readerSelect.innerHTML += `<option value="${r.id}">${r.first_name} ${r.last_name}</option>`);

            // Set Values
            bookSelect.value = item.book_id;
            readerSelect.value = item.reader_id;

            modal.style.display = "block";
        });
    }

    // 5. Create Loan from Reservation (Global scope)
    window.createLoan = function (id) {
        if (confirm('Voulez-vous transformer cette réservation en prêt actif ?')) {
            const formData = new FormData();
            formData.append('id', id);

            fetch('/api/reservations/convert', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        alert("La réservation a été convertie en prêt avec succès. Redirection vers les prêts...");
                        window.location.href = '/prets';
                    } else {
                        alert("Erreur: " + (result.error || 'Erreur inconnue'));
                    }
                })
                .catch(err => console.error(err));
        }
    }

    // New: Mark as Terminée
    window.completeReservation = function (id) {
        if (confirm('Marquer cette réservation comme prête ?')) {
            const formData = new FormData();
            formData.append('id', id);

            fetch('/api/reservations/complete', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        fetchReservations();
                    } else {
                        alert("Erreur: " + (result.error || 'Erreur inconnue'));
                    }
                })
                .catch(err => console.error(err));
        }
    }

    // 6. Delete Reservation (Global scope)
    window.deleteReservation = function (id) {
        if (confirm('Supprimer définitivement cette réservation ?')) {
            const formData = new FormData();
            formData.append('id', id);

            fetch('/api/reservations/delete', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        fetchReservations();
                    } else {
                        alert("Erreur: " + (result.error || 'Erreur inconnue'));
                    }
                })
                .catch(err => console.error(err));
        }
    }
});
