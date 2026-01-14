document.addEventListener('DOMContentLoaded', () => {

    const searchInput = document.getElementById('searchInput');
    const addReaderBtn = document.getElementById('addReaderBtn');
    const modal = document.getElementById('readerModal');
    const closeModal = document.querySelector('.close-modal');
    const readerForm = document.getElementById('addReaderForm');
    const modalTitle = modal.querySelector('h2');

    let isEditMode = false;
    let currentReaderId = null;

    // 1. Fetch Readers from Server
    const readersGrid = document.getElementById('readersGrid');

    function fetchReaders() {
        readersGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center;">Chargement...</div>';
        fetch('/api/lecteurs?action=fetch')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                window.allReaders = data;
                renderReaders(data);
            })
            .catch(error => {
                console.error('Fetch error:', error);
                readersGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: red;">Erreur de chargement: ${error.message}</div>`;
            });
    }

    function renderReaders(data) {
        readersGrid.innerHTML = "";
        if (!data || data.length === 0) {
            readersGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center;">Aucun lecteur trouvé.</div>';
            return;
        }

        data.forEach(reader => {
            const card = document.createElement('div');
            card.className = 'reader-card';

            const statusClass = (reader.status === 'Actif') ? 'status-active' : 'status-inactive';

            // Safe initials logic
            const fName = reader.first_name || "?";
            const lName = reader.last_name || "?";
            const initials = (fName[0] + lName[0]).toUpperCase();

            card.innerHTML = `
                <div class="reader-header">
                    <div class="reader-avatar">${initials}</div>
                    <span class="reader-status ${statusClass}">${reader.status}</span>
                </div>
                <div class="reader-info">
                    <h3>${reader.first_name} ${reader.last_name}</h3>
                    <p><i class='bx bx-envelope'></i> ${reader.email}</p>
                    <p><i class='bx bx-phone'></i> ${reader.phone || 'Non renseigné'}</p>
                    <p><i class='bx bx-calendar'></i> Inscrit le ${reader.registration_date}</p>
                </div>
                <div class="reader-actions">
                    <button class="action-btn edit" onclick="window.editReader(${reader.id})" title="Modifier">
                        <i class='bx bx-edit'></i>
                    </button>
                    <button class="action-btn delete" onclick="window.deleteReader(${reader.id})" title="Supprimer">
                        <i class='bx bx-trash'></i>
                    </button>
                </div>
            `;
            readersGrid.appendChild(card);
        });
    }

    // Initial Load
    fetchReaders();

    // 2. Search Functionality
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        if (!window.allReaders) return;

        const filtered = window.allReaders.filter(reader =>
            (reader.first_name && reader.first_name.toLowerCase().includes(term)) ||
            (reader.last_name && reader.last_name.toLowerCase().includes(term)) ||
            (reader.email && reader.email.toLowerCase().includes(term))
        );
        renderReaders(filtered);
    });

    // 3. Modal Logic
    function openModal(mode = 'add', reader = null) {
        isEditMode = mode === 'edit';
        modal.style.display = "block";

        if (isEditMode && reader) {
            modalTitle.textContent = "Modifier le Lecteur";
            currentReaderId = reader.id;
            document.getElementById('firstName').value = reader.first_name;
            document.getElementById('lastName').value = reader.last_name;
            document.getElementById('email').value = reader.email;
            document.getElementById('phone').value = reader.phone || '';
            document.getElementById('status').value = reader.status || 'Actif';
        } else {
            modalTitle.textContent = "Ajouter un Lecteur";
            currentReaderId = null;
            readerForm.reset();
            document.getElementById('status').value = 'Actif';
        }
    }

    addReaderBtn.addEventListener('click', () => {
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

    // 4. Save Reader Logic (AJAX)
    readerForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const readerData = {
            first_name: document.getElementById('firstName').value,
            last_name: document.getElementById('lastName').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            status: document.getElementById('status').value
        };

        let url = '/api/lecteurs/add';
        if (isEditMode) {
            url = '/api/lecteurs/edit';
            readerData.id = currentReaderId;
        }

        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(readerData)
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    modal.style.display = "none";
                    readerForm.reset();
                    fetchReaders(); // Reload list
                } else {
                    alert("Erreur: " + (result.error || 'Erreur inconnue'));
                }
            })
            .catch(err => console.error(err));
    });

    // 5. Global Actions
    window.deleteReader = function (id) {
        if (confirm('Êtes-vous sûr de vouloir supprimer ce lecteur ?')) {
            const formData = new FormData();
            formData.append('id', id);

            fetch('/api/lecteurs/delete', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        fetchReaders(); // Reload
                    } else {
                        alert("Erreur lors de la suppression: " + (result.error || 'Erreur inconnue'));
                    }
                })
                .catch(err => console.error(err));
        }
    }

    window.editReader = function (id) {
        const reader = window.allReaders.find(r => r.id == id);
        if (reader) {
            openModal('edit', reader);
        }
    }
});
