document.addEventListener('DOMContentLoaded', function() {
    // Get all necessary elements from the DOM
    const tableBody = document.getElementById('study-table-body');
    const addRowBtn = document.getElementById('addRowBtn');
    const gradeLockBtn = document.getElementById('grade-lock-btn');
    const validationAlert = document.getElementById('validation-alert');
    const confirmationAlert = document.getElementById('confirmation-alert');
    const confirmMsg = document.getElementById('confirmation-message');
    const confirmYesBtn = document.getElementById('confirm-yes');
    const confirmNoBtn = document.getElementById('confirm-no');

    // State variables
    let isGradeLockOn = true;
    let rowToDelete = null;

    // --- Custom Confirmation Dialog Functions ---
    function showConfirmation(message, row) {
        rowToDelete = row;
        confirmMsg.textContent = message;
        confirmationAlert.style.display = 'block';
        validationAlert.style.display = 'none';
    }

    function hideConfirmation() {
        rowToDelete = null;
        confirmationAlert.style.display = 'none';
    }

    // --- Helper Functions (Toast, Validation, Summary, Save) ---
    function showToast(message, type = 'success') {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        // Optional: click to remove immediately
        toast.addEventListener('click', () => toast.remove());

        container.appendChild(toast);

        // Trigger fade after a delay
        setTimeout(() => {
            toast.style.opacity = 0;
            toast.style.transform = 'translateY(-20px)';
            setTimeout(() => toast.remove(), 500); // remove after fade
        }, 3000);
    }

    function showValidationAlert(messages) {
        if (!validationAlert) return;
        if (messages && messages.length > 0) {
            const listHtml = `<ul>${messages.map(msg => `<li>${msg}</li>`).join('')}</ul>`;
            validationAlert.innerHTML = listHtml;
            validationAlert.style.display = 'block';
        } else {
            validationAlert.innerHTML = '';
            validationAlert.style.display = 'none';
        }
    }

    function validateRow(row) {
        const errorMessages = [];
        showValidationAlert([]);
        const inputsToValidate = row.querySelectorAll('input[name]');
        inputsToValidate.forEach(input => {
            input.classList.remove('input-error');
            if (!input.checkValidity()) {
                let message = '';
                const fieldName = input.name.replace('_', ' ');
                const formattedName = fieldName.charAt(0).toUpperCase() + fieldName.slice(1);
                if (input.validity.valueMissing) {
                    message = `${formattedName} is a required field.`;
                } else if (input.validity.rangeUnderflow) {
                    message = `${formattedName} must be at least ${input.min}.`;
                } else if (input.validity.rangeOverflow) {
                    message = `${formattedName} must be no more than ${input.max}.`;
                } else {
                    message = `Please enter a valid value for ${formattedName}.`;
                }
                errorMessages.push(message);
                input.classList.add('input-error');
            }
        });
        if (errorMessages.length > 0) {
            showValidationAlert(errorMessages);
            return false;
        }
        return true;
    }
    
    function updateSummaryRow(summaryData, subjectName) {
        let summaryRow = tableBody.querySelector('.summary-row');
        if (summaryData) {
            const summaryHtml = `<td><strong>Summary for ${subjectName}</strong></td><td>${summaryData.total_hours.toFixed(1)}h (total)</td><td>-</td><td>${summaryData.average_grade.toFixed(1)}% (avg)</td><td>${summaryData.total_weight}% (graded)</td><td>-</td>`;
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
    
    // --- Event Listeners ---

    if (confirmNoBtn) {
        confirmNoBtn.addEventListener('click', hideConfirmation);
    }
    
    if (confirmYesBtn) {
        confirmYesBtn.addEventListener('click', async function() {
            if (rowToDelete) {
                const logId = rowToDelete.dataset.id;
                if (!logId) { rowToDelete.remove(); hideConfirmation(); return; }
                const filterDropdown = document.getElementById('subject-filter');
                const currentFilter = filterDropdown ? filterDropdown.value : 'all';
                try {
                    const response = await fetch(`/delete/${logId}?current_filter=${currentFilter}`, { method: 'POST' });
                    const result = await response.json();
                    showToast(result.message, response.ok ? 'success' : 'error');
                    if (response.ok) {
                        updateSummaryRow(result.summary, currentFilter);
                        rowToDelete.remove();
                    }
                } catch (error) {
                    console.error("Delete failed:", error);
                    showToast("A network error occurred.", "error");
                } finally {
                    hideConfirmation();
                }
            }
        });
    }

    if (gradeLockBtn) {
        gradeLockBtn.addEventListener('click', function() {
            isGradeLockOn = !isGradeLockOn;
            this.textContent = isGradeLockOn ? 'Grade Lock: ON' : 'Grade Lock: OFF';
            this.classList.toggle('lock-on', isGradeLockOn);
            this.classList.toggle('lock-off', !isGradeLockOn);
        });
    }

    if (addRowBtn) {
        addRowBtn.addEventListener('click', function() {
            const newRow = document.createElement('tr');
            const filterDropdown = document.getElementById('subject-filter');
            const currentFilter = filterDropdown ? filterDropdown.value : 'all';
            const defaultValue = (currentFilter && currentFilter !== 'all') ? currentFilter : '';
            const placeholderText = defaultValue ? '' : 'Type or select';
            const subjectInputHtml = `<input type="text" name="subject" value="${defaultValue}" placeholder="${placeholderText}" required list="subject-list">`;
            const gradeAttributes = isGradeLockOn ? 'min="0" max="100"' : 'min="0"';
            const weightAttributes = 'min="0" max="100"';
            newRow.innerHTML = `<td>${subjectInputHtml}</td><td><input type="number" name="study_time" step="0.1" min="0" required></td><td><input type="text" name="assignment_name" required></td><td><input type="number" name="grade" ${gradeAttributes} placeholder="Optional"></td><td><input type="number" name="weight" ${weightAttributes} required></td><td><button class="action-btn save-btn">Save</button><button class="action-btn delete-btn">Delete</button></td>`;
            tableBody.appendChild(newRow); 
        });
    }

    if (tableBody) {
        // This is the main click handler that was broken. It is now complete.
        tableBody.addEventListener('click', async function (event) {
            if (!event.target.classList.contains('action-btn')) return;
            const button = event.target;
            const row = button.closest('tr');

            // THIS IS THE RESTORED EDIT LOGIC
            if (button.classList.contains('edit-btn')) {
                button.textContent = 'Save';
                button.classList.remove('edit-btn');
                button.classList.add('save-btn');
                const cells = row.querySelectorAll('td');
                const gradeText = cells[3].textContent.trim();
                const gradeValue = gradeText === '-' ? '' : parseInt(gradeText, 10);
                const gradeAttributes = isGradeLockOn ? 'min="0" max="100"' : 'min="0"';
                const weightAttributes = 'min="0" max="100"';
                cells[0].innerHTML = `<input type="text" name="subject" value="${cells[0].textContent.trim()}" required list="subject-list">`;
                cells[1].innerHTML = `<input type="number" name="study_time" value="${(parseFloat(cells[1].textContent) || 0).toFixed(1)}" step="0.1" min="0" required>`;
                cells[2].innerHTML = `<input type="text" name="assignment_name" value="${cells[2].textContent.trim()}" required>`;
                cells[3].innerHTML = `<input type="number" name="grade" value="${gradeValue}" ${gradeAttributes} placeholder="Optional">`;
                cells[4].innerHTML = `<input type="number" name="weight" value="${parseInt(cells[4].textContent, 10) || 0}" ${weightAttributes} required>`;
            } else if (button.classList.contains('save-btn')) {
                await handleSave(row);
            } else if (button.classList.contains('delete-btn')) {
                showConfirmation("Are you sure you want to delete this assignment?", row);
            }
        });

        tableBody.addEventListener('input', function(event) {
            if (event.target.matches('input')) {
                showValidationAlert([]);
                event.target.classList.remove('input-error');
            }
        });
        
        tableBody.addEventListener('keydown', async function(event) {
            if (event.key === 'Enter' && event.target.matches('input')) {
                event.preventDefault();
                await handleSave(event.target.closest('tr'));
            }
        });
    }

    // Chart rendering logic
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