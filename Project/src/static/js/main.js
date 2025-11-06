document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.getElementById('study-table-body');
    const addRowBtn = document.getElementById('addRowBtn');

    // --- NEW: A helper function to validate a row before saving ---
    function validateRow(row) {
        const invalidFields = [];
        const requiredInputs = row.querySelectorAll('input[required]');

        requiredInputs.forEach(input => {
            // First, remove any old error styling
            input.classList.remove('input-error');
            
            // Check if the input is empty
            if (input.value.trim() === '') {
                // Add the input's name to our list of errors
                const fieldName = input.name.replace('_', ' '); // e.g., 'study_time' -> 'study time'
                invalidFields.push(fieldName.charAt(0).toUpperCase() + fieldName.slice(1)); // Capitalize
                
                // Apply the error style to the input field
                input.classList.add('input-error');
            }
        });

        if (invalidFields.length > 0) {
            // If there are errors, show an alert and return false
            alert(`Please fill out all required fields:\n- ${invalidFields.join('\n- ')}`);
            return false;
        }

        // If all checks pass, return true
        return true;
    }

    if (addRowBtn) {
        addRowBtn.addEventListener('click', function() {
            const newRow = document.createElement('tr'); 
            newRow.innerHTML = `<td><input type="text" name="subject" required list="subject-list"></td><td><input type="number" name="study_time" step="0.1" min="0" required></td><td><input type="text" name="assignment_name" required></td><td><input type="number" name="grade" min="0" max="100" placeholder="Optional"></td><td><input type="number" name="weight" min="0" max="100" required></td><td><button class="action-btn save-btn">Save</button><button class="action-btn delete-btn">Delete</button></td>`;
            tableBody.appendChild(newRow); 
        });
    }

    if (tableBody) {
        tableBody.addEventListener('click', function (event) {
            if (!event.target.classList.contains('action-btn')) return;
            const button = event.target;
            const row = button.closest('tr');
            const logId = row.dataset.id;

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
                // --- UPDATED: Validate before submitting ---
                if (validateRow(row)) {
                    // If validation passes, submit the form
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.style.display = 'none';
                    form.action = logId ? `/update/${logId}` : `/add`;
                    row.querySelectorAll('input').forEach(input => form.appendChild(input.cloneNode()));
                    document.body.appendChild(form);
                    form.submit();
                }
            
            } else if (button.classList.contains('delete-btn')) {
                if (confirm("Are you sure you want to delete this assignment?")) {
                    if (!logId) { row.remove(); return; }
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.style.display = 'none';
                    form.action = `/delete/${logId}`;
                    document.body.appendChild(form);
                    form.submit();
                }
            }
        });

        tableBody.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && event.target.matches('input')) {
                event.preventDefault();
                const row = event.target.closest('tr');
                if (row) {
                    const saveButton = row.querySelector('.save-btn');
                    if (saveButton) {
                        saveButton.click(); // This will now trigger the click handler with the validation logic
                    }
                }
            }
        });
    }

    // Chart.js rendering logic (no changes)
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