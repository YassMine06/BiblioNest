document.addEventListener('DOMContentLoaded', () => {
    const penaltiesGrid = document.getElementById('penaltiesGrid');

    // 1. Fetch Penalties from Server
    function fetchPenalties() {
        penaltiesGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center;">Chargement...</div>';
        fetch('/api/penalites?action=fetch')
            .then(response => response.json())
            .then(data => {
                window.allPenalties = data;
                renderPenalties(data);
            })
            .catch(error => {
                console.error('Error:', error);
                penaltiesGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: red;">Erreur de chargement des pénalités.</div>';
            });
    }

    function renderPenalties(data) {
        penaltiesGrid.innerHTML = "";
        if (data.length === 0) {
            penaltiesGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #666;">Aucune pénalité enregistrée.</div>';
            return;
        }

        data.forEach(item => {
            const card = document.createElement('div');
            card.className = 'penalty-card';

            const isPaid = item.status === 'Payé';
            const statusClass = isPaid ? 'status-paid' : 'status-unpaid';
            const amountClass = isPaid ? 'paid' : '';

            card.innerHTML = `
                <div class="penalty-header">
                    <div class="penalty-amount ${amountClass}">${parseFloat(item.amount).toFixed(2)} <span style="font-size: 0.8rem;">DH</span></div>
                    <span class="penalty-status ${statusClass}">${item.status}</span>
                </div>
                <div class="penalty-body">
                    <div class="reader-name"><i class='bx bx-user'></i> ${item.reader_name || 'Inconnu'}</div>
                    <h4>Motif</h4>
                    <p>${item.reason}</p>
                </div>
                <div class="penalty-actions">
                    <div class="info-icon-wrapper">
                        <i class='bx bx-info-circle'></i>
                        <div class="info-tooltip">
                            <div class="tooltip-item"><strong>Livre:</strong> ${item.book_title || 'N/A'}</div>
                            ${item.days_late > 0 ? `<div class="tooltip-item"><strong>Retard:</strong> ${item.days_late} jours</div>` : ''}
                            ${item.calculation_text ? `<div class="tooltip-item"><strong>Calcul:</strong> ${item.calculation_text}</div>` : ''}
                            <div class="tooltip-item"><strong>Type:</strong> ${item.penalty_type}</div>
                        </div>
                    </div>
                    <div class="actions-buttons">
                        ${!isPaid ? `
                            <button class="action-btn pay" onclick="payPenalty(${item.id})" title="Marquer comme payé">
                                <i class='bx bx-check-circle'></i>
                            </button>
                        ` : ''}
                        <button class="action-btn edit" onclick="editPenalty(${item.id})" title="Modifier">
                            <i class='bx bx-edit'></i>
                        </button>
                        <button class="action-btn delete" onclick="deletePenalty(${item.id})" title="Supprimer">
                            <i class='bx bx-trash'></i>
                        </button>
                    </div>
                </div>
            `;
            penaltiesGrid.appendChild(card);
        });
    }

    // Initial Load
    fetchPenalties();

    // 3. Populate Dropdowns (Types & Readers)
    function populateSelects() {
        return Promise.all([
            fetch('/api/penalites?action=fetch_readers').then(res => res.json()),
            fetch('/api/penalites?action=fetch_types').then(res => res.json()),
            fetch('/api/livres?action=fetch').then(res => res.json())
        ]).then(([readers, types, books]) => {
            const readerSelect = document.getElementById('readerSelect');
            const typeSelect = document.getElementById('typeSelect');
            const bookSelect = document.getElementById('bookSelect');

            readerSelect.innerHTML = '<option value="">Choisir un lecteur</option>';
            readers.forEach(r => {
                const opt = document.createElement('option');
                opt.value = r.id;
                opt.textContent = r.full_name;
                readerSelect.appendChild(opt);
            });

            typeSelect.innerHTML = '<option value="">Choisir un type</option>';
            types.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.id;
                opt.textContent = t.label;
                opt.dataset.amount = t.fixed_amount;
                opt.dataset.rate = t.daily_rate;
                opt.dataset.label = t.label; // Store label for logic
                typeSelect.appendChild(opt);
            });

            if(bookSelect) {
                bookSelect.innerHTML = '<option value="">Aucun livre associé</option>';
                books.forEach(b => {
                    const opt = document.createElement('option');
                    opt.value = b.id;
                    opt.textContent = b.title;
                    opt.dataset.price = b.price;
                    bookSelect.appendChild(opt);
                });
            }
        });
    }

    // Amount auto-fill logic
    // Amount auto-fill logic
    function calculateAmount() {
        const typeSelect = document.getElementById('typeSelect');
        const bookSelect = document.getElementById('bookSelect');
        const amountInput = document.getElementById('amount');
        const reasonInput = document.getElementById('reason');

        const selectedType = typeSelect.options[typeSelect.selectedIndex];
        const selectedBook = bookSelect.options[bookSelect.selectedIndex];

        if (!selectedType || !selectedType.value) return;

        const fixedAmount = parseFloat(selectedType.dataset.amount || 0);
        const dailyRate = parseFloat(selectedType.dataset.rate || 0);
        const label = selectedType.dataset.label || '';
        const bookPrice = selectedBook && selectedBook.value ? parseFloat(selectedBook.dataset.price || 0) : 0;

        // Custom Logic: If "Perte", Amount = Book Price + Fixed Amount
        if (label.toLowerCase().includes('perte')) {
            amountInput.value = (fixedAmount + bookPrice).toFixed(2);
        } else {
            // Standard Logic
            if (fixedAmount > 0) {
                amountInput.value = fixedAmount;
            } else if (dailyRate > 0) {
                amountInput.value = dailyRate;
            }
        }

        if (reasonInput.value === '' || reasonInput.value === selectedType.text) {
             reasonInput.value = selectedType.text; // Default reason
        }
    }

    document.getElementById('typeSelect').addEventListener('change', calculateAmount);
    document.getElementById('bookSelect').addEventListener('change', calculateAmount);

    // 4. Modal Logic
    const modal = document.getElementById('penModal');
    const addBtn = document.getElementById('addPenBtn');
    const closeBtn = document.querySelector('.close-modal');
    const form = document.getElementById('addPenForm');

    let isEditing = false;
    let currentId = null;

    function resetModal() {
        isEditing = false;
        currentId = null;
        form.reset();
        document.querySelector('.modal-content h2').innerText = 'Ajouter une Pénalité';
        // Hide status field for new penalties if added to modal, but kept simple for now
    }

    if (addBtn) {
        addBtn.addEventListener('click', () => {
            resetModal();
            populateSelects().then(() => {
                modal.style.display = "block";
            });
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = "none";
        });
    }

    window.addEventListener('click', (e) => {
        if (e.target == modal) {
            modal.style.display = "none";
        }
    });

    // 5. Add/Edit Penalty Submit
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();

            const action = isEditing ? 'edit' : 'add';
            const data = {
                id: currentId,
                reader_id: document.getElementById('readerSelect').value,
                book_id: document.getElementById('bookSelect').value, // NEW
                penalty_type_id: document.getElementById('typeSelect').value,
                reason: document.getElementById('reason').value,
                amount: document.getElementById('amount').value,
                status: isEditing ? (window.allPenalties.find(p => p.id == currentId).status) : 'Impayé'
            };

            fetch(`/api/penalites/${action}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
                .then(res => res.json())
                .then(result => {
                    if (result.success) {
                        alert(isEditing ? "Pénalité modifiée !" : "Pénalité ajoutée !");
                        modal.style.display = "none";
                        form.reset();
                        fetchPenalties();
                    } else {
                        alert("Erreur: " + result.error);
                    }
                })
                .catch(err => console.error(err));
        });
    }

    // Edit Function
    window.editPenalty = function (id) {
        const item = window.allPenalties.find(p => p.id == id);
        if (!item) return;

        resetModal();
        isEditing = true;
        currentId = id;
        document.querySelector('.modal-content h2').innerText = 'Modifier la Pénalité';

        populateSelects().then(() => {
            document.getElementById('readerSelect').value = item.reader_id;
            document.getElementById('typeSelect').value = item.penalty_type_id || "";
            document.getElementById('reason').value = item.reason;
            document.getElementById('amount').value = item.amount;
            modal.style.display = "block";
        });
    };

    // Delete Function
    window.deletePenalty = function (id) {
        if (confirm("Supprimer cette pénalité ?")) {
            const formData = new FormData();
            formData.append('id', id);

            fetch('/api/penalites/delete', {
                method: 'POST',
                body: formData
            })
                .then(res => res.json())
                .then(result => {
                    if (result.success) {
                        fetchPenalties();
                    } else {
                        alert("Erreur: " + result.error);
                    }
                })
                .catch(err => console.error(err));
        }
    };

    // Pay Function
    window.payPenalty = function (id) {
        if (confirm("Marquer cette pénalité comme payée ?")) {
            const formData = new FormData();
            formData.append('id', id);

            fetch('/api/penalites/pay', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        alert("Pénalité payée !");
                        fetchPenalties();
                    } else {
                        alert("Erreur: " + (result.error || 'Erreur inconnue'));
                    }
                })
                .catch(err => console.error(err));
        }
    };
});
