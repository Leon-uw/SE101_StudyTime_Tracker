document.addEventListener('DOMContentLoaded',
    function () {
        // --- Sidebar Logic ---
        const menuBtn = document.getElementById('menu-btn');
        const closeSidebarBtn = document.getElementById('close-sidebar-btn');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        const subjectsToggle = document.getElementById('subjects-toggle');
        const subjectsSubmenu = document.getElementById('subjects-submenu');

        function toggleSidebar() {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('active');
        }

        if (menuBtn) menuBtn.addEventListener('click', toggleSidebar);
        if (closeSidebarBtn) closeSidebarBtn.addEventListener('click', toggleSidebar);
        if (overlay) overlay.addEventListener('click', toggleSidebar);

        if (subjectsToggle) {
            subjectsToggle.addEventListener('click', (e) => {
                // Only prevent default if clicking directly on the toggle, not on child links
                if (e.target === subjectsToggle || e.target.closest('#subjects-toggle')) {
                    e.preventDefault();
                    subjectsToggle.parentElement.classList.toggle('active');
                }
            });
        }

        // Ensure subject links in submenu work properly
        if (subjectsSubmenu) {
            subjectsSubmenu.addEventListener('click', (e) => {
                const link = e.target.closest('a');
                if (link && link.href && !link.id.includes('add-subject')) {
                    // Allow default navigation for subject links
                    // Close sidebar after a short delay to allow navigation
                    setTimeout(() => {
                        if (sidebar && sidebar.classList.contains('open')) {
                            toggleSidebar();
                        }
                    }, 100);
                }
            });
        }

        // --- Dark Mode Logic ---
        const themeToggle = document.getElementById('theme-toggle');
        const currentTheme = localStorage.getItem('theme');

        if (currentTheme === 'dark') {
            document.body.classList.add('dark-mode');
            if (themeToggle) themeToggle.checked = true;
        }

        if (themeToggle) {
            themeToggle.addEventListener('change', () => {
                if (themeToggle.checked) {
                    document.body.classList.add('dark-mode');
                    localStorage.setItem('theme', 'dark');
                } else {
                    document.body.classList.remove('dark-mode');
                    localStorage.setItem('theme', 'light');
                }
                updateTotalWeightIndicator();
            });
        }

        // --- Auto-dismiss server-rendered toasts ---
        document.querySelectorAll('.toast.show').forEach(toast => {
            setTimeout(() => {
                toast.classList.remove('show');
                toast.addEventListener('transitionend', () => toast.remove());
            }, 4000);
        });

        // --- Element Selectors ---
        const assignmentTableBody = document.getElementById('study-table-body');
        const categoryTableBody = document.getElementById('category-table-body');
        const addRowBtn = document.getElementById('addRowBtn');
        const addCategoryBtn = document.getElementById('addCategoryBtn');
        const predictBtn = document.getElementById('predict-btn');
        const resetPredictorBtn = document.getElementById('reset-predictor-btn');
        const gradeLockBtn = document.getElementById('grade-lock-btn');
        const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
        const deselectAllBtn = document.getElementById('deselectAllBtn');
        const selectAllCheckbox = document.getElementById('selectAll');
        const validationAlert = document.getElementById('validation-alert');
        const confirmationModal = document.getElementById('confirmation-modal');
        const modalMsg = document.getElementById('modal-message');
        const confirmYesBtn = document.getElementById('modal-confirm-yes');
        const confirmNoBtn = document.getElementById('modal-confirm-no');
        const subjectFilterDropdown = document.getElementById('subject-filter');
        const subjectFilterVisible = document.getElementById('subject-filter-visible');

        // --- Subject Predictor Elements ---
        const subjectPredictorContainer = document.getElementById('subject-predictor-container');
        const predictOverallGradeInput = document.getElementById('predict-overall-grade');
        const predictStudyTimeInput = document.getElementById('predict-study-time');
        const predictorRemainingWeight = document.getElementById('predictor-remaining-weight');
        const predictorAvgNeeded = document.getElementById('predictor-avg-needed');
        const predictorMessage = document.getElementById('predictor-message');

        const triggerSubjectPredictBtn = document.getElementById('trigger-subject-predict-btn');

        // --- State Variables ---
        // Load from localStorage, default Grade Lock to true, Show Predictions to false
        let isGradeLockOn = localStorage.getItem('isGradeLockOn') !== null ? localStorage.getItem('isGradeLockOn') === 'true' : true;
        let showPredictions = localStorage.getItem('showPredictions') === 'true';

        let itemToDelete = {
            row: null,
            type: null
        };
        const weightCategoriesMap = JSON.parse(document.body.dataset.weightCategories || '{}');
        let weightPreviewState = new Map();
        let predictorWeightPreviewState = new Map();
        let allAssignmentsData = []; // Store all assignments for client-side filtering

        // ... (Helper Functions: debounce) ...



        function updateSubjectPrediction(subject) {
            const container = document.getElementById('subject-predictor-container');
            if (!container) return;

            const subjectFilterDropdown = document.getElementById('subject-filter');
            // Also check visible filter if hidden one is empty/default
            const subjectFilterVisible = document.getElementById('subject-filter-visible');

            let currentFilter = subjectFilterDropdown ? subjectFilterDropdown.value : '';
            if ((!currentFilter || currentFilter === 'all') && subjectFilterVisible) {
                currentFilter = subjectFilterVisible.value;
            }

            let targetSubject = subject || currentFilter;

            if (targetSubject && targetSubject !== 'all') {
                container.style.display = 'flex'; // Or block, depending on layout
                // Clear previous results
                if (predictorRemainingWeight) predictorRemainingWeight.textContent = '-';
                if (predictorAvgNeeded) predictorAvgNeeded.textContent = '-';
            } else {
                container.style.display = 'none';
            }
        }

        if (triggerSubjectPredictBtn) {
            triggerSubjectPredictBtn.addEventListener('click', async function () {
                const subjectFilterDropdown = document.getElementById('subject-filter');
                const subjectFilterVisible = document.getElementById('subject-filter-visible');

                let subject = subjectFilterDropdown ? subjectFilterDropdown.value : '';
                if ((!subject || subject === 'all') && subjectFilterVisible) {
                    subject = subjectFilterVisible.value;
                }

                if (!subject || subject === 'all') {
                    showToast('Please select a subject first.', 'error');
                    return;
                }

                const overallGrade = predictOverallGradeInput.value;
                const studyTime = predictStudyTimeInput.value;

                if (!overallGrade && !studyTime) {
                    showToast('Please enter a target grade or study time.', 'error');
                    return;
                }

                if ((overallGrade && parseFloat(overallGrade) < 0) || (studyTime && parseFloat(studyTime) < 0)) {
                    showToast('Values cannot be negative.', 'error');
                    return;
                }

                // Clear the OTHER input to ensure mutually exclusive prediction
                // If user entered overall grade, we predict study time (so clear study time input if it had a value? No, usually we want to fill it)
                // Actually, the user request says: "make it so when you predict a subject it shows the predicted grade or percent in the other input field and not separately"

                const formData = new FormData();
                formData.append('subject', subject);
                if (overallGrade) formData.append('target_grade', overallGrade);
                if (studyTime) formData.append('study_time', studyTime);

                // Pass the current state of "Show Predictions"
                // If true, the backend should include predicted assignments in the current grade/weight calc
                formData.append('use_predictions', showPredictions);

                try {
                    const response = await fetch('/predict_subject', {
                        method: 'POST',
                        body: formData
                    });
                    const result = await response.json();

                    if (result.status === 'success') {
                        // Clear previous error messages
                        // Clear previous results
                        // (Toast messages disappear automatically, so no need to clear a static element)

                        if (result.remaining_weight !== undefined && predictorRemainingWeight) {
                            predictorRemainingWeight.textContent = result.remaining_weight + '%';
                        }

                        // Populate the complementary field
                        if (result.predicted_additional_time !== undefined && result.predicted_additional_time !== null) {
                            predictStudyTimeInput.value = result.predicted_additional_time;
                            // Optional: Highlight it?
                        } else if (result.predicted_overall_grade !== undefined && result.predicted_overall_grade !== null) {
                            predictOverallGradeInput.value = result.predicted_overall_grade;
                        }

                        // Also show avg needed if available
                        if (predictorAvgNeeded) {
                            if (result.average_grade_needed !== undefined) {
                                predictorAvgNeeded.textContent = result.average_grade_needed + '%';
                            }
                        }

                        if (result.message) {
                            // Show non-critical messages (like "Target unreachable")
                            const type = result.message.includes('unreachable') ? 'error' : 'success';
                            showToast(result.message, type);
                        }

                    } else {
                        showToast(result.message, 'error');
                    }
                } catch (error) {
                    console.error('Prediction failed:', error);
                    showToast('Network error occurred.', 'error');
                }
            });
        }

        // Enter key support for Subject Predictor
        if (predictOverallGradeInput) {
            predictOverallGradeInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    // Clear the other input if it has a value to avoid confusion? 
                    // Or just let the button handler deal with it (it prioritizes target_grade if both present usually, or we should ensure only one is sent)
                    // For better UX, if I press enter here, I probably want to predict based on THIS value.
                    if (predictStudyTimeInput) predictStudyTimeInput.value = '';
                    triggerSubjectPredictBtn.click();
                }
            });
        }
        if (predictStudyTimeInput) {
            predictStudyTimeInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (predictOverallGradeInput) predictOverallGradeInput.value = '';
                    triggerSubjectPredictBtn.click();
                }
            });
        }

        // Initialize predictor visibility on load
        const initialSubject = subjectFilterDropdown ? subjectFilterDropdown.value : '';
        const initialVisibleSubject = subjectFilterVisible ? subjectFilterVisible.value : '';
        if (initialSubject && initialSubject !== 'all') {
            updateSubjectPrediction(initialSubject);
        } else if (initialVisibleSubject && initialVisibleSubject !== 'all') {
            updateSubjectPrediction(initialVisibleSubject);
        }

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
            // Allow HTML content for lists
            toast.innerHTML = message;
            container.appendChild(toast);

            // Trigger reflow
            void toast.offsetWidth;

            requestAnimationFrame(() => {
                toast.classList.add('show');
            });

            setTimeout(() => {
                toast.classList.remove('show');
                toast.addEventListener('transitionend', () => toast.remove());
            }, 4000); // Increased duration slightly for readability
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
            if (messages && messages.length > 0) {
                const messageHtml = `<ul style="margin: 0; padding-left: 20px; text-align: left;">${messages.map(msg => `<li>${msg}</li>`).join('')}</ul>`;
                showToast(messageHtml, 'error');
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

        function recalculateSummaryFromDOM() {
            const rows = Array.from(assignmentTableBody.querySelectorAll('tr[data-id]')); // Only data rows
            let totalTime = 0;
            let totalWeightedGrade = 0;
            let totalWeight = 0;

            rows.forEach(row => {
                // Skip if row is hidden (e.g. filtered out)
                if (row.style.display === 'none') return;

                // Check if it's a prediction row
                const isPrediction = row.classList.contains('prediction-row');
                if (isPrediction && !showPredictions) return; // Skip if predictions are hidden

                // Get values from inputs or text content
                let time = 0;
                let grade = null;
                let weight = 0;

                if (isPrediction) {
                    const timeInput = row.querySelector('.hours-input');
                    const gradeInput = row.querySelector('.grade-input');
                    // Weight is in the 7th column (index 6)
                    const weightCell = row.querySelectorAll('td')[6];

                    if (timeInput) {
                        time = parseFloat(timeInput.value) || 0;
                    }
                    if (gradeInput && gradeInput.value !== '') {
                        grade = parseFloat(gradeInput.value);
                    }
                    if (weightCell) {
                        weight = parseFloat(weightCell.textContent) || 0;
                    }
                } else {
                    // Regular row
                    // Time: 4th col (index 3) "X hours"
                    const timeCell = row.querySelectorAll('td')[3];
                    if (timeCell) {
                        time = parseFloat(timeCell.textContent) || 0;
                    }

                    // Grade: 6th col (index 5) "X%" or "-"
                    const gradeCell = row.querySelectorAll('td')[5];
                    if (gradeCell) {
                        const gradeText = gradeCell.textContent.trim();
                        if (gradeText !== '-' && gradeText !== '') {
                            grade = parseFloat(gradeText);
                        }
                    }

                    // Weight: 7th col (index 6) "X%"
                    const weightCell = row.querySelectorAll('td')[6];
                    if (weightCell) {
                        weight = parseFloat(weightCell.textContent) || 0;
                    }
                }

                totalTime += time;
                if (grade !== null) {
                    totalWeightedGrade += grade * weight;
                    totalWeight += weight;
                }
            });

            const avgGrade = totalWeight > 0 ? (totalWeightedGrade / totalWeight).toFixed(1) : '0.0';

            // Update the summary row in the DOM
            const summaryRow = document.querySelector('.summary-row');
            if (summaryRow && summaryRow.children.length >= 7) {
                // 4th col: Total Time
                if (summaryRow.children[3]) summaryRow.children[3].textContent = totalTime.toFixed(1) + 'h (total)';
                // 6th col: Avg Grade
                if (summaryRow.children[5]) summaryRow.children[5].textContent = avgGrade + '% (avg)';
                // 7th col: Total Weight
                if (summaryRow.children[6]) summaryRow.children[6].textContent = totalWeight.toFixed(2) + '% (graded)';

                // Toggle active class for styling
                const summaryCells = [summaryRow.children[3], summaryRow.children[5], summaryRow.children[6]];
                summaryCells.forEach(cell => {
                    if (cell) {
                        if (showPredictions) {
                            cell.classList.add('show-predictions-active');
                        } else {
                            cell.classList.remove('show-predictions-active');
                        }
                    }
                });
            }
        }

        // ... (applyWeightPreview, revertWeightPreview, etc.) ...

        // ... (renderAssignmentTable function - needs to call updateSummaryRow at the end) ...

        // ... (updateCategoryTableRow, updateTotalWeightIndicator, handleAssignmentSave, handleCategorySave) ...

        // ... (Confirmation Modal Listeners) ...

        if (gradeLockBtn) {
            // Initialize button state
            gradeLockBtn.textContent = isGradeLockOn ? 'Grade Lock: ON' : 'Grade Lock: OFF';
            gradeLockBtn.classList.toggle('lock-on', isGradeLockOn);
            gradeLockBtn.classList.toggle('lock-off', !isGradeLockOn);

            gradeLockBtn.addEventListener('click', function () {
                isGradeLockOn = !isGradeLockOn;
                localStorage.setItem('isGradeLockOn', isGradeLockOn); // Save state

                this.textContent = isGradeLockOn ? 'Grade Lock: ON' : 'Grade Lock: OFF';
                this.classList.toggle('lock-on', isGradeLockOn);
                this.classList.toggle('lock-off', !isGradeLockOn);

                // Remove forced styles if they were applied
                this.style.backgroundColor = '';

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

        // ... (addCategoryBtn, categoryTableBody listeners) ...

        // ... (addNewRow function) ...

        const showPredictionsBtn = document.getElementById('show-predictions-btn');

        // Toggle Show Predictions
        if (showPredictionsBtn) {
            // Initialize button state
            showPredictionsBtn.textContent = showPredictions ? 'Show Predictions: ON' : 'Show Predictions: OFF';
            showPredictionsBtn.classList.toggle('lock-on', showPredictions);
            showPredictionsBtn.classList.toggle('lock-off', !showPredictions);

            showPredictionsBtn.addEventListener('click', () => {
                showPredictions = !showPredictions;
                localStorage.setItem('showPredictions', showPredictions); // Save state

                showPredictionsBtn.textContent = showPredictions ? 'Show Predictions: ON' : 'Show Predictions: OFF';
                showPredictionsBtn.classList.toggle('lock-on', showPredictions);
                showPredictionsBtn.classList.toggle('lock-off', !showPredictions);

                // Refresh UI
                // We need to re-render to ensure "Remaining Weight" in predictor is correct
                // AND to update the summary row
                const currentSubject = subjectFilterDropdown.value;
                // Re-fetch or just re-render? 
                // Ideally we just call recalculateSummaryFromDOM and updateSubjectPrediction
                recalculateSummaryFromDOM();
                updateSubjectPrediction(null);
            });
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

        // Duplicate function removed/consolidated


        function validateRow(row) {
            const errorMessages = [];
            // Clear previous error styling first
            row.querySelectorAll('input, select').forEach(input => {
                input.classList.remove('input-error');
            });

            // Validate all required fields
            const inputsToValidate = row.querySelectorAll('input[required], select[required]');
            inputsToValidate.forEach(input => {
                if (!input.checkValidity() || (input.value && input.value.trim && input.value.trim() === '')) {
                    let message = '';
                    const fieldName = input.name.replace('_', ' ');
                    const formattedName = fieldName.charAt(0).toUpperCase() + fieldName.slice(1);
                    if (input.validity.valueMissing || (input.value && input.value.trim && input.value.trim() === '')) {
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

        function renderSummaryRow(summaryData, subjectName) {
            let summaryRow = assignmentTableBody.querySelector('.summary-row');
            // If not found in body, check thead (where it should be)
            if (!summaryRow) {
                const table = assignmentTableBody.closest('table');
                const thead = table ? table.querySelector('thead') : null;
                if (thead) {
                    summaryRow = thead.querySelector('.summary-row');
                }
            }

            if (summaryData) {
                const summaryHtml = `<td></td><td><strong>Summary for ${subjectName}</strong></td><td>-</td><td>${summaryData.total_hours.toFixed(1)}h (total)</td><td>-</td><td>${summaryData.average_grade.toFixed(1)}% (avg)</td><td>${summaryData.total_weight.toFixed(2)}% (graded)</td><td>-</td>`;

                if (summaryRow) {
                    summaryRow.innerHTML = summaryHtml;
                } else {
                    // Create in thead if possible
                    const table = assignmentTableBody.closest('table');
                    const thead = table ? table.querySelector('thead') : null;
                    if (thead) {
                        summaryRow = document.createElement('tr');
                        summaryRow.className = 'summary-row';
                        summaryRow.innerHTML = summaryHtml;
                        thead.appendChild(summaryRow);
                    }
                }
            } else if (summaryRow) {
                summaryRow.remove();
            }
        }

        function applyWeightPreview(assignmentRow, isEditing = false) {
            revertWeightPreview();
            const subject = assignmentRow.querySelector('select[name="subject"]').value;
            const category = assignmentRow.querySelector('select[name="category"]').value;
            if (!subject || !category) return;
            const categoryData = (weightCategoriesMap[subject] || []).find(c => c.name === category);
            if (!categoryData) return;

            // Get existing rows in this subject/category
            const existingRows = Array.from(assignmentTableBody.querySelectorAll('tr[data-id]')).filter(row => {
                // Skip the row being edited to avoid counting it twice
                if (isEditing && row === assignmentRow) return false;

                const cells = row.querySelectorAll('td');
                // Check if it's in view mode (not being edited)
                // cells[0] is checkbox, cells[1] is subject, cells[2] is category
                if (cells.length > 1 && cells[2].querySelector('.category-tag')) {
                    return cells[1].textContent.trim() === subject &&
                        cells[2].querySelector('.category-tag').lastChild.textContent.trim() === category;
                }
                // Check if it's in edit mode
                const subjectSelect = row.querySelector('select[name="subject"]');
                const categorySelect = row.querySelector('select[name="category"]');
                if (subjectSelect && categorySelect) {
                    return subjectSelect.value === subject && categorySelect.value === category;
                }
                return false;
            });

            const newTotalAssessments = existingRows.length + 1;
            const newCalculatedWeight = newTotalAssessments > 0 ? (categoryData.total_weight / newTotalAssessments) : 0;


            existingRows.forEach(row => {
                const weightCell = row.querySelectorAll('td')[6]; // Weight is now at index 6
                weightPreviewState.set(row, weightCell.innerHTML);
                weightCell.innerHTML = `<em>${newCalculatedWeight.toFixed(2)}%</em>`;
            });
        }

        function revertWeightPreview() {
            weightPreviewState.forEach((originalHtml, row) => {
                const weightCell = row.querySelectorAll('td')[6]; // Weight is now at index 6
                if (weightCell) weightCell.innerHTML = originalHtml;
            });
            weightPreviewState.clear();
        }

        function revertPredictorWeightPreview() {
            predictorWeightPreviewState.forEach((originalHtml, row) => {
                const weightCell = row.querySelectorAll('td')[6]; // Weight is now at index 6
                if (weightCell) weightCell.innerHTML = originalHtml;
            });
            predictorWeightPreviewState.clear();
        }

        // --- Stats view grade display toggle ---
        const statToggleButtons = document.querySelectorAll('[data-stats-toggle]');

        function percentToGpa(percent) {
            if (percent === null || percent === undefined || isNaN(percent)) return null;
            return Math.max(0, Math.min(4, (percent / 100) * 4));
        }

        function applyStatsMode(mode) {
            statToggleButtons.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.statsToggle === mode);
            });

            document.querySelectorAll('.stat-grade').forEach(el => {
                const percent = parseFloat(el.dataset.gradePercent);
                if (isNaN(percent)) return;
                if (mode === 'gpa') {
                    const gpa = percentToGpa(percent);
                    if (gpa !== null) el.textContent = `${gpa.toFixed(2)}`;
                } else {
                    el.textContent = `${percent.toFixed(1)}%`;
                }
            });

            document.querySelectorAll('.stat-grade-per-hour').forEach(el => {
                const percentPerHour = parseFloat(el.dataset.gradePerHour);
                if (isNaN(percentPerHour)) return;
                if (mode === 'gpa') {
                    const gpaPerHour = percentPerHour * 0.04; // convert %/h to GPA(4.0)/h
                    el.textContent = `${gpaPerHour.toFixed(2)}/h`;
                } else {
                    el.textContent = `${percentPerHour.toFixed(2)}%/h`;
                }
            });

            // Update copy labels that mention percent explicitly
            document.querySelectorAll('[data-toggle-percent-label]').forEach(el => {
                const percentLabel = el.dataset.togglePercentLabel;
                const gpaLabel = el.dataset.toggleGpaLabel || percentLabel;
                el.textContent = mode === 'gpa' ? gpaLabel : percentLabel;
            });

            localStorage.setItem('statsMode', mode);
        }

        if (statToggleButtons.length > 0) {
            const savedMode = localStorage.getItem('statsMode') || 'percent';
            applyStatsMode(savedMode);
            statToggleButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    const mode = btn.dataset.statsToggle;
                    applyStatsMode(mode);
                });
            });
        }

        // --- Threshold controls (High Scores / Needs Work) ---
        const gradedScores = JSON.parse(document.body.dataset.gradedScores || '[]');
        const highInput = document.getElementById('high-threshold');
        const lowInput = document.getElementById('low-threshold');
        const highPctDisplay = document.getElementById('high-score-pct-display');
        const highDesc = document.getElementById('high-score-desc');
        const needsPctDisplay = document.getElementById('needs-work-pct-display');
        const needsDesc = document.getElementById('needs-work-desc');
        const highHint = document.getElementById('high-threshold-hint');
        const lowHint = document.getElementById('low-threshold-hint');
        const highPill = document.getElementById('high-pill-text');
        const lowPill = document.getElementById('low-pill-text');

        function computeThresholdStats(highCut, lowCut) {
            const total = gradedScores.length;
            if (total === 0) {
                return { strongPct: null, strongCount: 0, needsPct: null, needsCount: 0, total };
            }
            const strongCount = gradedScores.filter(g => g >= highCut).length;
            const needsCount = gradedScores.filter(g => g < lowCut).length;
            return {
                strongPct: (strongCount / total) * 100,
                strongCount,
                needsPct: (needsCount / total) * 100,
                needsCount,
                total
            };
        }

        function renderThresholds(mode) {
            if (!highInput || !lowInput || !highPctDisplay || !needsPctDisplay) return;
            const highCut = parseFloat(highInput.value) || 90;
            const lowCut = parseFloat(lowInput.value) || 70;
            const stats = computeThresholdStats(highCut, lowCut);

            // Update hints with both % and GPA equivalents
            const highGpa = percentToGpa(highCut);
            const lowGpa = percentToGpa(lowCut);
            if (highHint) highHint.textContent = `(${highCut.toFixed(0)}% / ${highGpa.toFixed(2)} GPA)`;
            if (lowHint) lowHint.textContent = `(${lowCut.toFixed(0)}% / ${lowGpa.toFixed(2)} GPA)`;

            if (stats.strongPct === null) {
                highPctDisplay.textContent = 'N/A';
                highDesc.textContent = 'Add more graded items to see this metric.';
            } else {
                const thresholdLabel = mode === 'gpa'
                    ? `${percentToGpa(highCut).toFixed(2)} GPA`
                    : `${highCut.toFixed(0)}%`;
                highPctDisplay.textContent = `${stats.strongPct.toFixed(1)}%`;
                highDesc.textContent = `${stats.strongCount} of ${stats.total} graded items cleared the high-score bar (≥ ${thresholdLabel}).`;
                if (highPill) highPill.textContent = mode === 'gpa'
                    ? `${percentToGpa(highCut).toFixed(2)}+ GPA`
                    : `${highCut.toFixed(0)}%+ results`;
            }

            if (stats.needsPct === null) {
                needsPctDisplay.textContent = 'N/A';
                needsDesc.textContent = 'Add more graded items to see this metric.';
            } else {
                const thresholdLabel = mode === 'gpa'
                    ? `${percentToGpa(lowCut).toFixed(2)} GPA`
                    : `${lowCut.toFixed(0)}%`;
                needsPctDisplay.textContent = `${stats.needsPct.toFixed(1)}%`;
                needsDesc.textContent = `${stats.needsCount} of ${stats.total} graded items are under the target range (< ${thresholdLabel}).`;
                if (lowPill) lowPill.textContent = mode === 'gpa'
                    ? `< ${percentToGpa(lowCut).toFixed(2)} GPA`
                    : `Below ${lowCut.toFixed(0)}%`;
            }

            localStorage.setItem('statsThresholds', JSON.stringify({ highCut, lowCut }));
        }

        if (gradedScores.length && highInput && lowInput) {
            // Restore saved thresholds
            try {
                const saved = JSON.parse(localStorage.getItem('statsThresholds') || '{}');
                if (saved.highCut !== undefined) highInput.value = saved.highCut;
                if (saved.lowCut !== undefined) lowInput.value = saved.lowCut;
            } catch (e) { /* ignore */ }

            const currentMode = localStorage.getItem('statsMode') || 'percent';
            renderThresholds(currentMode);

            const handleThresholdChange = () => {
                const mode = localStorage.getItem('statsMode') || 'percent';
                renderThresholds(mode);
            };

            // Manual apply button to update thresholds
            const applyThresholdsBtn = document.getElementById('apply-thresholds');
            if (applyThresholdsBtn) {
                applyThresholdsBtn.addEventListener('click', handleThresholdChange);
            }

            // Re-render thresholds when switching GPA/percent mode
            if (statToggleButtons.length > 0) {
                statToggleButtons.forEach(btn => {
                    btn.addEventListener('click', () => {
                        const mode = btn.dataset.statsToggle;
                        renderThresholds(mode);
                    });
                });
            }
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
                // cells[0] is checkbox, cells[1] is subject, cells[2] is category
                return cells.length > 1 &&
                    cells[1].textContent.trim() === subject &&
                    cells[2].querySelector('.category-tag')?.lastChild.textContent.trim() === category;
            });

            const newTotalAssessments = existingRows.length + 1;
            const newCalculatedWeight = newTotalAssessments > 0 ? (categoryData.total_weight / newTotalAssessments) : 0;

            // Set the predictor weight field
            if (predictWeight) {
                predictWeight.value = newCalculatedWeight.toFixed(2);
            }

            // Apply preview to existing assignments
            existingRows.forEach(row => {
                const weightCell = row.querySelectorAll('td')[6]; // Weight is now at index 6
                predictorWeightPreviewState.set(row, weightCell.innerHTML);
                weightCell.innerHTML = `<em>${newCalculatedWeight.toFixed(2)}%</em>`;
            });
        }

        function renderAssignmentTable(assignments, summaryData, subject) {
            assignmentTableBody.innerHTML = '';

            // Update summary row in thead
            const table = assignmentTableBody.closest('table');
            const thead = table ? table.querySelector('thead') : null;
            if (thead) {
                // Remove existing summary row if any
                const existingSummary = thead.querySelector('.summary-row');
                if (existingSummary) {
                    existingSummary.remove();
                }

                // Add new summary row if we have summary data
                if (summaryData) {
                    const summaryRow = document.createElement('tr');
                    summaryRow.className = 'summary-row';
                    summaryRow.innerHTML = `
                    <td></td>
                    <td><strong>Summary for ${subject}</strong></td>
                    <td>-</td>
                    <td>${summaryData.total_hours.toFixed(1)}h (total)</td>
                    <td>-</td>
                    <td>${summaryData.average_grade.toFixed(1)}% (avg)</td>
                    <td>${summaryData.total_weight.toFixed(2)}% (graded)</td>
                    <td>-</td>
                `;
                    thead.appendChild(summaryRow);
                }
            }

            assignments.forEach(log => {
                const row = document.createElement('tr');
                row.dataset.id = log.id;
                row.classList.add('assignment-row');

                // Add prediction class if this is a prediction
                if (log.is_prediction) {
                    row.classList.add('prediction-row');
                    row.dataset.isPrediction = 'true';
                }

                // Build the row HTML based on whether it's a prediction
                if (log.is_prediction) {
                    row.innerHTML = `<td><span class="drag-handle" title="Drag" aria-label="Drag to reorder" draggable="true">⋮⋮</span><input type="checkbox" class="select-assignment" data-id="${log.id}"></td><td>${log.subject}</td><td><span class="category-tag"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg> ${log.category}</span></td><td><input type="number" class="prediction-input hours-input" data-id="${log.id}" value="${log.study_time || 0}" step="0.1" style="width: 80px;"> hours</td><td>${log.assignment_name}</td><td><input type="number" class="prediction-input grade-input" data-id="${log.id}" value="${log.grade || ''}" step="1" style="width: 80px;">%</td><td>${parseFloat(log.weight).toFixed(2)}%</td><td><button class="action-btn predict-btn">Predict</button><button class="action-btn add-prediction-btn">Add</button><button class="action-btn delete-btn">Delete</button></td>`;
                } else {
                    row.innerHTML = `<td><span class="drag-handle" title="Drag" aria-label="Drag to reorder" draggable="true">⋮⋮</span><input type="checkbox" class="select-assignment" data-id="${log.id}"></td><td>${log.subject}</td><td><span class="category-tag"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg> ${log.category}</span></td><td>${parseFloat(log.study_time).toFixed(1)} hours</td><td>${log.assignment_name}</td><td>${log.grade !== null ? log.grade + '%' : '-'}</td><td>${parseFloat(log.weight).toFixed(2)}%</td><td><button class="action-btn edit-btn">Edit</button><button class="action-btn delete-btn">Delete</button></td>`;
                }

                assignmentTableBody.appendChild(row);
            });

            // Update summary row based on current state (including predictions toggle)
            recalculateSummaryFromDOM();
            if (typeof ensureDragHandles === 'function') {
                ensureDragHandles();
                setTimeout(ensureDragHandles, 0); // catch async paints
            }
        }

        function updateCategoryTableRow(subject, categoryName) {
            if (!categoryTableBody) return;
            const categoryRow = Array.from(categoryTableBody.querySelectorAll('tr')).find(r => r.dataset.name === categoryName);
            if (!categoryRow) return;
            const categoryData = (weightCategoriesMap[subject] || []).find(c => c.name === categoryName);
            if (!categoryData) return;
            const numAssessments = Array.from(assignmentTableBody.querySelectorAll('tr[data-id]')).filter(r => {
                const cells = r.querySelectorAll('td');
                // cells[0] is checkbox, cells[1] is subject, cells[2] is category
                return cells.length > 1 && cells[1].textContent.trim() === subject && cells[2].querySelector('.category-tag')?.lastChild.textContent.trim() === categoryName;
            }).length;
            categoryRow.querySelector('.num-assessments').textContent = numAssessments;
            const newCalculatedWeight = numAssessments > 0 ? `${(categoryData.total_weight / numAssessments).toFixed(2)}%` : 'N/A';
            categoryRow.querySelector('.calculated-weight').textContent = newCalculatedWeight;
        }

        function updateTotalWeightIndicator() {
            const totalWeightIndicator = document.getElementById('total-weight-indicator');
            const totalWeightValue = document.getElementById('total-weight-value');

            if (!totalWeightIndicator || !totalWeightValue || !categoryTableBody) return;

            // Calculate total weight from all category rows
            let totalWeight = 0;
            const categoryRows = categoryTableBody.querySelectorAll('tr[data-id]');

            categoryRows.forEach(row => {
                const weightCell = row.querySelectorAll('td')[1];
                if (weightCell) {
                    const weightText = weightCell.textContent.trim();
                    // Handle both "50%" format and input fields
                    const inputField = weightCell.querySelector('input[name="total_weight"]');
                    if (inputField) {
                        totalWeight += parseFloat(inputField.value) || 0;
                    } else {
                        totalWeight += parseFloat(weightText) || 0;
                    }
                }
            });

            // Update the display
            totalWeightValue.textContent = totalWeight.toFixed(1);

            // Color code based on total
            const isDarkMode = document.body.classList.contains('dark-mode');

            if (totalWeight === 100) {
                if (isDarkMode) {
                    totalWeightIndicator.style.backgroundColor = '#1a4d3a';
                    totalWeightIndicator.style.color = '#61dc9b';
                    totalWeightIndicator.style.border = '1px solid #25A762';
                } else {
                    totalWeightIndicator.style.backgroundColor = '#d4f5e6';
                    totalWeightIndicator.style.color = '#25A762';
                    totalWeightIndicator.style.border = '1px solid #61dc9b';
                }
            } else if (totalWeight < 100) {
                if (isDarkMode) {
                    totalWeightIndicator.style.backgroundColor = '#003547';
                    totalWeightIndicator.style.color = '#93dbff';
                    totalWeightIndicator.style.border = '1px solid #0081a7';
                } else {
                    totalWeightIndicator.style.backgroundColor = '#e3f5ff';
                    totalWeightIndicator.style.color = '#0081a7';
                    totalWeightIndicator.style.border = '1px solid #93dbff';
                }
            } else {
                if (isDarkMode) {
                    totalWeightIndicator.style.backgroundColor = '#3d0000';
                    totalWeightIndicator.style.color = '#ff5959';
                    totalWeightIndicator.style.border = '1px solid #7A0000';
                } else {
                    totalWeightIndicator.style.backgroundColor = '#ffe6e6';
                    totalWeightIndicator.style.color = '#7A0000';
                    totalWeightIndicator.style.border = '1px solid #ff5959';
                }
            }
        }

        async function handleAssignmentSave(row, suppressToast = false, forceAssignment = false) {
            // --- FIX: Do not revert the preview if validation fails ---
            if (!validateRow(row)) return;
            revertWeightPreview(); // Only revert on successful validation

            const logId = row.dataset.id;
            const isNew = !logId;
            const url = isNew ? '/add' : `/update/${logId}`;
            const formData = new FormData();

            // Gather data from inputs
            row.querySelectorAll('input, select').forEach(el => {
                if (el.name) formData.append(el.name, el.value);
            });

            // For prediction rows (and potentially others), subject and category might be text, not inputs
            // We need to ensure they are present in formData
            if (!formData.has('subject')) {
                const subjectCell = row.querySelector('td:nth-child(2)');
                if (subjectCell) formData.append('subject', subjectCell.textContent.trim());
            }
            if (!formData.has('category')) {
                const categoryCell = row.querySelector('td:nth-child(3)');
                if (categoryCell) {
                    // Category cell might contain an icon/span, get text content carefully
                    // The span has class "category-tag"
                    const categorySpan = categoryCell.querySelector('.category-tag');
                    if (categorySpan) {
                        formData.append('category', categorySpan.textContent.trim());
                    } else {
                        formData.append('category', categoryCell.textContent.trim());
                    }
                }
            }

            // Ensure assignment_name is present (it's text in prediction rows)
            if (!formData.has('assignment_name')) {
                const nameCell = row.querySelector('td:nth-child(5)');
                if (nameCell) formData.append('assignment_name', nameCell.textContent.trim());
            }

            // Ensure study_time and grade are present if they are inputs (they should be caught by querySelectorAll above)
            // But we need to map class names to form names if they don't have name attributes
            // In renderAssignmentTable:
            // <input type="number" class="prediction-input hours-input" ... > -> needs name="study_time"
            // <input type="number" class="prediction-input grade-input" ... > -> needs name="grade"

            // Let's fix the inputs in renderAssignmentTable to have name attributes, 
            // OR handle it here. Adding name attributes in renderAssignmentTable is cleaner but requires re-rendering.
            // Let's handle it here for robustness.

            const hoursInput = row.querySelector('.hours-input');
            if (hoursInput && !formData.has('study_time')) {
                formData.append('study_time', hoursInput.value);
            }

            const gradeInput = row.querySelector('.grade-input');
            if (gradeInput && !formData.has('grade')) {
                formData.append('grade', gradeInput.value);
            }

            const currentSubjectFilter = subjectFilterDropdown.value;
            formData.append('current_filter', currentSubjectFilter);

            // Determine is_prediction status
            // If forceAssignment is true, we are converting to assignment, so is_prediction = false
            // Otherwise, use the row's dataset
            let isPrediction = row.dataset.isPrediction === 'true';
            if (forceAssignment) {
                isPrediction = false;
            }
            formData.append('is_prediction', isPrediction ? 'true' : 'false');
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
                if (!suppressToast) {
                    showToast(result.message, 'success');
                }
                renderAssignmentTable(result.updated_assignments, result.summary, currentSubjectFilter);
                if (typeof ensureDragHandles === 'function') ensureDragHandles();
                if (isNew) {
                    updateCategoryTableRow(result.log.subject, result.log.category);
                }
                // --- NEW: Update subject prediction (remaining weight) ---
                updateSubjectPrediction(null);
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
            confirmYesBtn.addEventListener('click', async function () {
                if (itemToDelete.row) {
                    // Clear any validation alerts when deleting
                    showValidationAlert([]);

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
                        // Update weight indicator if deleting a category row
                        if (type === 'category') {
                            updateTotalWeightIndicator();
                        }
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
                                if (typeof ensureDragHandles === 'function') ensureDragHandles();

                                // Extract category name - handle both edit mode and view mode
                                let categoryName;
                                // cells[0] is checkbox, cells[1] is subject, cells[2] is category
                                const categoryCell = row.querySelectorAll('td')[2];

                                // Check if row is in edit mode (has select dropdown)
                                const categorySelect = categoryCell.querySelector('select[name="category"]');
                                if (categorySelect) {
                                    categoryName = categorySelect.value;
                                } else {
                                    // Row is in view mode (has category-tag span)
                                    const categoryTag = categoryCell.querySelector('.category-tag');
                                    if (categoryTag) {
                                        categoryName = categoryTag.lastChild.textContent.trim();
                                    }
                                }

                                if (categoryName) {
                                    updateCategoryTableRow(currentFilter, categoryName);
                                }
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
            gradeLockBtn.addEventListener('click', function () {
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
            addCategoryBtn.addEventListener('click', function () {
                const newRow = document.createElement('tr');
                newRow.innerHTML = `<td><input type="text" name="name" required></td><td><input type="number" name="total_weight" min="0" max="100" required></td><td class="num-assessments">0</td><td class="calculated-weight">N/A</td><td><input type="text" name="default_name" placeholder="e.g., Quiz #"></td><td><button class="action-btn save-btn">Save</button><button class="action-btn delete-btn">Delete</button></td>`;
                categoryTableBody.appendChild(newRow);
                updateTotalWeightIndicator();
            });
        }

        if (categoryTableBody) {
            categoryTableBody.addEventListener('click', async function (event) {
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
            categoryTableBody.addEventListener('keydown', async function (event) {
                if (event.key === 'Enter' && event.target.matches('input')) {
                    event.preventDefault();
                    const row = event.target.closest('tr');
                    if (row) {
                        await handleCategorySave(row);
                    }
                }
            });
        }

        function addNewRow(isPrediction = false) {
            revertWeightPreview();
            revertPredictorWeightPreview();

            const newRow = document.createElement('tr');
            newRow.classList.add('assignment-row');               // <-- DnD relies on this
            if (isPrediction) {
                newRow.classList.add('prediction-row');
                newRow.dataset.isPrediction = 'true';
            }

            const gradeAttrs = isGradeLockOn ? 'min="0" max="100"' : 'min="0"';

            const currentSubjectFilter = subjectFilterDropdown ? subjectFilterDropdown.value : 'all';
            const isSubjectFiltered = currentSubjectFilter && currentSubjectFilter !== 'all';

            const allSubjects = Object.keys(weightCategoriesMap);

            // subject <select>
            const subjectSelect = document.createElement('select');
            subjectSelect.name = 'subject';
            subjectSelect.required = true;
            subjectSelect.setAttribute('autocomplete', 'off');

            if (isSubjectFiltered) {
                const option = document.createElement('option');
                option.value = currentSubjectFilter;
                option.textContent = currentSubjectFilter;
                option.selected = true;
                subjectSelect.appendChild(option);
                subjectSelect.disabled = true;
                subjectSelect.style.backgroundColor = '#eee';
            } else {
                const defaultOpt = document.createElement('option');
                defaultOpt.value = '';
                defaultOpt.disabled = true;
                defaultOpt.selected = true;
                defaultOpt.textContent = '-- Select Subject --';
                subjectSelect.appendChild(defaultOpt);

                allSubjects.forEach(subject => {
                    const option = document.createElement('option');
                    option.value = subject;
                    option.textContent = subject;
                    subjectSelect.appendChild(option);
                });
            }

            const subjectTd = document.createElement('td');
            subjectTd.appendChild(subjectSelect);

            // category <select>
            const categorySelect = document.createElement('select');
            categorySelect.name = 'category';
            categorySelect.required = true;
            categorySelect.innerHTML = '<option value="" disabled selected>-- Select Category --</option>';

            if (isSubjectFiltered) {
                const categories = (weightCategoriesMap[currentSubjectFilter] || []).map(c => c.name);
                categories.forEach(cat => {
                    const option = document.createElement('option');
                    option.value = cat;
                    option.textContent = cat;
                    categorySelect.appendChild(option);
                });
            }

            subjectSelect.addEventListener('change', function () {
                const selectedSubject = this.value;
                categorySelect.innerHTML = '<option value="" disabled selected>-- Select Category --</option>';
                if (selectedSubject && weightCategoriesMap[selectedSubject]) {
                    weightCategoriesMap[selectedSubject].forEach(catObj => {
                        const option = document.createElement('option');
                        option.value = catObj.name;
                        option.textContent = catObj.name;
                        categorySelect.appendChild(option);
                    });
                }
            });

            categorySelect.addEventListener('change', function () {
                const selectedSubject = subjectSelect.value;
                const selectedCategory = this.value;
                const assignmentInput = newRow.querySelector('input[name="assignment_name"]');

                if (selectedSubject && selectedCategory) {
                    const categories = weightCategoriesMap[selectedSubject] || [];
                    const categoryDef = categories.find(c => c.name === selectedCategory);

                    if (categoryDef) {
                        let count = 1;
                        const existingRows = assignmentTableBody.querySelectorAll('tr[data-id]');
                        existingRows.forEach(row => {
                            const subjCell = row.querySelector('td:nth-child(2)');
                            const catCell = row.querySelector('td:nth-child(3)');
                            if (subjCell && catCell &&
                                subjCell.textContent.trim() === selectedSubject &&
                                catCell.textContent.trim().includes(selectedCategory)) {
                                count++;
                            }
                        });

                        if (assignmentInput && categoryDef.default_name) {
                            if (categoryDef.default_name.includes('#')) {
                                assignmentInput.value = categoryDef.default_name.replace('#', count);
                            } else {
                                assignmentInput.value = categoryDef.default_name + ' ' + count;
                            }
                        }

                        const newTotalAssessments = count;
                        const calculatedWeight = newTotalAssessments > 0
                            ? (categoryDef.total_weight / newTotalAssessments).toFixed(2)
                            : '0.00';

                        const weightCell = newRow.querySelector('td:nth-child(7)');
                        if (weightCell) weightCell.textContent = calculatedWeight + '%';
                    }
                }
            });

            const categoryTd = document.createElement('td');
            categoryTd.appendChild(categorySelect);

            // ✅ FIRST CELL: drag handle + checkbox (always)
            const firstTd = document.createElement('td');
            firstTd.innerHTML = `
    <span class="drag-handle" title="Drag" aria-label="Drag to reorder" draggable="true">⋮⋮</span>
    <input type="checkbox" class="select-assignment">
  `;

            // Assemble the row
            newRow.appendChild(firstTd);
            newRow.appendChild(subjectTd);
            newRow.appendChild(categoryTd);

            // rest of inputs
            if (isPrediction) {
                newRow.innerHTML += `
      <td><input type="number" name="study_time" class="prediction-input hours-input" step="0.1" min="0" placeholder="Hours" style="width: 70px;"> hours</td>
      <td><input type="text" name="assignment_name" placeholder="Assignment Name" style="width: 150px;"></td>
      <td><input type="number" name="grade" class="prediction-input grade-input" step="1" ${gradeAttrs} placeholder="Grade" style="width: 60px;">%</td>
      <td>0.00%</td>
      <td><button class="action-btn delete-btn">Delete</button></td>
    `;
            } else {
                newRow.innerHTML += `
      <td><input type="number" name="study_time" step="0.1" min="0" required style="width: 70px;"> hours</td>
      <td><input type="text" name="assignment_name" required style="width: 150px;"></td>
      <td><input type="number" name="grade" step="1" ${gradeAttrs} style="width: 60px;">%</td>
      <td>0.00%</td>
      <td><button class="action-btn save-btn">Save</button><button class="action-btn delete-btn">Delete</button></td>
    `;
            }

            // re-attach selects (innerHTML above wipes them)
            const cells = newRow.querySelectorAll('td');
            cells[1].innerHTML = '';
            cells[1].appendChild(subjectSelect);
            cells[2].innerHTML = '';
            cells[2].appendChild(categorySelect);

            assignmentTableBody.appendChild(newRow);

            if (isSubjectFiltered) {
                subjectSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }

            // make sure the handle & class stay present
            if (typeof ensureDragHandles === 'function') ensureDragHandles();
        }


        if (addRowBtn) {
            addRowBtn.addEventListener('click', () => addNewRow(false));
        }

        const addPredictionBtn = document.getElementById('addPredictionBtn');
        if (addPredictionBtn) {
            addPredictionBtn.addEventListener('click', async () => {
                // Check if subject filter is set
                const currentSubjectFilter = subjectFilterDropdown ? subjectFilterDropdown.value : 'all';
                const isSubjectFiltered = currentSubjectFilter && currentSubjectFilter !== 'all';

                if (!isSubjectFiltered) {
                    showToast('Please select a specific subject to add a prediction', 'error');
                    return;
                }

                // Get category data for the filtered subject
                const categories = weightCategoriesMap[currentSubjectFilter] || [];
                if (categories.length === 0) {
                    showToast('Please add at least one category definition before adding predictions', 'error');
                    return;
                }

                // Auto-save a new prediction with default values
                try {
                    const formData = new FormData();
                    formData.append('subject', currentSubjectFilter);
                    formData.append('category', categories[0].name); // Use first category as default
                    formData.append('study_time', 0);
                    formData.append('assignment_name', 'Prediction');
                    formData.append('grade', '');
                    formData.append('weight', 0);
                    formData.append('is_prediction', 'true');
                    formData.append('current_filter', currentSubjectFilter);

                    const response = await fetch('/add', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (response.ok) {
                        showToast(result.message, 'success');
                        renderAssignmentTable(result.updated_assignments, result.summary, currentSubjectFilter);
                        if (typeof ensureDragHandles === 'function') ensureDragHandles();
                    } else {
                        showToast(result.message, 'error');
                    }
                } catch (error) {
                    console.error('Failed to add prediction:', error);
                    showToast('Network error occurred', 'error');
                }
            });
        }

        if (assignmentTableBody) {
            assignmentTableBody.addEventListener('click', async function (event) {
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
                    // Adjust indices: cells[0] is checkbox, cells[1] is subject, cells[2] is category, etc.
                    const subjectText = cells[1].textContent.trim();
                    const categoryText = cells[2].querySelector('.category-tag').lastChild.textContent.trim();
                    const gradeText = cells[5].textContent.trim();
                    const gradeValue = gradeText === '-' ? '' : parseInt(gradeText, 10);
                    const gradeAttributes = isGradeLockOn ? 'min="0" max="100"' : 'min="0"';

                    const currentSubjectFilter = subjectFilterDropdown ? subjectFilterDropdown.value : 'all';
                    const isSubjectFiltered = currentSubjectFilter && currentSubjectFilter !== 'all';

                    // Get all subjects from weightCategoriesMap
                    const allSubjects = Object.keys(weightCategoriesMap);

                    // Create subject select dropdown
                    const subjectSelect = document.createElement('select');
                    subjectSelect.name = 'subject';
                    subjectSelect.required = true;

                    if (isSubjectFiltered) {
                        // If filtering by subject, lock it to that subject
                        const option = document.createElement('option');
                        option.value = subjectText;
                        option.textContent = subjectText;
                        option.selected = true;
                        subjectSelect.appendChild(option);
                        subjectSelect.disabled = true;
                        subjectSelect.style.backgroundColor = '#eee';
                    } else {
                        // If viewing all subjects, allow editing
                        allSubjects.forEach(subject => {
                            const option = document.createElement('option');
                            option.value = subject;
                            option.textContent = subject;
                            if (subject === subjectText) {
                                option.selected = true;
                            }
                            subjectSelect.appendChild(option);
                        });
                    }

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
                    // Keep checkbox cell empty (cells[0])
                    cells[1].innerHTML = '';
                    cells[1].appendChild(subjectSelect);
                    cells[2].innerHTML = '';
                    cells[2].appendChild(categorySelect);
                    cells[3].innerHTML = `<input type="number" name="study_time" value="${(parseFloat(cells[3].textContent) || 0).toFixed(1)}" step="0.1" min="0" required>`;
                    cells[4].innerHTML = `<input type="text" name="assignment_name" value="${cells[4].textContent.trim()}" required>`;
                    cells[5].innerHTML = `<input type="number" name="grade" value="${gradeValue}" ${gradeAttributes} placeholder="Optional">`;
                    cells[6].innerHTML = `<input type="number" name="weight" value="${parseFloat(cells[6].textContent) || 0}" required readonly style="background-color: #eee;">`;
                } else if (button.classList.contains('save-btn')) {
                    await handleAssignmentSave(row);
                } else if (button.classList.contains('delete-btn')) {
                    showConfirmation("Are you sure you want to delete this assignment?", row, 'assignment');
                } else if (button.classList.contains('add-prediction-btn')) {
                    // Convert prediction to assignment
                    // suppressToast=false, forceAssignment=true
                    await handleAssignmentSave(row, false, true);
                } else if (button.classList.contains('predict-btn')) {
                    // Handle individual assignment prediction
                    const hoursInput = row.querySelector('.hours-input');
                    const gradeInput = row.querySelector('.grade-input');
                    const weightCell = row.querySelectorAll('td')[6]; // Weight is at index 6

                    const hours = hoursInput ? hoursInput.value : '';
                    const grade = gradeInput ? gradeInput.value : '';
                    const weight = weightCell ? parseFloat(weightCell.textContent) : 0;

                    // Validate: need either hours OR grade (target), but not both populated for prediction?
                    // Actually, usually we have one and want to predict the other.

                    if (hours && grade) {
                        showToast('Please clear one field to predict it based on the other.', 'error');
                        return;
                    }
                    if (!hours && !grade) {
                        showToast('Please enter either Hours or Target Grade.', 'error');
                        return;
                    }

                    if ((hours && parseFloat(hours) < 0) || (grade && parseFloat(grade) < 0)) {
                        showToast('Values cannot be negative.', 'error');
                        return;
                    }

                    const subject = row.querySelector('td:nth-child(2)').textContent.trim();
                    const categoryTag = row.querySelector('td:nth-child(3) .category-tag');
                    const category = categoryTag ? categoryTag.lastChild.textContent.trim() : row.querySelector('td:nth-child(3)').textContent.trim();

                    const formData = new FormData();
                    formData.append('subject', subject);
                    // formData.append('category', category); // Not strictly needed for k-estimation but good for context if needed
                    formData.append('weight', weight);
                    formData.append('grade_lock', isGradeLockOn ? 'true' : 'false');

                    if (hours) formData.append('hours', hours);
                    if (grade) formData.append('target_grade', grade);

                    try {
                        const response = await fetch('/predict', {
                            method: 'POST',
                            body: formData
                        });
                        const data = await response.json();

                        if (response.ok) {
                            if (data.mode === 'grade_from_hours') {
                                if (gradeInput) {
                                    gradeInput.value = data.predicted_grade;
                                    gradeInput.classList.add('predicted-value'); // Add some styling class if desired
                                }
                            } else if (data.mode === 'hours_from_grade') {
                                if (hoursInput) {
                                    hoursInput.value = data.required_hours;
                                    hoursInput.classList.add('predicted-value');
                                }
                            }
                            showToast('Prediction calculated!', 'success');

                            // Save the prediction to the database immediately
                            // suppressToast=true, forceAssignment=false (keep as prediction)
                            await handleAssignmentSave(row, true, false);

                        } else {
                            showToast(data.message || 'Prediction failed', 'error');
                        }
                    } catch (e) {
                        console.error(e);
                        showToast('Error connecting to server', 'error');
                    }
                }
            });

            // Enter key support for individual prediction inputs
            assignmentTableBody.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && e.target.classList.contains('prediction-input')) {
                    e.preventDefault();
                    const row = e.target.closest('tr');
                    const predictBtn = row.querySelector('.predict-btn');
                    if (predictBtn) predictBtn.click();
                }
            });
            assignmentTableBody.addEventListener('change', function (event) {
                if (event.target.name === 'subject') {
                    const subjectValue = event.target.value;
                    const row = event.target.closest('tr');

                    // Revert weight preview first
                    revertWeightPreview();

                    // Clear all fields except subject
                    const categorySelect = row.querySelector('select[name="category"]');
                    if (!categorySelect) return;

                    const studyTimeInput = row.querySelector('input[name="study_time"]');
                    const assignmentNameInput = row.querySelector('input[name="assignment_name"]');
                    const gradeInput = row.querySelector('input[name="grade"]');
                    const weightInput = row.querySelector('input[name="weight"]');

                    if (studyTimeInput) studyTimeInput.value = '';
                    if (assignmentNameInput) assignmentNameInput.value = '';
                    if (gradeInput) gradeInput.value = '';
                    if (weightInput) weightInput.value = '';

                    // Clear and repopulate category dropdown
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
            assignmentTableBody.addEventListener('change', function (event) {
                const target = event.target;
                if (target.name === 'category') {
                    const row = target.closest('tr');

                    // Revert any existing weight preview first
                    revertWeightPreview();

                    // Clear all fields except subject and category
                    const studyTimeInput = row.querySelector('input[name="study_time"]');
                    const assignmentNameInput = row.querySelector('input[name="assignment_name"]');
                    const gradeInput = row.querySelector('input[name="grade"]');
                    const weightInput = row.querySelector('input[name="weight"]');

                    if (studyTimeInput) studyTimeInput.value = '';
                    if (assignmentNameInput) assignmentNameInput.value = '';
                    if (gradeInput) gradeInput.value = '';
                    if (weightInput) weightInput.value = '';

                    // Fill in defaults if category is selected
                    const subject = row.querySelector('select[name="subject"]').value;
                    const categoryName = target.value;

                    if (subject && categoryName) {
                        const categoryData = (weightCategoriesMap[subject] || []).find(c => c.name === categoryName);
                        if (categoryData) {
                            // Fill in weight
                            if (weightInput) {
                                if (categoryData.num_assessments > 0) {
                                    weightInput.value = (categoryData.total_weight / categoryData.num_assessments).toFixed(2);
                                }
                            }

                            // Fill in default assignment name if available
                            if (assignmentNameInput && categoryData.default_name) {
                                if (categoryData.default_name.includes('#')) {
                                    // cells[0] is checkbox, cells[1] is subject, cells[2] is category
                                    const existingCount = Array.from(document.querySelectorAll('#study-table-body tr[data-id]')).filter(r => r.querySelectorAll('td')[2].textContent.trim().includes(categoryName)).length;
                                    assignmentNameInput.value = categoryData.default_name.replace('#', existingCount + 1);
                                } else {
                                    assignmentNameInput.value = categoryData.default_name;
                                }
                            }

                            // Apply weight preview for both new and edited assignments
                            const isEditing = !!row.dataset.id;
                            applyWeightPreview(row, isEditing);
                        }
                    }
                }
            });
            assignmentTableBody.addEventListener('keydown', async function (event) {
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

        // --- Prediction Feature Event Listeners ---
        if (assignmentTableBody) {
            // Handle Enter key in prediction rows to convert to assignment
            assignmentTableBody.addEventListener('keydown', function (event) {
                if (event.key !== 'Enter') return;

                const target = event.target;
                if (!target.classList.contains('prediction-input')) return;

                const row = target.closest('tr');
                if (!row || !row.classList.contains('prediction-row')) return;

                event.preventDefault();

                // Trigger click on the "Predict" button instead of "Add"
                const predictButton = row.querySelector('.predict-btn');
                if (predictButton) {
                    predictButton.click();
                }
            });

            // Auto-clear predicted values when user manually edits input fields
            assignmentTableBody.addEventListener('input', function (event) {
                const target = event.target;
                if (!target.classList.contains('prediction-input')) return;

                const row = target.closest('tr');
                if (!row || !row.classList.contains('prediction-row')) return;

                const hoursInput = row.querySelector('.hours-input');
                const gradeInput = row.querySelector('.grade-input');

                // If user edits hours field, clear predicted grade
                if (target.classList.contains('hours-input')) {
                    if (gradeInput && gradeInput.classList.contains('predicted-value')) {
                        gradeInput.value = '';
                        gradeInput.classList.remove('predicted-value');
                    }
                }
                // If user edits grade field, clear predicted hours
                else if (target.classList.contains('grade-input')) {
                    if (hoursInput && hoursInput.classList.contains('predicted-value')) {
                        hoursInput.value = '';
                        hoursInput.classList.remove('predicted-value');
                    }
                }
            });


            // Handle "Add" button click to convert prediction to assignment
            assignmentTableBody.addEventListener('click', async function (event) {
                const button = event.target;
                if (!button.classList.contains('add-prediction-btn')) return;

                const row = button.closest('tr');
                if (!row) return;

                const hoursInput = row.querySelector('.hours-input');
                const gradeInput = row.querySelector('.grade-input');
                const assignmentNameCell = row.querySelector('td:nth-child(5)');

                if (!hoursInput || parseFloat(hoursInput.value) <= 0) {
                    showToast('Please enter study time before converting to assignment', 'error');
                    return;
                }

                const assignmentId = row.dataset.id;
                if (!assignmentId) {
                    showToast('Please save the prediction first', 'error');
                    return;
                }

                try {
                    // First, update the prediction with current values
                    const subjectCell = row.querySelector('td:nth-child(2)');
                    const categoryCell = row.querySelector('td:nth-child(3)');
                    const weightCell = row.querySelector('td:nth-child(7)');

                    const subject = subjectCell.textContent.trim();
                    const categoryText = categoryCell.textContent.trim();
                    const categoryMatch = categoryText.match(/\s*(.+)$/);
                    const category = categoryMatch ? categoryMatch[1].trim() : categoryText;
                    const assignmentName = assignmentNameCell.textContent.trim() || 'Prediction';
                    const weight = parseFloat(weightCell.textContent) || 0;

                    const updateFormData = new FormData();
                    updateFormData.append('subject', subject);
                    updateFormData.append('category', category);
                    updateFormData.append('study_time', hoursInput.value);
                    updateFormData.append('assignment_name', assignmentName);
                    updateFormData.append('grade', gradeInput.value || '');
                    updateFormData.append('weight', weight);
                    updateFormData.append('is_prediction', 'true');
                    updateFormData.append('current_filter', subjectFilterDropdown ? subjectFilterDropdown.value : 'all');

                    const updateResponse = await fetch(`/update/${assignmentId}`, {
                        method: 'POST',
                        body: updateFormData
                    });

                    if (!updateResponse.ok) {
                        const errorResult = await updateResponse.json();
                        showToast(errorResult.message || 'Failed to update prediction values', 'error');
                        return;
                    }

                    // Now convert the prediction to an assignment
                    const formData = new FormData();
                    formData.append('assignment_id', assignmentId);
                    formData.append('current_filter', subjectFilterDropdown ? subjectFilterDropdown.value : 'all');

                    const response = await fetch('/convert_prediction', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (response.ok) {
                        showToast('Prediction converted to assignment!', 'success');
                        renderAssignmentTable(result.updated_assignments, result.summary, subjectFilterDropdown ? subjectFilterDropdown.value : 'all');
                        if (typeof ensureDragHandles === 'function') ensureDragHandles();
                    } else {
                        showToast(result.message || 'Failed to convert prediction', 'error');
                    }
                } catch (error) {
                    console.error('Conversion failed:', error);
                    showToast('Network error occurred', 'error');
                }
            });
        }

        // Pie Chart Removed

        // Get the predictor form elements
        const predictSubject = document.getElementById('predict-subject');
        const predictCategory = document.getElementById('predict-category');

        // Function to clear predictor fields
        function clearPredictorFields(keepSubject = false) {
            if (!keepSubject) {
                predictCategory.innerHTML = '<option value="">-- Select Category --</option>';
            }
            document.getElementById('weight').value = '';

            const hoursInput = document.getElementById('hours');
            hoursInput.value = '';
            hoursInput.style.color = '';
            hoursInput.style.fontWeight = '';

            const targetGradeInput = document.getElementById('target_grade');
            targetGradeInput.value = '';
            targetGradeInput.style.color = '';
            targetGradeInput.style.fontWeight = '';

            const resultDiv = document.getElementById('prediction-result');
            resultDiv.textContent = '';
            resultDiv.style.color = '';
            resultDiv.style.backgroundColor = '';
            resultDiv.style.border = '';
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
            predictCategory.addEventListener('change', function () {
                const subject = predictSubject.value;
                const category = predictCategory.value;

                // Clear fields except subject and category when category changes
                const hoursInput = document.getElementById('hours');
                hoursInput.value = '';
                hoursInput.style.color = '';
                hoursInput.style.fontWeight = '';

                const targetGradeInput = document.getElementById('target_grade');
                targetGradeInput.value = '';
                targetGradeInput.style.color = '';
                targetGradeInput.style.fontWeight = '';

                const resultDiv = document.getElementById('prediction-result');
                resultDiv.textContent = '';
                resultDiv.style.color = '';
                resultDiv.style.backgroundColor = '';
                resultDiv.style.border = '';

                // Apply weight preview
                applyPredictorWeightPreview(subject, category);
            });

            // Add Enter key handler for predictor inputs
            const predictorInputs = [
                document.getElementById('hours'),
                document.getElementById('target_grade')
            ];

            predictorInputs.forEach(input => {
                if (input) {
                    input.addEventListener('keydown', function (e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            const predictBtn = document.getElementById('predict-btn');
                            if (predictBtn) {
                                predictBtn.click();
                            }
                        }
                    });
                }
            });

            // Clear predicted value when user edits target grade
            const targetGradeInput = document.getElementById('target_grade');
            if (targetGradeInput) {
                targetGradeInput.addEventListener('input', function () {
                    // Remove green styling from target grade (user is switching to predict hours mode)
                    this.style.color = '';
                    this.style.fontWeight = '';

                    // Completely clear hours value and styling (if it was predicted)
                    const hoursInput = document.getElementById('hours');
                    if (hoursInput) {
                        hoursInput.value = '';
                        hoursInput.style.color = '';
                        hoursInput.style.fontWeight = '';
                    }

                    // Clear prediction result
                    const resultDiv = document.getElementById('prediction-result');
                    if (resultDiv) {
                        resultDiv.textContent = '';
                        resultDiv.style.color = '';
                        resultDiv.style.backgroundColor = '';
                        resultDiv.style.border = '';
                    }
                });
            }

            // Clear predicted value when user edits hours
            const hoursInput = document.getElementById('hours');
            if (hoursInput) {
                hoursInput.addEventListener('input', function () {
                    // Remove blue styling from hours (user is switching to predict grade mode)
                    this.style.color = '';
                    this.style.fontWeight = '';

                    // Completely clear target grade value and styling (if it was predicted)
                    const targetGradeInput = document.getElementById('target_grade');
                    if (targetGradeInput) {
                        targetGradeInput.value = '';
                        targetGradeInput.style.color = '';
                        targetGradeInput.style.fontWeight = '';
                    }

                    // Clear prediction result
                    const resultDiv = document.getElementById('prediction-result');
                    if (resultDiv) {
                        resultDiv.textContent = '';
                        resultDiv.style.color = '';
                        resultDiv.style.backgroundColor = '';
                        resultDiv.style.border = '';
                    }
                });
            }
        }

        // Handle the predictor button click
        if (predictBtn) {
            predictBtn.addEventListener('click', async () => {
                const resultDiv = document.getElementById('prediction-result');

                // Get input values
                const subject = document.getElementById('predict-subject').value;
                const category = document.getElementById('predict-category').value;
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

                            // Fill in target grade field with predicted value and style it green
                            const targetGradeInput = document.getElementById('target_grade');
                            if (targetGradeInput) {
                                targetGradeInput.value = data.predicted_grade;
                                targetGradeInput.style.color = '#28a745';
                                targetGradeInput.style.fontWeight = 'bold';
                            }
                        } else if (data.mode === 'hours_from_grade') {
                            resultDiv.textContent = `Required Hours: ${data.required_hours} hours`;
                            resultDiv.style.color = '#004085';
                            resultDiv.style.backgroundColor = '#d1ecf1';
                            resultDiv.style.border = '1px solid #bee5eb';

                            // Fill in hours field with predicted value and style it blue
                            const hoursInput = document.getElementById('hours');
                            if (hoursInput) {
                                hoursInput.value = data.required_hours;
                                hoursInput.style.color = '#007bff';
                                hoursInput.style.fontWeight = 'bold';
                            }
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

        // --- Reset Predictor Button Handler ---
        if (resetPredictorBtn) {
            resetPredictorBtn.addEventListener('click', function () {
                // Clear all predictor fields including subject
                clearPredictorFields(false);
                // Reset subject to first option
                if (predictSubject) {
                    predictSubject.selectedIndex = 0;
                    updatePredictorCategories();
                }
            });
        }

        // --- Add Subject Button Handler ---
        const addSubjectBtn = document.getElementById('add-subject-link');
        const addSubjectModal = document.getElementById('add-subject-modal');
        const newSubjectInput = document.getElementById('new-subject-input');
        const subjectModalConfirm = document.getElementById('subject-modal-confirm');
        const subjectModalCancel = document.getElementById('subject-modal-cancel');

        if (addSubjectBtn && addSubjectModal) {
            addSubjectBtn.addEventListener('click', function () {
                addSubjectModal.style.display = 'flex';
                newSubjectInput.value = '';
                newSubjectInput.focus();
            });

            subjectModalCancel.addEventListener('click', function () {
                addSubjectModal.style.display = 'none';
            });

            // Allow Enter key to submit
            newSubjectInput.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    subjectModalConfirm.click();
                }
            });

            // Allow Escape key to cancel
            addSubjectModal.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') {
                    addSubjectModal.style.display = 'none';
                }
            });

            subjectModalConfirm.addEventListener('click', function () {
                const subjectName = newSubjectInput.value.trim();

                if (!subjectName) {
                    showToast('Subject name cannot be empty', 'error');
                    return;
                }

                addSubjectModal.style.display = 'none';

                fetch('/add_subject', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ subject_name: subjectName })
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
        const deleteSubjectModal = document.getElementById('delete-subject-modal');
        const deleteSubjectMessage = document.getElementById('delete-subject-message');
        const deleteSubjectConfirm = document.getElementById('delete-subject-confirm');
        const deleteSubjectCancel = document.getElementById('delete-subject-cancel');

        const deleteSubjectFinalModal = document.getElementById('delete-subject-final-modal');
        const deleteSubjectFinalMessage = document.getElementById('delete-subject-final-message');
        const deleteSubjectFinalConfirm = document.getElementById('delete-subject-final-confirm');
        const deleteSubjectFinalCancel = document.getElementById('delete-subject-final-cancel');

        if (deleteSubjectBtn && deleteSubjectModal && deleteSubjectFinalModal) {
            let subjectToDelete = '';

            deleteSubjectBtn.addEventListener('click', function () {
                subjectToDelete = this.dataset.subject;
                deleteSubjectMessage.textContent = `Are you sure you want to delete the subject "${subjectToDelete}"?\n\nThis will delete ALL assignments and categories for this subject.`;
                deleteSubjectModal.style.display = 'flex';
            });

            deleteSubjectCancel.addEventListener('click', function () {
                deleteSubjectModal.style.display = 'none';
            });

            deleteSubjectConfirm.addEventListener('click', function () {
                deleteSubjectModal.style.display = 'none';
                deleteSubjectFinalMessage.textContent = `This action cannot be undone!\n\nDelete "${subjectToDelete}" and all its data permanently?`;
                deleteSubjectFinalModal.style.display = 'flex';
            });

            deleteSubjectFinalCancel.addEventListener('click', function () {
                deleteSubjectFinalModal.style.display = 'none';
            });

            deleteSubjectFinalConfirm.addEventListener('click', function () {
                deleteSubjectFinalModal.style.display = 'none';

                // Proceed with deletion
                fetch('/delete_subject', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ subject_name: subjectToDelete })
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

            // Allow Escape key to cancel on both modals
            deleteSubjectModal.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') {
                    deleteSubjectModal.style.display = 'none';
                }
            });

            deleteSubjectFinalModal.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') {
                    deleteSubjectFinalModal.style.display = 'none';
                }
            });
        }

        // --- Multi-Select Delete Functionality ---
        const selectedCountSpan = document.getElementById('selectedCount');

        function updateDeleteButton() {
            const selected = document.querySelectorAll('.select-assignment:checked');
            const deselectBtn = document.getElementById('deselectAllBtn');

            if (selected.length > 0) {
                deleteSelectedBtn.style.display = 'inline-block';
                selectedCountSpan.textContent = selected.length;
                if (deselectBtn) deselectBtn.style.display = 'inline-block';
            } else {
                deleteSelectedBtn.style.display = 'none';
                if (deselectBtn) deselectBtn.style.display = 'none';
            }

            // Update "select all" checkbox state
            const allCheckboxes = document.querySelectorAll('.select-assignment');
            const allChecked = allCheckboxes.length > 0 &&
                Array.from(allCheckboxes).every(cb => cb.checked);
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = allChecked;
            }
        }

        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', function () {
                const checkboxes = document.querySelectorAll('.select-assignment');
                checkboxes.forEach(cb => cb.checked = false);
                if (selectAllCheckbox) selectAllCheckbox.checked = false;
                updateDeleteButton();
            });
        }

        // Click anywhere on row to toggle checkbox (except buttons and inputs)
        if (assignmentTableBody) {
            assignmentTableBody.addEventListener('click', function (e) {
                // Don't toggle if clicking on buttons, inputs, selects, or the checkbox itself
                if (e.target.matches('button, input, select, .action-btn')) {
                    return;
                }

                // Don't toggle if clicking within an SVG (category tag icon)
                if (e.target.closest('svg')) {
                    return;
                }

                // Don't toggle if the click is on an action button or its parent
                if (e.target.closest('button')) {
                    return;
                }

                // Find the closest row
                const row = e.target.closest('tr[data-id]');
                if (!row) return;

                // Don't toggle for summary row
                if (row.classList.contains('summary-row')) return;

                // Don't toggle if row is in edit mode (has input/select elements)
                if (row.querySelector('input[name="study_time"], select[name="subject"]')) {
                    return;
                }

                // Find and toggle the checkbox
                const checkbox = row.querySelector('.select-assignment');
                if (checkbox) {
                    checkbox.checked = !checkbox.checked;
                    updateDeleteButton();
                }
            });

            // Stop propagation on checkbox clicks to prevent double-toggling
            assignmentTableBody.addEventListener('click', function (e) {
                if (e.target.classList.contains('select-assignment')) {
                    e.stopPropagation();
                }
            }, true);
        }

        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function () {
                const checkboxes = document.querySelectorAll('.select-assignment');
                checkboxes.forEach(cb => cb.checked = this.checked);
                updateDeleteButton();
            });
        }

        if (assignmentTableBody) {
            assignmentTableBody.addEventListener('change', function (e) {
                if (e.target.classList.contains('select-assignment')) {
                    updateDeleteButton();
                }
            });
        }

        if (deleteSelectedBtn) {
            deleteSelectedBtn.addEventListener('click', function () {
                const selected = document.querySelectorAll('.select-assignment:checked');
                const ids = Array.from(selected).map(cb => parseInt(cb.dataset.id));

                if (ids.length === 0) return;

                // Use confirmation modal
                const confirmModal = document.getElementById('confirmation-modal');
                const modalMessage = document.getElementById('modal-message');
                const modalConfirmYes = document.getElementById('modal-confirm-yes');
                const modalConfirmNo = document.getElementById('modal-confirm-no');

                if (confirmModal && modalMessage) {
                    modalMessage.textContent = `Are you sure you want to delete ${ids.length} assignment${ids.length > 1 ? 's' : ''}? This cannot be undone.`;
                    confirmModal.style.display = 'flex';

                    // Remove old listeners and add new ones
                    const newModalConfirmYes = modalConfirmYes.cloneNode(true);
                    modalConfirmYes.parentNode.replaceChild(newModalConfirmYes, modalConfirmYes);

                    const newModalConfirmNo = modalConfirmNo.cloneNode(true);
                    modalConfirmNo.parentNode.replaceChild(newModalConfirmNo, modalConfirmNo);

                    newModalConfirmYes.addEventListener('click', function () {
                        confirmModal.style.display = 'none';
                        const currentFilter = subjectFilterDropdown ? subjectFilterDropdown.value : '';

                        fetch(`/delete_multiple?current_filter=${currentFilter}`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            body: JSON.stringify({ ids: ids })
                        })
                            .then(response => response.json())
                            .then(data => {
                                if (data.status === 'success') {
                                    renderAssignmentTable(data.updated_assignments, data.summary, currentFilter);
                                    if (typeof ensureDragHandles === 'function') ensureDragHandles();
                                    if (selectAllCheckbox) selectAllCheckbox.checked = false;
                                    if (typeof ensureDragHandles === 'function') ensureDragHandles();
                                    updateDeleteButton();
                                    showToast(data.message, 'success');
                                } else {
                                    showToast(data.message, 'error');
                                }
                            })
                            .catch(error => {
                                console.error('Error:', error);
                                showToast('Failed to delete assignments', 'error');
                            });
                    });

                    newModalConfirmNo.addEventListener('click', function () {
                        confirmModal.style.display = 'none';
                    });
                }
            });
        }

        // Initialize total weight indicator on page load
        updateTotalWeightIndicator();

        // Update total weight indicator when category weights are edited
        if (categoryTableBody) {
            categoryTableBody.addEventListener('input', function (event) {
                if (event.target.matches('input[name="total_weight"]')) {
                    updateTotalWeightIndicator();
                }
            });
        }

        // Handle subject filter dropdown on home page
        if (subjectFilterVisible) {
            subjectFilterVisible.addEventListener('change', function () {
                const selectedSubject = this.value;
                // Update the hidden input
                if (subjectFilterDropdown) {
                    subjectFilterDropdown.value = selectedSubject;
                }

                // Filter table rows client-side without page reload
                const rows = assignmentTableBody.querySelectorAll('tr[data-id]');
                let visibleCount = 0;

                rows.forEach(row => {
                    const subjectCell = row.querySelector('td:nth-child(2)');
                    if (!subjectCell) return;

                    const rowSubject = subjectCell.textContent.trim();

                    if (selectedSubject === 'all' || rowSubject === selectedSubject) {
                        row.style.display = '';
                        visibleCount++;
                    } else {
                        row.style.display = 'none';
                    }
                });

                // Update or hide summary container
                const summaryContainer = document.getElementById('summary-container');
                if (summaryContainer) {
                    if (selectedSubject === 'all' || visibleCount === 0) {
                        summaryContainer.style.display = 'none';
                    } else {
                        summaryContainer.style.display = '';
                    }
                }
            });
        }

        // --- Rename Subject Logic ---
        const renameSubjectBtn = document.getElementById('rename-subject-btn');
        const renameSubjectModal = document.getElementById('rename-subject-modal');
        const renameSubjectInput = document.getElementById('rename-subject-input');
        const renameSubjectConfirm = document.getElementById('rename-subject-confirm');
        const renameSubjectCancel = document.getElementById('rename-subject-cancel');

        if (renameSubjectBtn && renameSubjectModal) {
            renameSubjectBtn.addEventListener('click', function () {
                const currentSubject = document.querySelector('.nav-center h1').childNodes[0].textContent.trim();
                renameSubjectInput.value = currentSubject;
                renameSubjectModal.style.display = 'flex';
                renameSubjectInput.focus();
            });

            renameSubjectCancel.addEventListener('click', function () {
                renameSubjectModal.style.display = 'none';
            });

            renameSubjectInput.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    renameSubjectConfirm.click();
                }
            });

            renameSubjectConfirm.addEventListener('click', function () {
                const newName = renameSubjectInput.value.trim();
                const currentSubject = document.querySelector('.nav-center h1').childNodes[0].textContent.trim();

                if (!newName) {
                    showToast('Subject name cannot be empty', 'error');
                    return;
                }

                if (newName === currentSubject) {
                    renameSubjectModal.style.display = 'none';
                    return;
                }

                const formData = new FormData();
                formData.append('old_name', currentSubject);
                formData.append('new_name', newName);

                fetch('/rename_subject', {
                    method: 'POST',
                    body: formData
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            window.location.href = `/subject/${encodeURIComponent(data.new_name)}`;
                        } else {
                            showToast(data.message, 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showToast('An error occurred while renaming the subject', 'error');
                    });
            });
        }


        const tbody = document.getElementById('study-table-body');
        if (!tbody) return;

        function ensureDragHandles() {
            const tb = document.getElementById('study-table-body');
            if (!tb) return;

            tb.querySelectorAll('tr.assignment-row').forEach(tr => {
                const td = tr.cells && tr.cells[0];
                if (!td) return;
                if (!tr.classList.contains('assignment-row')) tr.classList.add('assignment-row');
                if (!td.querySelector('.drag-handle')) {
                    const span = document.createElement('span');
                    span.className = 'drag-handle';
                    span.title = 'Drag';
                    span.setAttribute('aria-label', 'Drag to reorder');
                    span.setAttribute('draggable', 'true');
                    span.textContent = '⋮⋮';
                    td.insertBefore(span, td.firstChild);
                }
            });
        }


        // Run once immediately
        ensureDragHandles();
        //_kickwatch();            

        // --- Robust re-attacher (survives tbody replacement + odd re-renders) ---
        let _observedTbody = null;
        let _mo = null;

        function _observeCurrentTbody() {
            const tb = document.getElementById('study-table-body');
            if (!tb) return;

            if (tb !== _observedTbody) {
                if (_mo) _mo.disconnect();
                _mo = new MutationObserver(() => ensureDragHandles());
                // Watch rows being added/removed/replaced
                _mo.observe(tb, { childList: true });
                _observedTbody = tb;
            }
        }

        // Watch the whole document for a *new* tbody being inserted/replaced
        const _rootMO = new MutationObserver(() => {
            _observeCurrentTbody();
            ensureDragHandles();
        });
        _rootMO.observe(document.body, { childList: true, subtree: true });

        // Extra safety: if a render mutates attributes/character data only,
        // or fires outside MutationObserver timing, fix periodically for a bit.
        let _kickCount = 0;
        function _kickwatch() {
            // if rows exist but no handles, put them back
            const tb = document.getElementById('study-table-body');
            if (tb) {
                const hasRows = tb.querySelector('tr.assignment-row');
                const hasHandle = tb.querySelector('.drag-handle');
                if (hasRows && !hasHandle) ensureDragHandles();
            }
            if (_kickCount++ < 20) setTimeout(_kickwatch, 100); // try for ~2s
        }

        // initial bind
        _observeCurrentTbody();
        _kickwatch();




        const _tb = document.getElementById('study-table-body');
        if (_tb) {
            const mo = new MutationObserver(() => ensureDragHandles());
            mo.observe(_tb, { childList: true }); // only care when <tr>s are added/removed
        }

        let draggingEl = null;

        function rowFromEl(el) {
            return el && el.closest('tr.assignment-row');
        }

        // Start drag only from the handle
        tbody.addEventListener('pointerdown', (e) => {
            const cell = e.target.closest('td');
            const isFirstCell = cell && cell.cellIndex === 0;
            const handle = e.target.closest('.drag-handle');
            if (!handle && !isFirstCell) return;      // allow first cell as fallback
            const row = rowFromEl(handle || cell);
            if (!row) return;
            row.setAttribute('draggable', 'true');

        });


        // If user just clicks (no drag), remove draggable so it doesn't “stick”
        tbody.addEventListener('pointerup', (e) => {
            const row = rowFromEl(e.target);
            if (row) row.removeAttribute('draggable');
        });

        tbody.addEventListener('dragstart', (e) => {
            const row = rowFromEl(e.target);
            if (!row) return;
            draggingEl = row;
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', row.dataset.id);
            row.classList.add('dragging');
        });

        tbody.addEventListener('dragend', (e) => {
            const row = rowFromEl(e.target);
            if (row) {
                row.classList.remove('dragging');
                row.removeAttribute('draggable');
            }
            draggingEl = null;
        });

        tbody.addEventListener('dragover', (e) => {
            e.preventDefault(); // REQUIRED or drop won't fire
            const after = getRowAfterPointer(tbody, e.clientY);
            const current = draggingEl;
            if (!current) return;
            if (!after) tbody.appendChild(current);
            else if (after !== current) tbody.insertBefore(current, after);
        });

        tbody.addEventListener('drop', async (e) => {
            e.preventDefault();
            const ids = Array.from(tbody.querySelectorAll('tr.assignment-row'))
                .map(tr => parseInt(tr.dataset.id, 10))
                .filter(Number.isInteger);

            console.log('[DnD] Saving order:', ids);

            try {
                const r = await fetch('/api/assignments/reorder', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ order: ids })
                });
                const json = await r.json().catch(() => ({}));
                if (!r.ok || json.status !== 'ok') {
                    console.error('Reorder failed:', json);
                    showToast(json.message || 'Reorder failed', 'error');
                } else {
                    showToast('Order saved', 'success');
                    ensureDragHandles();
                    setTimeout(ensureDragHandles, 0);
                }
            } catch (err) {
                console.error('Network error saving order', err);
                showToast('Network error saving order', 'error');
            }
        });

        function getRowAfterPointer(container, y) {
            const rows = [...container.querySelectorAll('tr.assignment-row:not(.dragging)')];
            let closest = null;
            let closestOffset = Number.NEGATIVE_INFINITY;
            for (const row of rows) {
                const box = row.getBoundingClientRect();
                const offset = y - box.top - box.height / 2;
                if (offset < 0 && offset > closestOffset) {
                    closestOffset = offset;
                    closest = row;
                }
            }
            return closest;
        }

        function rowHTML(row) {
            const firstCell = `
        <td>
            <span class="drag-handle" title="Drag" aria-label="Drag to reorder" draggable="true">⋮⋮</span>
             <input type="checkbox" class="select-assignment" data-id="${row.id}">
        </td>`;

            // keep your prediction/non-prediction cells exactly like the Jinja template
            const studyTd = row.is_prediction
                ? `<td><input type="number" class="prediction-input hours-input" data-id="${row.id}" value="${row.study_time}" step="0.1" min="0" style="width: 80px;"> hours</td>`
                : `<td>${Number(row.study_time).toFixed(1)} hours</td>`;

            const gradeTd = row.is_prediction
                ? `<td><input type="number" class="prediction-input grade-input" data-id="${row.id}" value="${row.grade}" step="1" min="0" style="width: 80px;">%</td>`
                : `<td>${row.grade != null ? row.grade + '%' : '-'}</td>`;

            const actionsTd = row.is_prediction
                ? `<td><button class="action-btn predict-btn">Predict</button><button class="action-btn add-prediction-btn">Add</button><button class="action-btn delete-btn">Delete</button></td>`
                : `<td><button class="action-btn edit-btn">Edit</button><button class="action-btn delete-btn">Delete</button></td>`;

            return `
        <tr data-id="${row.id}" class="assignment-row${row.is_prediction ? ' prediction-row' : ''}">
        ${firstCell}
        <td>${row.subject}</td>
        <td><span class="category-tag">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>
            <line x1="7" y1="7" x2="7.01" y2="7"></line>
            </svg> ${row.category}</span></td>
        ${studyTd}
        <td>${row.assignment_name}</td>
        ${gradeTd}
        <td>${Number(row.weight).toFixed(2)}%</td>
        ${actionsTd}
        </tr>`;
        }


    });


