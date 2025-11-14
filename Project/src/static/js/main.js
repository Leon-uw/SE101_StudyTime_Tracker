document.addEventListener('DOMContentLoaded', function() {
    // --- Element Selectors ---
    const assignmentTableBody = document.getElementById('study-table-body');
    const categoryTableBody = document.getElementById('category-table-body');
    const addRowBtn = document.getElementById('addRowBtn');
    const addCategoryBtn = document.getElementById('addCategoryBtn');
    const gradeLockBtn = document.getElementById('grade-lock-btn');
    const validationAlert = document.getElementById('validation-alert');
    const confirmationModal = document.getElementById('confirmation-modal');
    const modalMsg = document.getElementById('modal-message');
    const confirmYesBtn = document.getElementById('modal-confirm-yes');
    const confirmNoBtn = document.getElementById('modal-confirm-no');
    const subjectFilterDropdown = document.getElementById('subject-filter');

    // --- State Variables ---
    let isGradeLockOn = true;
    let itemToDelete = {
        row: null,
        type: null
    };
    const weightCategoriesMap = JSON.parse(document.body.dataset.weightCategories || '{}');
    let weightPreviewState = new Map();
    let predictorWeightPreviewState = new Map();

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

    function showConfirmation(message, row, type) {
        itemToDelete = {
            row,
            type
        };
        modalMsg.textContent = message;
        confirmationModal.style.display = 'flex';
    }

    function hideConfirmation() {
        itemToDelete = {
            row: null,
            type: null
        };
        confirmationModal.style.display = 'none';
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
        // Do not clear global alerts here, as multiple rows might have errors.
        const inputsToValidate = row.querySelectorAll('input[required], select[required]');
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

        // Additional validation for grade lock
        const gradeInput = row.querySelector('input[name="grade"]');
        if (gradeInput && gradeInput.value && isGradeLockOn) {
            const gradeValue = parseFloat(gradeInput.value);
            if (gradeValue > 100) {
                errorMessages.push('Grade cannot exceed 100% when Grade Lock is ON.');
                gradeInput.classList.add('input-error');
            }
        }

        if (errorMessages.length > 0) {
            showValidationAlert(errorMessages);
            return false;
        }
        return true;
    }

    function updateSummaryRow(summaryData, subjectName) {
        let summaryRow = assignmentTableBody.querySelector('.summary-row');
        if (summaryData) {
            const summaryHtml = `<td><strong>Summary for ${subjectName}</strong></td><td>-</td><td>${summaryData.total_hours.toFixed(1)}h (total)</td><td>-</td><td>${summaryData.average_grade.toFixed(1)}% (avg)</td><td>${summaryData.total_weight.toFixed(2)}% (graded)</td><td>-</td>`;
            if (summaryRow) {
                summaryRow.innerHTML = summaryHtml;
            } else {
                summaryRow = document.createElement('tr');
                summaryRow.className = 'summary-row';
                summaryRow.innerHTML = summaryHtml;
                assignmentTableBody.prepend(summaryRow);
            }
        } else if (summaryRow) {
            summaryRow.remove();
        }
    }

    function applyWeightPreview(newAssignmentRow) {
        revertWeightPreview();
        const subject = newAssignmentRow.querySelector('input[name="subject"]').value;
        const category = newAssignmentRow.querySelector('select[name="category"]').value;
        if (!subject || !category) return;
        const categoryData = (weightCategoriesMap[subject] || []).find(c => c.name === category);
        if (!categoryData) return;
        const existingRows = Array.from(assignmentTableBody.querySelectorAll('tr[data-id]')).filter(row => {
            const cells = row.querySelectorAll('td');
            return cells.length > 1 && cells[0].textContent.trim() === subject && cells[1].querySelector('.category-tag').lastChild.textContent.trim() === category;
        });
        const newTotalAssessments = existingRows.length + 1;
        const newCalculatedWeight = newTotalAssessments > 0 ? (categoryData.total_weight / newTotalAssessments) : 0;
        newAssignmentRow.querySelector('input[name="weight"]').value = newCalculatedWeight.toFixed(2);
        existingRows.forEach(row => {
            const weightCell = row.querySelectorAll('td')[5];
            weightPreviewState.set(row, weightCell.innerHTML);
            weightCell.innerHTML = `<em>${newCalculatedWeight.toFixed(2)}%</em>`;
        });
    }

    function revertWeightPreview() {
        weightPreviewState.forEach((originalHtml, row) => {
            const weightCell = row.querySelectorAll('td')[5];
            if (weightCell) weightCell.innerHTML = originalHtml;
        });
        weightPreviewState.clear();
    }

    function revertPredictorWeightPreview() {
        predictorWeightPreviewState.forEach((originalHtml, row) => {
            const weightCell = row.querySelectorAll('td')[5];
            if (weightCell) weightCell.innerHTML = originalHtml;
        });
        predictorWeightPreviewState.clear();
    }

    function applyPredictorWeightPreview(subject, category) {
        revertPredictorWeightPreview();

        const predictWeight = document.getElementById('weight');

        if (!subject || !category) {
            if (predictWeight) predictWeight.value = '';
            return;
        }

        const categoryData = (weightCategoriesMap[subject] || []).find(c => c.name === category);
        if (!categoryData) {
            if (predictWeight) predictWeight.value = '';
            return;
        }

        // Find existing assignments in this subject/category
        const existingRows = Array.from(assignmentTableBody.querySelectorAll('tr[data-id]')).filter(row => {
            const cells = row.querySelectorAll('td');
            return cells.length > 1 &&
                   cells[0].textContent.trim() === subject &&
                   cells[1].querySelector('.category-tag')?.lastChild.textContent.trim() === category;
        });

        const newTotalAssessments = existingRows.length + 1;
        const newCalculatedWeight = newTotalAssessments > 0 ? (categoryData.total_weight / newTotalAssessments) : 0;

        // Set the predictor weight field
        if (predictWeight) {
            predictWeight.value = newCalculatedWeight.toFixed(2);
        }

        // Apply preview to existing assignments
        existingRows.forEach(row => {
            const weightCell = row.querySelectorAll('td')[5];
            predictorWeightPreviewState.set(row, weightCell.innerHTML);
            weightCell.innerHTML = `<em>${newCalculatedWeight.toFixed(2)}%</em>`;
        });
    }

    function renderAssignmentTable(assignments, summaryData, subject) {
        assignmentTableBody.innerHTML = '';
        if (summaryData) {
            const summaryRow = document.createElement('tr');
            summaryRow.className = 'summary-row';
            summaryRow.innerHTML = `<td><strong>Summary for ${subject}</strong></td><td>-</td><td>${summaryData.total_hours.toFixed(1)}h (total)</td><td>-</td><td>${summaryData.average_grade.toFixed(1)}% (avg)</td><td>${summaryData.total_weight.toFixed(2)}% (graded)</td><td>-</td>`;
            assignmentTableBody.appendChild(summaryRow);
        }
        assignments.forEach(log => {
            const row = document.createElement('tr');
            row.dataset.id = log.id;
            row.innerHTML = `<td>${log.subject}</td><td><span class="category-tag"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg> ${log.category}</span></td><td>${parseFloat(log.study_time).toFixed(1)} hours</td><td>${log.assignment_name}</td><td>${log.grade !== null ? log.grade + '%' : '-'}</td><td>${parseFloat(log.weight).toFixed(2)}%</td><td><button class="action-btn edit-btn">Edit</button><button class="action-btn delete-btn">Delete</button></td>`;
            assignmentTableBody.appendChild(row);
        });
    }

    function updateCategoryTableRow(subject, categoryName) {
        if (!categoryTableBody) return;
        const categoryRow = Array.from(categoryTableBody.querySelectorAll('tr')).find(r => r.dataset.name === categoryName);
        if (!categoryRow) return;
        const categoryData = (weightCategoriesMap[subject] || []).find(c => c.name === categoryName);
        if (!categoryData) return;
        const numAssessments = Array.from(assignmentTableBody.querySelectorAll('tr[data-id]')).filter(r => {
            const cells = r.querySelectorAll('td');
            return cells.length > 1 && cells[0].textContent.trim() === subject && cells[1].querySelector('.category-tag')?.lastChild.textContent.trim() === categoryName;
        }).length;
        categoryRow.querySelector('.num-assessments').textContent = numAssessments;
        const newCalculatedWeight = numAssessments > 0 ? `${(categoryData.total_weight / numAssessments).toFixed(2)}%` : 'N/A';
        categoryRow.querySelector('.calculated-weight').textContent = newCalculatedWeight;
    }

    async function handleAssignmentSave(row) {
        // --- FIX: Do not revert the preview if validation fails ---
        if (!validateRow(row)) return;
        revertWeightPreview(); // Only revert on successful validation

        const logId = row.dataset.id;
        const isNew = !logId;
        const url = isNew ? '/add' : `/update/${logId}`;
        const formData = new FormData();
        row.querySelectorAll('input, select').forEach(el => formData.append(el.name, el.value));
        const currentSubjectFilter = subjectFilterDropdown.value;
        formData.append('current_filter', currentSubjectFilter);
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if (!response.ok) {
                showToast(result.message, 'error');
                return;
            }
            showToast(result.message, 'success');
            renderAssignmentTable(result.updated_assignments, result.summary, currentSubjectFilter);
            if (isNew) {
                updateCategoryTableRow(result.log.subject, result.log.category);
            }
        } catch (error) {
            console.error('Save failed:', error);
            showToast('A network error occurred.', 'error');
        }
    }

    async function handleCategorySave(row) {
        if (!validateRow(row)) return;
        const catId = row.dataset.id;
        const isNew = !catId;
        const url = isNew ? '/category/add' : `/category/update/${catId}`;
        const formData = new FormData();
        row.querySelectorAll('input').forEach(input => formData.append(input.name, input.value));
        const subject = subjectFilterDropdown.value;
        formData.append('subject', subject);
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if (!response.ok) {
                showToast(result.message, 'error');
                return;
            }
            showToast(result.message, 'success');
            // Instead of complex logic, just reload the page to see category changes
            window.location.reload();
        } catch (error) {
            console.error('Category save failed:', error);
            showToast('A network error occurred.', 'error');
        }
    }

    if (confirmNoBtn) {
        confirmNoBtn.addEventListener('click', hideConfirmation);
    }
    if (confirmYesBtn) {
        confirmYesBtn.addEventListener('click', async function() {
            if (itemToDelete.row) {
                const {
                    row,
                    type
                } = itemToDelete;
                if (type === 'assignment' && !row.dataset.id) {
                    revertWeightPreview();
                }
                const itemId = row.dataset.id;
                if (!itemId) {
                    row.remove();
                    hideConfirmation();
                    return;
                }
                const isAssignment = type === 'assignment';
                const url = isAssignment ? `/delete/${itemId}` : `/category/delete/${itemId}`;
                const currentFilter = subjectFilterDropdown.value;
                try {
                    const response = await fetch(`${url}?current_filter=${currentFilter}`, {
                        method: 'POST'
                    });
                    const result = await response.json();
                    showToast(result.message, response.ok ? 'success' : 'error');
                    if (response.ok) {
                        if (isAssignment) {
                            renderAssignmentTable(result.updated_assignments, result.summary, currentFilter);
                            const categoryName = row.querySelectorAll('td')[1].querySelector('.category-tag').lastChild.textContent.trim();
                            updateCategoryTableRow(currentFilter, categoryName);
                        } else {
                            window.location.reload(); // Reload to see category deletion reflected
                        }
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

            // Update all grade input fields max attribute
            const allGradeInputs = document.querySelectorAll('input[name="grade"]');
            allGradeInputs.forEach(input => {
                if (isGradeLockOn) {
                    input.setAttribute('max', '100');
                } else {
                    input.removeAttribute('max');
                }
            });
        });
    }

    if (addCategoryBtn) {
        addCategoryBtn.addEventListener('click', function() {
            const newRow = document.createElement('tr');
            newRow.innerHTML = `<td><input type="text" name="name" required></td><td><input type="number" name="total_weight" min="0" max="100" required></td><td class="num-assessments">0</td><td class="calculated-weight">N/A</td><td><input type="text" name="default_name" placeholder="e.g., Quiz #"></td><td><button class="action-btn save-btn">Save</button><button class="action-btn delete-btn">Delete</button></td>`;
            categoryTableBody.appendChild(newRow);
        });
    }

    if (categoryTableBody) {
        categoryTableBody.addEventListener('click', async function(event) {
            const button = event.target.closest('.action-btn');
            if (!button) return;
            const row = button.closest('tr');
            if (button.classList.contains('edit-btn')) {
                button.textContent = 'Save';
                button.classList.remove('edit-btn');
                button.classList.add('save-btn');
                const cells = row.querySelectorAll('td');
                cells[0].innerHTML = `<input type="text" name="name" value="${cells[0].textContent.trim()}" required>`;
                cells[1].innerHTML = `<input type="number" name="total_weight" value="${parseInt(cells[1].textContent, 10) || 0}" min="0" max="100" required>`;
                cells[4].innerHTML = `<input type="text" name="default_name" value="${cells[4].textContent.trim() === '-' ? '' : cells[4].textContent.trim()}" placeholder="e.g., Quiz #">`;
            } else if (button.classList.contains('save-btn')) {
                await handleCategorySave(row);
            } else if (button.classList.contains('delete-btn')) {
                showConfirmation("Delete this category definition? This cannot be undone.", row, 'category');
            }
        });

        // --- NEW: Add keydown listener for the category table ---
        categoryTableBody.addEventListener('keydown', async function(event) {
            if (event.key === 'Enter' && event.target.matches('input')) {
                event.preventDefault();
                const row = event.target.closest('tr');
                if (row) {
                    await handleCategorySave(row);
                }
            }
        });
    }

    if (addRowBtn) {
        addRowBtn.addEventListener('click', function() {
            revertWeightPreview();
            revertPredictorWeightPreview();
            const newRow = document.createElement('tr');
            const currentSubject = subjectFilterDropdown.value;
            const subjectDefault = (currentSubject !== 'all') ? currentSubject : '';
            const gradeAttrs = isGradeLockOn ? 'min="0" max="100"' : 'min="0"';
            const categorySelect = document.createElement('select');
            categorySelect.name = 'category';
            categorySelect.required = true;
            categorySelect.innerHTML = `<option value="" disabled selected>Select subject first</option>`;
            const td = document.createElement('td');
            td.appendChild(categorySelect);
            newRow.innerHTML = `<td><input type="text" name="subject" value="${subjectDefault}" placeholder="${subjectDefault ? '' : 'Type or select'}" required list="subject-list"></td>${td.outerHTML}<td><input type="number" name="study_time" step="0.1" min="0" required></td><td><input type="text" name="assignment_name" required></td><td><input type="number" name="grade" ${gradeAttrs} placeholder="Optional"></td><td><input type="number" name="weight" required readonly style="background-color: #eee;"></td><td><button class="action-btn save-btn">Save</button><button class="action-btn delete-btn">Delete</button></td>`;
            assignmentTableBody.appendChild(newRow);
            const subjectInput = newRow.querySelector('input[name="subject"]');
            if (subjectInput.value) {
                subjectInput.dispatchEvent(new Event('change', {
                    bubbles: true
                }));
            }
        });
    }

    if (assignmentTableBody) {
        assignmentTableBody.addEventListener('click', async function(event) {
            const button = event.target.closest('.action-btn');
            if (!button) return;
            const row = button.closest('tr');
            if (button.classList.contains('edit-btn')) {
                revertWeightPreview();
                revertPredictorWeightPreview();
                button.textContent = 'Save';
                button.classList.remove('edit-btn');
                button.classList.add('save-btn');
                const cells = row.querySelectorAll('td');
                const subjectText = cells[0].textContent.trim();
                const categoryText = cells[1].querySelector('.category-tag').lastChild.textContent.trim();
                const gradeText = cells[4].textContent.trim();
                const gradeValue = gradeText === '-' ? '' : parseInt(gradeText, 10);
                const gradeAttributes = isGradeLockOn ? 'min="0" max="100"' : 'min="0"';
                const categorySelect = document.createElement('select');
                categorySelect.name = 'category';
                categorySelect.required = true;
                if (weightCategoriesMap[subjectText]) {
                    weightCategoriesMap[subjectText].forEach(cat => {
                        const option = new Option(cat.name, cat.name);
                        if (cat.name === categoryText) option.selected = true;
                        categorySelect.add(option);
                    });
                }
                cells[0].innerHTML = `<input type="text" name="subject" value="${subjectText}" required list="subject-list">`;
                cells[1].innerHTML = '';
                cells[1].appendChild(categorySelect);
                cells[2].innerHTML = `<input type="number" name="study_time" value="${(parseFloat(cells[2].textContent) || 0).toFixed(1)}" step="0.1" min="0" required>`;
                cells[3].innerHTML = `<input type="text" name="assignment_name" value="${cells[3].textContent.trim()}" required>`;
                cells[4].innerHTML = `<input type="number" name="grade" value="${gradeValue}" ${gradeAttributes} placeholder="Optional">`;
                cells[5].innerHTML = `<input type="number" name="weight" value="${parseFloat(cells[5].textContent) || 0}" required readonly style="background-color: #eee;">`;
            } else if (button.classList.contains('save-btn')) {
                await handleAssignmentSave(row);
            } else if (button.classList.contains('delete-btn')) {
                showConfirmation("Are you sure you want to delete this assignment?", row, 'assignment');
            }
        });
        assignmentTableBody.addEventListener('change', function(event) {
            if (event.target.name === 'subject') {
                const subjectValue = event.target.value.trim();
                const row = event.target.closest('tr');
                const categorySelect = row.querySelector('select[name="category"]');
                if (!categorySelect) return;

                // Clear existing options
                categorySelect.innerHTML = '<option value="" disabled selected>Select category</option>';

                // Add categories if they exist
                if (subjectValue && weightCategoriesMap[subjectValue]) {
                    weightCategoriesMap[subjectValue].forEach(catObj => {
                        const option = new Option(catObj.name, catObj.name);
                        categorySelect.add(option);
                    });
                }
            }
        });
        assignmentTableBody.addEventListener('change', function(event) {
            const target = event.target;
            if (target.name === 'category') {
                const row = target.closest('tr');
                if (!row.dataset.id) {
                    applyWeightPreview(row);
                }
                const subject = row.querySelector('input[name="subject"]').value;
                const categoryName = target.value;
                const categoryData = (weightCategoriesMap[subject] || []).find(c => c.name === categoryName);
                if (categoryData) {
                    const nameInput = row.querySelector('input[name="assignment_name"]');
                    if (categoryData.default_name) {
                        if (categoryData.default_name.includes('#')) {
                            const existingCount = Array.from(document.querySelectorAll('#study-table-body tr[data-id]')).filter(r => r.querySelectorAll('td')[1].textContent.trim().includes(categoryName)).length;
                            nameInput.value = categoryData.default_name.replace('#', existingCount + 1);
                        } else {
                            nameInput.value = categoryData.default_name;
                        }
                    }
                }
            }
        });
        assignmentTableBody.addEventListener('keydown', async function(event) {
            if (event.key === 'Enter' && event.target.matches('input, select')) {
                event.preventDefault();
                showValidationAlert([]); // Clear old errors before trying to save all
                const editedRows = assignmentTableBody.querySelectorAll('tr:has(.save-btn)');
                for (const row of editedRows) {
                    await handleAssignmentSave(row);
                }
            }
        });
    }

    const ctx = document.getElementById('hoursPieChart');
    if (ctx) {
        try {
            const chartLabels = JSON.parse(document.body.dataset.chartLabels);
            const chartValues = JSON.parse(document.body.dataset.chartValues);
            if (chartLabels && chartLabels.length > 0) {
                new Chart(ctx.getContext('2d'), {
                    type: 'pie',
                    data: {
                        labels: chartLabels,
                        datasets: [{
                            label: 'Hours Studied',
                            data: chartValues,
                            backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40'],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top'
                            }
                        }
                    }
                });
            }
        } catch (e) {
            console.error("Failed to parse chart data:", e);
        }
    }

    // Get the predictor form elements
    const predictSubject = document.getElementById('predict-subject');
    const predictCategory = document.getElementById('predict-category');

    // Function to clear predictor fields
    function clearPredictorFields(keepSubject = false) {
        if (!keepSubject) {
            predictCategory.innerHTML = '<option value="">-- Select Category --</option>';
        }
        document.getElementById('assignment_name').value = '';
        document.getElementById('weight').value = '';
        document.getElementById('hours').value = '';
        document.getElementById('target_grade').value = '';
        document.getElementById('prediction-result').textContent = '';
        revertPredictorWeightPreview();
    }

    // Function to populate category dropdown based on selected subject
    function updatePredictorCategories() {
        const selectedSubject = predictSubject.value;
        const categoryObjs = weightCategoriesMap[selectedSubject] || [];

        // Clear existing options
        predictCategory.innerHTML = '';

        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = '-- Select Category --';
        predictCategory.appendChild(defaultOption);

        // Add category options - extract names from category objects
        categoryObjs.forEach(catObj => {
            const option = new Option(catObj.name, catObj.name);
            predictCategory.add(option);
        });

        // Clear all other fields when subject changes
        clearPredictorFields(true);
    }

    // Initialize categories on page load
    if (predictSubject && predictCategory) {
        updatePredictorCategories();

        // Update categories when subject changes
        predictSubject.addEventListener('change', updatePredictorCategories);

        // Update weight preview when category changes
        predictCategory.addEventListener('change', function() {
            const subject = predictSubject.value;
            const category = predictCategory.value;

            // Clear fields except subject and category when category changes
            document.getElementById('assignment_name').value = '';
            document.getElementById('hours').value = '';
            document.getElementById('target_grade').value = '';
            document.getElementById('prediction-result').textContent = '';

            // Apply weight preview
            applyPredictorWeightPreview(subject, category);
        });
    }

    // Handle the predictor button click
    const predictBtn = document.getElementById('predict-btn');
    if (predictBtn) {
        predictBtn.addEventListener('click', async () => {
            const resultDiv = document.getElementById('prediction-result');

            // Get input values
            const subject = document.getElementById('predict-subject').value;
            const category = document.getElementById('predict-category').value;
            const assignmentName = document.getElementById('assignment_name').value;
            const weight = document.getElementById('weight').value;
            const hours = document.getElementById('hours').value;
            const targetGrade = document.getElementById('target_grade').value;

            // Validate positive values
            if (weight && parseFloat(weight) < 0) {
                resultDiv.textContent = 'Error: Weight must be a positive number';
                resultDiv.style.color = 'red';
                resultDiv.style.backgroundColor = '#f8d7da';
                resultDiv.style.border = '1px solid #f5c6cb';
                return;
            }
            if (hours && parseFloat(hours) < 0) {
                resultDiv.textContent = 'Error: Hours must be a positive number';
                resultDiv.style.color = 'red';
                resultDiv.style.backgroundColor = '#f8d7da';
                resultDiv.style.border = '1px solid #f5c6cb';
                return;
            }
            if (targetGrade && parseFloat(targetGrade) < 0) {
                resultDiv.textContent = 'Error: Target grade must be a positive number';
                resultDiv.style.color = 'red';
                resultDiv.style.backgroundColor = '#f8d7da';
                resultDiv.style.border = '1px solid #f5c6cb';
                return;
            }

            // Validate that either hours OR target_grade is provided (not both, not neither)
            if ((!hours && !targetGrade) || (hours && targetGrade)) {
                resultDiv.textContent = 'Error: Please provide either Hours OR Target Grade (not both)';
                resultDiv.style.color = 'red';
                resultDiv.style.backgroundColor = '#f8d7da';
                resultDiv.style.border = '1px solid #f5c6cb';
                return;
            }

            // Create FormData
            const formData = new FormData();
            formData.append('subject', subject);
            if (category) formData.append('category', category);
            if (assignmentName) formData.append('assignment_name', assignmentName);
            if (weight) formData.append('weight', weight);
            if (hours) formData.append('hours', hours);
            if (targetGrade) formData.append('target_grade', targetGrade);
            formData.append('grade_lock', isGradeLockOn ? 'true' : 'false');

            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    if (data.mode === 'grade_from_hours') {
                        resultDiv.textContent = `Predicted Grade: ${data.predicted_grade}%`;
                        resultDiv.style.color = '#155724';
                        resultDiv.style.backgroundColor = '#d4edda';
                        resultDiv.style.border = '1px solid #c3e6cb';
                    } else if (data.mode === 'hours_from_grade') {
                        resultDiv.textContent = `Required Hours: ${data.required_hours} hours`;
                        resultDiv.style.color = '#004085';
                        resultDiv.style.backgroundColor = '#d1ecf1';
                        resultDiv.style.border = '1px solid #bee5eb';
                    }
                } else {
                    resultDiv.textContent = data.message || 'Error making prediction';
                    resultDiv.style.color = 'red';
                    resultDiv.style.backgroundColor = '#f8d7da';
                    resultDiv.style.border = '1px solid #f5c6cb';
                }
            } catch (error) {
                resultDiv.textContent = 'Error: ' + error.message;
                resultDiv.style.color = 'red';
                resultDiv.style.backgroundColor = '#f8d7da';
                resultDiv.style.border = '1px solid #f5c6cb';
            }
        });
    }

    // --- Add Subject Button Handler ---
    const addSubjectBtn = document.getElementById('add-subject-btn');
    if (addSubjectBtn) {
        addSubjectBtn.addEventListener('click', function() {
            const subjectName = prompt('Enter new subject name:');
            if (!subjectName || !subjectName.trim()) {
                return;
            }

            fetch('/add_subject', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: new URLSearchParams({subject_name: subjectName.trim()})
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Navigate to the new subject's filter page
                    window.location.href = '/?subject=' + encodeURIComponent(data.subject);
                } else {
                    showToast(data.message, 'error');
                }
            })
            .catch(error => {
                showToast('Error adding subject: ' + error.message, 'error');
            });
        });
    }

    // --- Delete Subject Button Handler with Double Confirmation ---
    const deleteSubjectBtn = document.getElementById('delete-subject-btn');
    if (deleteSubjectBtn) {
        deleteSubjectBtn.addEventListener('click', function() {
            const subjectName = this.dataset.subject;

            // First confirmation
            const firstConfirm = confirm(`Are you sure you want to delete the subject "${subjectName}"?\n\nThis will delete ALL assignments and categories for this subject.\n\nClick OK to continue.`);

            if (!firstConfirm) {
                return;
            }

            // Second confirmation
            const secondConfirm = confirm(`FINAL WARNING: This action cannot be undone!\n\nDelete "${subjectName}" and all its data permanently?`);

            if (!secondConfirm) {
                return;
            }

            // Proceed with deletion
            fetch('/delete_subject', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: new URLSearchParams({subject_name: subjectName})
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showToast(data.message, 'success');
                    // Navigate back to "All Subjects" view
                    window.location.href = '/';
                } else {
                    showToast(data.message, 'error');
                }
            })
            .catch(error => {
                showToast('Error deleting subject: ' + error.message, 'error');
            });
        });
    }

});