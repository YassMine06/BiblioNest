document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('returnsTableBody');

    // 1. Fetch Returns History from Server
    function fetchReturns() {
        tableBody.innerHTML = "<tr><td colspan='4' style='text-align:center'>Chargement...</td></tr>";
        fetch('/api/retours?action=fetch')
            .then(response => response.json())
            .then(data => {
                window.allReturns = data;
                renderTable(data);
            })
            .catch(error => {
                console.error('Error:', error);
                tableBody.innerHTML = "<tr><td colspan='4' style='text-align:center; color:red'>Erreur de chargement.</td></tr>";
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
            tableBody.innerHTML = "<tr><td colspan='5' style='text-align:center'>Aucun retour enregistré.</td></tr>";
            return;
        }

        data.forEach(item => {
            const row = document.createElement('tr');

            // Determine condition based on late days
            let condition = 'À temps';
            let conditionClass = 'badge-success';
            let daysLateDisplay = '-';

            if (item.days_late > 0) {
                condition = 'En retard';
                conditionClass = 'badge-retard';
                daysLateDisplay = `<span style="color:red; font-weight:bold;">${item.days_late} jours</span>`;
            }

            row.innerHTML = `
                <td>${item.book_title || 'N/A'}</td>
                <td>${item.reader_name || 'N/A'}</td>
                <td>${formatDate(item.returned_at)}</td>
                <td>${daysLateDisplay}</td>
                <td><span class="status ${conditionClass}">${condition}</span></td>
            `;
            tableBody.appendChild(row);
        });
    }

    // Initial Load
    fetchReturns();
});
