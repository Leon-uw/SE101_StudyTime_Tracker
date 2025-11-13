document.addEventListener('DOMContentLoaded', function() {
    // --- Element Selectors ---
    const tableBody = document.getElementById('study-table-body');
    const addRowBtn = document.getElementById('addRowBtn');
    const gradeLockBtn = document.getElementById('grade-lock-btn');
    const validationAlert = document.getElementById('validation-alert');
    const confirmationAlert = document.getElementById('confirmation-alert');
    const confirmMsg = document.getElementById('confirmation-message');
    const confirmYesBtn = document.getElementById('confirm-yes');
    const confirmNoBtn = document.getElementById('confirm-no');
    const subjectFilterDropdown = document.getElementById('subject-filter');
    
    // --- State Variables ---
    let isGradeLockOn = true;
    let rowToDelete = null;
    const subjectCategoriesMap = JSON.parse(document.body.dataset.subjectCategories || '{}');

    // --- Helper Functions ---
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
        container.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        setTimeout(() => {
            toast.classList.remove('show');
            toast.addEventListener('transitionend', () => toast.remove());
        }, 3000);
    }

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

    function showValidationAlert(messages) {
        if (!validationAlert) return;
        if (messages && messages.length > 0) {
            validationAlert.innerHTML = `<ul>${messages.map(msg => `<li>${msg}</li>`).join('')}</ul>`;
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
            const summaryHtml = `<td><strong>Summary for ${subjectName}</strong></td><td>-</td><td>${summaryData.total_hours.toFixed(1)}h (total)</td><td>-</td><td>${summaryData.average_grade.toFixed(1)}% (avg)</td><td>${summaryData.total_weight}% (graded)</td><td>-</td>`;
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

    function updateAllOpenInputsForGradeLock() {
        const allInputs = tableBody.querySelectorAll('input[name="grade"], input[name="weight"]');
        allInputs.forEach(input => {
            if (input.name === 'grade') {
                if (isGradeLockOn) {
                    input.min = 0;
                    input.max = 100;
                } else {
                    input.min = 0;
                    input.removeAttribute('max');
                }
            } else if (input.name === 'weight') {
                input.min = 0;
                input.max = 100;
            }
        });
    }
    
    function updateSubjectDropdown(newSubject) {
        if (![...subjectFilterDropdown.options].some(opt => opt.value === newSubject)) {
            const newOption = new Option(newSubject, newSubject);
            subjectFilterDropdown.add(newOption);
            document.getElementById('subject-list').appendChild(new Option(newSubject, newSubject));
        }
    }

    function updateCategoryMapAndFilter(subject, newCategory) {
        if (!subjectCategoriesMap[subject]) {
            subjectCategoriesMap[subject] = [];
        }
        if (!subjectCategoriesMap[subject].includes(newCategory)) {
            subjectCategoriesMap[subject].push(newCategory);
            subjectCategoriesMap[subject].sort();
            
            const categoryFilter = document.getElementById('category-filter');
            if (categoryFilter && subjectFilterDropdown.value === subject) {
                const newOption = new Option(newCategory, newCategory);
                categoryFilter.add(newOption);
            }
        }
    }

    async function handleSave(row) {
        if (!validateRow(row)) return;
        const logId = row.dataset.id;
        const isNew = !logId;
        const url = isNew ? '/add' : `/update/${logId}`;
        const formData = new FormData();
        row.querySelectorAll('input').forEach(input => formData.append(input.name, input.value));
        
        const currentSubjectFilter = subjectFilterDropdown ? subjectFilterDropdown.value : 'all';
        const categoryFilterDropdown = document.getElementById('category-filter');
        const currentCategoryFilter = categoryFilterDropdown ? categoryFilterDropdown.value : 'all';
        formData.append('current_filter', currentSubjectFilter);
        
        try {
            const response = await fetch(url, { method: 'POST', body: formData });
            const result = await response.json();
            if (!response.ok) { showToast(result.message, 'error'); return; }
            showToast(result.message, 'success');
            const savedLog = result.log;

            updateSubjectDropdown(savedLog.subject);
            updateCategoryMapAndFilter(savedLog.subject, savedLog.category);
            
            updateSummaryRow(result.summary, currentSubjectFilter);
            const subjectMatches = !currentSubjectFilter || currentSubjectFilter === 'all' || savedLog.subject === currentSubjectFilter;
            const categoryMatches = !currentCategoryFilter || currentCategoryFilter === 'all' || savedLog.category === currentCategoryFilter;
            
            if (!subjectMatches || !categoryMatches) {
                row.remove();
            } else {
                row.innerHTML = `<td>${savedLog.subject}</td><td><span class="category-tag"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg> ${savedLog.category}</span></td><td>${parseFloat(savedLog.study_time).toFixed(1)} hours</td><td>${savedLog.assignment_name}</td><td>${savedLog.grade !== null ? savedLog.grade + '%' : '-'}</td><td>${savedLog.weight}%</td><td><button class="action-btn edit-btn">Edit</button><button class="action-btn delete-btn">Delete</button></td>`;
                if (isNew) { row.dataset.id = savedLog.id; }
            }
        } catch (error) {
            console.error('Save failed:', error);
            showToast('A network error occurred.', 'error');
        }
    }
    
    // --- Event Listeners ---
    if (confirmNoBtn) { confirmNoBtn.addEventListener('click', hideConfirmation); }
    if (confirmYesBtn) {
        confirmYesBtn.addEventListener('click', async function() {
            if (rowToDelete) {
                const logId = rowToDelete.dataset.id;
                if (!logId) { rowToDelete.remove(); hideConfirmation(); return; }
                const currentFilter = subjectFilterDropdown ? subjectFilterDropdown.value : 'all';
                try {
                    const response = await fetch(`/delete/${logId}?current_filter=${currentFilter}`, { method: 'POST' });
                    const result = await response.json();
                    showToast(result.message, response.ok ? 'success' : 'error');
                    if (response.ok) {
                        updateSummaryRow(result.summary, currentFilter);
                        rowToDelete.remove();
                    }
                } catch (error) { console.error("Delete failed:", error); showToast("A network error occurred.", "error"); }
                finally { hideConfirmation(); }
            }
        });
    }

    if (gradeLockBtn) {
        gradeLockBtn.addEventListener('click', function() {
            isGradeLockOn = !isGradeLockOn;
            this.textContent = isGradeLockOn ? 'Grade Lock: ON' : 'Grade Lock: OFF';
            this.classList.toggle('lock-on', isGradeLockOn);
            this.classList.toggle('lock-off', !isGradeLockOn);
            updateAllOpenInputsForGradeLock();
        });
    }

    if (addRowBtn) {
        addRowBtn.addEventListener('click', function() {
            const newRow = document.createElement('tr');
            const currentSubjectFilter = subjectFilterDropdown ? subjectFilterDropdown.value : 'all';
            const categoryFilterDropdown = document.getElementById('category-filter');
            const currentCategoryFilter = categoryFilterDropdown ? categoryFilterDropdown.value : 'all';
            const subjectDefault = (currentSubjectFilter !== 'all') ? currentSubjectFilter : '';
            const categoryDefault = (currentCategoryFilter !== 'all') ? currentCategoryFilter : '';
            const subjectInputHtml = `<input type="text" name="subject" value="${subjectDefault}" placeholder="${subjectDefault ? '' : 'Type or select'}" required list="subject-list">`;
            const categoryInputHtml = `<input type="text" name="category" value="${categoryDefault}" placeholder="${categoryDefault ? '' : 'e.g., Homework'}" required list="category-suggestions">`;
            const gradeAttributes = isGradeLockOn ? 'min="0" max="100"' : 'min="0"';
            const weightAttributes = 'min="0" max="100"';
            newRow.innerHTML = `<td>${subjectInputHtml}</td><td>${categoryInputHtml}</td><td><input type="number" name="study_time" step="0.1" min="0" required></td><td><input type="text" name="assignment_name" required></td><td><input type="number" name="grade" ${gradeAttributes} placeholder="Optional"></td><td><input type="number" name="weight" ${weightAttributes} required></td><td><button class="action-btn save-btn">Save</button><button class="action-btn delete-btn">Delete</button></td>`;
            tableBody.appendChild(newRow);
            const subjectInput = newRow.querySelector('input[name="subject"]');
            if (subjectInput.value) {
                subjectInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
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
                const subjectText = cells[0].textContent.trim();
                const categoryText = cells[1].querySelector('.category-tag').textContent.trim();
                const gradeText = cells[4].textContent.trim();
                const gradeValue = gradeText === '-' ? '' : parseInt(gradeText, 10);
                const gradeAttributes = isGradeLockOn ? 'min="0" max="100"' : 'min="0"';
                const weightAttributes = 'min="0" max="100"';
                cells[0].innerHTML = `<input type="text" name="subject" value="${subjectText}" required list="subject-list">`;
                cells[1].innerHTML = `<input type="text" name="category" value="${categoryText}" required list="category-suggestions">`;
                cells[2].innerHTML = `<input type="number" name="study_time" value="${(parseFloat(cells[2].textContent) || 0).toFixed(1)}" step="0.1" min="0" required>`;
                cells[3].innerHTML = `<input type="text" name="assignment_name" value="${cells[3].textContent.trim()}" required>`;
                cells[4].innerHTML = `<input type="number" name="grade" value="${gradeValue}" ${gradeAttributes} placeholder="Optional">`;
                cells[5].innerHTML = `<input type="number" name="weight" value="${parseInt(cells[5].textContent, 10) || 0}" ${weightAttributes} required>`;
                cells[0].querySelector('input').dispatchEvent(new Event('input', { bubbles: true }));
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
            if (event.target.name === 'subject') {
                const subjectValue = event.target.value;
                const categoryDatalist = document.getElementById('category-suggestions');
                categoryDatalist.innerHTML = '';
                if (subjectValue && subjectCategoriesMap[subjectValue]) {
                    subjectCategoriesMap[subjectValue].forEach(category => {
                        const option = document.createElement('option');
                        option.value = category;
                        categoryDatalist.appendChild(option);
                    });
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