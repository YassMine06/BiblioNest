document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('loansTableBody');
    const addLoanBtn = document.getElementById('addLoanBtn');
    const modal = document.getElementById('loanModal');
    const closeModal = document.querySelector('.close-modal');
    const addLoanForm = document.getElementById('addLoanForm');
    const bookSelect = document.getElementById('bookSelect');
    const readerSelect = document.getElementById('readerSelect');

    // 1. Fetch Loans from Server
    function fetchLoans() {
        tableBody.innerHTML = "<tr><td colspan='6' style='text-align:center'>Chargement...</td></tr>";
        fetch('/api/prets?action=fetch')
            .then(response => response.json())
            .then(data => {
                window.allLoans = data;
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
            tableBody.innerHTML = "<tr><td colspan='6' style='text-align:center'>Aucun prêt actif.</td></tr>";
            return;
        }

        data.forEach(loan => {
            const row = document.createElement('tr');

            let statusClass = '';
            if (loan.status === 'En cours') statusClass = 'badge-active';
            else if (loan.status === 'Retard') statusClass = 'badge-retard';
            else statusClass = 'badge-success'; // Terminé

            row.innerHTML = `
                <td><strong>${loan.book_title || 'N/A'}</strong></td>
                <td>${loan.reader_name || 'N/A'}</td>
                <td>${formatDate(loan.loan_date)}</td>
                <td>${formatDate(loan.due_date)}</td>
                <td><span class="status ${statusClass}">${loan.status}</span></td>
                <td>
                    <div class="action-buttons">
                        ${loan.status !== 'Terminé' ? `
                        <button class="action-btn" onclick="returnBook(${loan.id})" title="Retourner">
                            <i class='bx bx-check-circle' style='color: green;'></i>
                        </button>` : ''}
                        <button class="action-btn" onclick="window.editLoan(${loan.id})" title="Modifier">
                            <i class='bx bx-edit' style='color: blue;'></i>
                        </button>
                        <button class="action-btn" onclick="window.deleteLoan(${loan.id})" title="Supprimer">
                            <i class='bx bx-trash' style='color: red;'></i>
                        </button>
                    </div>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }

    // Initial Load
    fetchLoans();

    // 2. Populate Dropdowns
    function populateSelects() {
        return fetch('/api/prets?action=fetch_options')
            .then(res => res.json())
            .then(data => {
                const books = data.books;
                const readers = data.readers;
                bookSelect.innerHTML = '<option value="">Choisir un livre...</option>';
                books.forEach(book => {
                    bookSelect.innerHTML += `<option value="${book.id}">${book.title} (${book.available_copies} dispo)</option>`;
                });

                readerSelect.innerHTML = '<option value="">Choisir un lecteur...</option>';
                readers.forEach(reader => {
                    readerSelect.innerHTML += `<option value="${reader.id}">${reader.full_name}</option>`;
                });
            }).catch(err => console.error('Error loading data:', err));
    }

    let isEditing = false;
    let currentId = null;

    // Edit Function
    window.editLoan = function (id) {
        const item = window.allLoans.find(l => l.id == id);
        if (!item) return;

        isEditing = true;
        currentId = id;
        document.querySelector('.modal-content h2').innerText = 'Modifier le Prêt';

        populateSelects().then(() => {
            bookSelect.value = item.book_id;
            readerSelect.value = item.reader_id;
            document.getElementById('loanDate').value = item.loan_date;
            document.getElementById('returnDate').value = item.due_date;
            modal.style.display = "block";
        });
    };

    // 3. Modal Logic
    addLoanBtn.addEventListener('click', () => {
        isEditing = false;
        currentId = null;
        addLoanForm.reset();
        document.querySelector('.modal-content h2').innerText = 'Enregistrer un Prêt';

        populateSelects().then(() => {
            // Set default dates based on settings
            document.getElementById('loanDate').valueAsDate = new Date();

            fetch('/api/settings')
                .then(res => res.json())
                .then(settings => {
                    const duration = parseInt(settings.default_loan_duration) || 14;
                    const returnDate = new Date();
                    returnDate.setDate(returnDate.getDate() + duration);
                    document.getElementById('returnDate').valueAsDate = returnDate;
                    modal.style.display = "block";
                })
                .catch(err => {
                    console.error(err);
                    const returnDate = new Date();
                    returnDate.setDate(returnDate.getDate() + 14);
                    document.getElementById('returnDate').valueAsDate = returnDate;
                    modal.style.display = "block";
                });
        });
    });

    closeModal.addEventListener('click', () => {
        modal.style.display = "none";
    });

    window.addEventListener('click', (e) => {
        if (e.target == modal) {
            modal.style.display = "none";
        }
    });

    // 4. Add/Edit Loan Logic (AJAX)
    addLoanForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const url = isEditing ? '/api/prets/edit' : '/api/prets/add';
        const loanData = {
            id: currentId,
            book_id: parseInt(bookSelect.value),
            reader_id: parseInt(readerSelect.value),
            loan_date: document.getElementById('loanDate').value,
            due_date: document.getElementById('returnDate').value
        };

        if (!loanData.book_id || !loanData.reader_id) {
            alert("Veuillez sélectionner un livre et un lecteur.");
            return;
        }

        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(loanData)
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    alert(isEditing ? "Prêt modifié avec succès !" : "Prêt enregistré avec succès !");
                    modal.style.display = "none";
                    addLoanForm.reset();
                    fetchLoans(); // Reload list
                } else {
                    alert("Erreur: " + (result.error || "Erreur inconnue"));
                }
            })
            .catch(err => console.error(err));
    });

    // 5. Return Book Logic (Global scope)
    window.returnBook = function (id) {
        if (confirm('Confirmer le retour de ce livre ?')) {
            const formData = new FormData();
            formData.append('id', id);

            fetch('/api/prets/return', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        alert("Livre retourné avec succès !");
                        fetchLoans(); // Reload
                    } else {
                        alert("Erreur: " + (result.error || 'Erreur inconnue'));
                    }
                })
                .catch(err => console.error(err));
        }
    }

    // 6. Delete Loan Logic
    window.deleteLoan = function (id) {
        if (confirm('Êtes-vous sûr de vouloir supprimer ce prêt ?')) {
            const formData = new FormData();
            formData.append('id', id);

            fetch('/api/prets/delete', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        fetchLoans(); // Reload
                    } else {
                        alert("Erreur: " + (result.error || 'Erreur inconnue'));
                    }
                })
                .catch(err => console.error(err));
        }
    }
});
