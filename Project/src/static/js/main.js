document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.getElementById('study-table-body');
    const addRowBtn = document.getElementById('addRowBtn');

    function showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = type;
        toast.classList.add('show');
        setTimeout(() => { toast.classList.remove('show'); }, 3000);
    }

    function validateRow(row) {
        const invalidFields = [];
        const requiredInputs = row.querySelectorAll('input[required]');
        requiredInputs.forEach(input => {
            input.classList.remove('input-error');
            if (input.value.trim() === '') {
                const fieldName = input.name.replace('_', ' ');
                invalidFields.push(fieldName.charAt(0).toUpperCase() + fieldName.slice(1));
                input.classList.add('input-error');
            }
        });
        if (invalidFields.length > 0) {
            alert(`Please fill out all required fields:\n- ${invalidFields.join('\n- ')}`);
            return false;
        }
        return true;
    }

    function updateSummaryRow(summaryData, subjectName) {
        let summaryRow = tableBody.querySelector('.summary-row');
        if (summaryData) {
            const summaryHtml = `
                <td><strong>Summary for ${subjectName}</strong></td>
                <td>${summaryData.total_hours.toFixed(1)}h (total)</td>
                <td>-</td>
                <td>${summaryData.average_grade.toFixed(1)}% (avg)</td>
                <td>${summaryData.total_weight}% (graded)</td>
                <td>-</td>
            `;
            if (summaryRow) {
                summaryRow.innerHTML = summaryHtml;
            } else {
                summaryRow = document.createElement('tr');
                summaryRow.className = 'summary-row';
                summaryRow.innerHTML = summaryHtml;
                tableBody.prepend(summaryRow);
            }
        } else if (summaryRow) {
            summaryRow.remove();
        }
    }

    async function handleSave(row) {
        if (!validateRow(row)) return;

        const logId = row.dataset.id;
        const isNew = !logId;
        const url = isNew ? '/add' : `/update/${logId}`;
        const formData = new FormData();
        row.querySelectorAll('input').forEach(input => formData.append(input.name, input.value));
        const filterDropdown = document.getElementById('subject-filter');
        const currentFilter = filterDropdown ? filterDropdown.value : 'all';
        formData.append('current_filter', currentFilter);

        try {
            const response = await fetch(url, { method: 'POST', body: formData });
            const result = await response.json();
            if (!response.ok) { showToast(result.message, 'error'); return; }

            showToast(result.message, 'success');
            const savedLog = result.log;

            updateSummaryRow(result.summary, currentFilter);

            if (currentFilter && currentFilter !== 'all' && savedLog.subject !== currentFilter) {
                row.remove();
            } else {
                row.innerHTML = `<td>${savedLog.subject}</td><td>${parseFloat(savedLog.study_time).toFixed(1)} hours</td><td>${savedLog.assignment_name}</td><td>${savedLog.grade !== null ? savedLog.grade + '%' : '-'}</td><td>${savedLog.weight}%</td><td><button class="action-btn edit-btn">Edit</button><button class="action-btn delete-btn">Delete</button></td>`;
                if (isNew) { row.dataset.id = savedLog.id; }
            }
        } catch (error) {
            console.error('Save failed:', error);
            showToast('A network error occurred.', 'error');
        }
    }
    
    if (addRowBtn) {
        addRowBtn.addEventListener('click', function() {
            const newRow = document.createElement('tr');
            const filterDropdown = document.getElementById('subject-filter');
            const currentFilter = filterDropdown ? filterDropdown.value : 'all';
            const defaultValue = (currentFilter && currentFilter !== 'all') ? currentFilter : '';
            const placeholderText = defaultValue ? '' : 'Type or select a subject';
            const subjectInputHtml = `<input type="text" name="subject" value="${defaultValue}" placeholder="${placeholderText}" required list="subject-list">`;
            
            newRow.innerHTML = `<td>${subjectInputHtml}</td><td><input type="number" name="study_time" step="0.1" min="0" required></td><td><input type="text" name="assignment_name" required></td><td><input type="number" name="grade" min="0" max="100" placeholder="Optional"></td><td><input type="number" name="weight" min="0" max="100" required></td><td><button class="action-btn save-btn">Save</button><button class="action-btn delete-btn">Delete</button></td>`;
            tableBody.appendChild(newRow);
        });
    }

    if (tableBody) {
        tableBody.addEventListener('click', async function (event) {
            if (!event.target.classList.contains('action-btn')) return;
            const button = event.target;
            const row = button.closest('tr');

            if (button.classList.contains('edit-btn')) {
                button.textContent = 'Save';
                button.classList.remove('edit-btn');
                button.classList.add('save-btn');
                const cells = row.querySelectorAll('td');
                const gradeText = cells[3].textContent.trim();
                const gradeValue = gradeText === '-' ? '' : parseInt(gradeText, 10);
                cells[0].innerHTML = `<input type="text" name="subject" value="${cells[0].textContent.trim()}" required list="subject-list">`;
                cells[1].innerHTML = `<input type="number" name="study_time" value="${(parseFloat(cells[1].textContent) || 0).toFixed(1)}" step="0.1" min="0" required>`;
                cells[2].innerHTML = `<input type="text" name="assignment_name" value="${cells[2].textContent.trim()}" required>`;
                cells[3].innerHTML = `<input type="number" name="grade" value="${gradeValue}" min="0" max="100" placeholder="Optional">`;
                cells[4].innerHTML = `<input type="number" name="weight" value="${parseInt(cells[4].textContent, 10) || 0}" min="0" max="100" required>`;
            } else if (button.classList.contains('save-btn')) {
                await handleSave(row);
            } else if (button.classList.contains('delete-btn')) {
                if (confirm("Are you sure you want to delete this assignment?")) {
                    const logId = row.dataset.id;
                    if (!logId) { row.remove(); return; }
                    
                    const filterDropdown = document.getElementById('subject-filter');
                    const currentFilter = filterDropdown ? filterDropdown.value : 'all';
                    
                    const response = await fetch(`/delete/${logId}?current_filter=${currentFilter}`, { method: 'POST' });
                    const result = await response.json();
                    
                    showToast(result.message, response.ok ? 'success' : 'error');
                    
                    if (response.ok) {
                        updateSummaryRow(result.summary, currentFilter);
                        row.remove();
                    }
                }
            }
        });

        tableBody.addEventListener('keydown', async function(event) {
            if (event.key === 'Enter' && event.target.matches('input')) {
                event.preventDefault();
                await handleSave(event.target.closest('tr'));
            }
        });
    }

    const ctx = document.getElementById('hoursPieChart');
    if (ctx) {
        try {
            const chartLabels = JSON.parse(document.body.dataset.chartLabels);
            const chartValues = JSON.parse(document.body.dataset.chartValues);
            if (chartLabels && chartLabels.length > 0) {
                new Chart(ctx.getContext('2d'), { type: 'pie', data: { labels: chartLabels, datasets: [{ label: 'Hours Studied', data: chartValues, backgroundColor: ['#ff6384','#36a2eb','#ffce56','#4bc0c0','#9966ff','#ff9f40'], borderWidth: 1 }] }, options: { responsive: true, plugins: { legend: { position: 'top' } } } });
            }
        } catch (e) {
            console.error("Failed to parse chart data:", e);
        }
    }
});