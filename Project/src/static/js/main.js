document.addEventListener('DOMContentLoaded',
    function () {
        // --- Top Navigation Dropdown Logic ---
        // Close dropdowns when clicking outside
        document.addEventListener('click', function (e) {
            if (!e.target.closest('.nav-dropdown')) {
                document.querySelectorAll('.nav-dropdown').forEach(dropdown => {
                    dropdown.classList.remove('open');
                });
            }
        });

        // Handle dropdown toggles on mobile (touch devices)
        document.querySelectorAll('.nav-dropdown .dropdown-toggle').forEach(toggle => {
            toggle.addEventListener('click', function (e) {
                e.preventDefault();
                const dropdown = this.closest('.nav-dropdown');
                const wasOpen = dropdown.classList.contains('open');

                // Close all other dropdowns
                document.querySelectorAll('.nav-dropdown').forEach(d => {
                    d.classList.remove('open');
                });

                // Toggle this one
                if (!wasOpen) {
                    dropdown.classList.add('open');
                }
            });
        });

        // Allow dropdown items to navigate normally (don't prevent default)
        document.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', function(e) {
                // Don't prevent default - let the link work
                // Just close the dropdown
                const dropdown = this.closest('.nav-dropdown');
                if (dropdown) {
                    dropdown.classList.remove('open');
                }
            });
        });

        // Legacy sidebar elements (kept for compatibility but not used)
        const subjectsToggle = document.getElementById('subjects-toggle');
        const subjectsSubmenu = document.getElementById('subjects-submenu');

        if (subjectsToggle) {
            subjectsToggle.addEventListener('click', (e) => {
                // Only prevent default if clicking directly on the toggle, not on child links
                if (e.target === subjectsToggle || e.target.closest('#subjects-toggle')) {
                    e.preventDefault();
                    subjectsToggle.parentElement.classList.toggle('active');
                }
            });
        }

        // --- Retired Subjects Submenu Toggle ---
        const retiredSubjectsToggle = document.getElementById('retired-subjects-toggle');
        const retiredSubjectsSubmenu = document.getElementById('retired-subjects-submenu');

        if (retiredSubjectsToggle) {
            retiredSubjectsToggle.addEventListener('click', (e) => {
                if (e.target === retiredSubjectsToggle || e.target.closest('#retired-subjects-toggle')) {
                    e.preventDefault();
                    retiredSubjectsToggle.parentElement.classList.toggle('active');
                }
            });
        }

        // Ensure retired subject links work properly
        if (retiredSubjectsSubmenu) {
            retiredSubjectsSubmenu.addEventListener('click', (e) => {
                const link = e.target.closest('a');
                if (link && link.href) {
                    // Allow default navigation
                    setTimeout(() => {
                        if (sidebar && sidebar.classList.contains('open')) {
                            toggleSidebar();
                        }
                    }, 100);
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

        // --- Theme System (Color Scheme + Dark Mode) ---
        const themeToggle = document.getElementById('theme-toggle');
        const schemeToggle = document.getElementById('scheme-toggle');

        // Load saved preferences
        let currentScheme = localStorage.getItem('colorScheme') || 'default';
        let currentMode = localStorage.getItem('theme') || 'light';

        // Apply saved theme on load
        function applyTheme(scheme, mode) {
            // Remove all theme classes
            document.body.classList.remove('toasty-mode', 'dark-mode');

            // Apply scheme
            if (scheme === 'toasty') {
                document.body.classList.add('toasty-mode');
            }

            // Apply mode
            if (mode === 'dark') {
                document.body.classList.add('dark-mode');
            }

            // Update toggle states
            if (themeToggle) themeToggle.checked = (mode === 'dark');
            if (schemeToggle) schemeToggle.checked = (scheme === 'toasty');
        }

        // Apply saved theme
        applyTheme(currentScheme, currentMode);

        // Dark mode toggle handler
        if (themeToggle) {
            themeToggle.addEventListener('change', () => {
                currentMode = themeToggle.checked ? 'dark' : 'light';
                localStorage.setItem('theme', currentMode);
                applyTheme(currentScheme, currentMode);
                updateTotalWeightIndicator();
            });
        }

        // Color scheme toggle handler
        if (schemeToggle) {
            schemeToggle.addEventListener('change', () => {
                currentScheme = schemeToggle.checked ? 'toasty' : 'default';
                localStorage.setItem('colorScheme', currentScheme);
                applyTheme(currentScheme, currentMode);
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
        // Grade Lock: Per-subject storage - each subject remembers its own grade lock state
        // Stored as object in localStorage: { "Math": true, "Science": false, ... }
        // Also synced with server database via API
        // Load from localStorage, default Grade Lock to true per subject, Show Predictions to false
        let gradeLockBySubject = {};
        try {
            const stored = localStorage.getItem('gradeLockBySubject');
            gradeLockBySubject = stored ? JSON.parse(stored) : {};
        } catch (e) {
            console.error('Error loading grade lock settings:', e);
            gradeLockBySubject = {};
        }

        // Load grade lock preferences from server
        async function loadGradeLockFromServer() {
            try {
                const response = await fetch('/api/grade_lock/get');
                if (response.ok) {
                    const data = await response.json();
                    if (data.status === 'success' && data.preferences) {
                        // Merge server preferences with local (server is source of truth)
                        gradeLockBySubject = data.preferences;
                        localStorage.setItem('gradeLockBySubject', JSON.stringify(gradeLockBySubject));
                        updateGradeLockButton();
                    }
                }
            } catch (e) {
                console.error('Error loading grade lock from server:', e);
            }
        }

        // Save grade lock preference to server
        async function saveGradeLockToServer(subject, gradeLock) {
            try {
                const response = await fetch('/api/grade_lock/set', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        subject: subject,
                        grade_lock: gradeLock
                    })
                });

                if (!response.ok) {
                    console.error('Failed to save grade lock to server');
                }
            } catch (e) {
                console.error('Error saving grade lock to server:', e);
            }
        }

        // Load preferences on page load
        loadGradeLockFromServer();

        // Helper function to get grade lock state for a subject
        function getGradeLock(subject) {
            // Default to true if not set
            return gradeLockBySubject[subject] !== undefined ? gradeLockBySubject[subject] : true;
        }

        // Helper function to set grade lock state for a subject
        function setGradeLock(subject, value) {
            gradeLockBySubject[subject] = value;
            localStorage.setItem('gradeLockBySubject', JSON.stringify(gradeLockBySubject));
            // Also save to server
            saveGradeLockToServer(subject, value);
        }

        // Helper function to get the current active subject
        function getCurrentSubject() {
            // First try the visible dropdown (for home page with 'all subjects')
            if (subjectFilterVisible && subjectFilterVisible.value && subjectFilterVisible.value !== 'all') {
                return subjectFilterVisible.value;
            }

            // Try the hidden filter input (set on subject-specific pages)
            if (subjectFilterDropdown && subjectFilterDropdown.value && subjectFilterDropdown.value !== 'all') {
                return subjectFilterDropdown.value;
            }

            return 'all';
        }

        // Helper function to check if we're on the main dashboard (All Subjects view)
        function isDashboard() {
            return getCurrentSubject() === 'all';
        }

        // Helper function to get current grade lock state based on active subject filter
        function getCurrentGradeLock() {
            const currentSubject = getCurrentSubject();
            if (currentSubject === 'all') {
                // When 'all' is selected, return true if ANY subject has grade lock on
                // Or default to true if no subjects are configured
                const subjects = Object.keys(weightCategoriesMap);
                if (subjects.length === 0) return true;
                return subjects.some(subj => getGradeLock(subj));
            }
            return getGradeLock(currentSubject);
        }

        let showPredictions = localStorage.getItem('showPredictions') === 'true';

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

        // --- NEW: Mutual Exclusivity for Subject Predictor Inputs ---
        if (predictOverallGradeInput && predictStudyTimeInput) {
            console.log('Prediction inputs found, attaching listeners');

            predictOverallGradeInput.addEventListener('input', function () {
                console.log('Overall Grade Input:', this.value);
                if (this.value) {
                    console.log('Clearing Study Time Input');
                    predictStudyTimeInput.value = '';
                }
            });

            predictStudyTimeInput.addEventListener('input', function () {
                console.log('Study Time Input:', this.value);
                if (this.value) {
                    console.log('Clearing Overall Grade Input');
                    predictOverallGradeInput.value = '';
                }
            });
        } else {
            console.error('Prediction inputs NOT found:', {
                overall: !!predictOverallGradeInput,
                study: !!predictStudyTimeInput
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
            console.log('showToast called:', message, type);
            let container = document.querySelector('.toast-container');
            if (!container) {
                console.log('Creating toast container');
                container = document.createElement('div');
                container.className = 'toast-container';
                document.body.appendChild(container);
            }
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            // Allow HTML content for lists
            toast.innerHTML = message;
            container.appendChild(toast);
            console.log('Toast element created:', toast);

            // Trigger reflow
            void toast.offsetWidth;

            requestAnimationFrame(() => {
                toast.classList.add('show');
                console.log('Toast show class added');
            });

            setTimeout(() => {
                toast.classList.remove('show');
                toast.addEventListener('transitionend', () => toast.remove());
            }, 4000); // Increased duration slightly for readability
        }

        function showConfirmation(message, row, type) {
            console.log('showConfirmation called:', message, type);
            
            if (!confirmationModal) {
                console.error('Confirmation modal not found!');
                // Fallback to browser confirm
                if (confirm(message)) {
                    itemToDelete = { row, type };
                    if (confirmYesBtn) confirmYesBtn.click();
                }
                return;
            }
            
            itemToDelete = {
                row,
                type
            };
            if (modalMsg) modalMsg.textContent = message;
            // Use both methods to ensure visibility
            confirmationModal.style.display = 'flex';
            confirmationModal.classList.add('active');
        }

        function hideConfirmation() {
            itemToDelete = {
                row: null,
                type: null
            };
            if (confirmationModal) {
                confirmationModal.style.display = 'none';
                confirmationModal.classList.remove('active');
            }
        }

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


        // --- Helper Functions ---


        function showValidationAlert(messages) {
            if (messages && messages.length > 0) {
                const messageHtml = `<ul style="margin: 0; padding-left: 20px; text-align: left;">${messages.map(msg => `<li>${msg}</li>`).join('')}</ul>`;
                showToast(messageHtml, 'error');
            }
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

        // Helper function to update grade lock button display
        function updateGradeLockButton() {
            if (!gradeLockBtn) return;

            const currentSubject = getCurrentSubject();
            const isLocked = getCurrentGradeLock();

            if (currentSubject === 'all') {
                gradeLockBtn.textContent = 'Grade Lock (All)';
            } else {
                gradeLockBtn.textContent = isLocked ? `Grade Lock (${currentSubject}): ON` : `Grade Lock (${currentSubject}): OFF`;
            }

            gradeLockBtn.classList.toggle('lock-on', isLocked);
            gradeLockBtn.classList.toggle('lock-off', !isLocked);
        }

        if (gradeLockBtn) {
            // Initialize button state
            updateGradeLockButton();

            gradeLockBtn.addEventListener('click', function () {
                const currentSubject = getCurrentSubject();

                if (currentSubject === 'all') {
                    showToast('Please select a specific subject to toggle grade lock', 'info');
                    return;
                }

                const currentState = getGradeLock(currentSubject);
                const newState = !currentState;
                setGradeLock(currentSubject, newState);

                updateGradeLockButton();

                // Remove forced styles if they were applied
                this.style.backgroundColor = '';

                // Update all grade input fields max attribute for current subject
                const allGradeInputs = document.querySelectorAll('input[name="grade"]');
                allGradeInputs.forEach(input => {
                    const row = input.closest('tr');
                    if (!row) return;

                    // Check if this row belongs to the current subject
                    const subjectCell = row.querySelector('td:nth-child(2)');
                    if (!subjectCell) return;

                    const rowSubject = subjectCell.textContent.trim();
                    if (rowSubject !== currentSubject) return;

                    if (newState) {
                        input.setAttribute('max', '100');
                    } else {
                        input.removeAttribute('max');
                    }
                });

                showToast(`Grade Lock for ${currentSubject}: ${newState ? 'ON' : 'OFF'}`, 'success');
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
            if (gradeInput && gradeInput.value) {
                // Get the subject for this row
                const subjectSelect = row.querySelector('select[name="subject"]');
                const subjectCell = row.querySelector('td:nth-child(2)');
                const rowSubject = subjectSelect ? subjectSelect.value : (subjectCell ? subjectCell.textContent.trim() : null);

                if (rowSubject && getGradeLock(rowSubject)) {
                    const gradeValue = parseFloat(gradeInput.value);
                    if (gradeValue > 100) {
                        errorMessages.push(`Grade cannot exceed 100% when Grade Lock is ON for ${rowSubject}.`);
                        gradeInput.classList.add('input-error');
                    }
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

        // Helper function to check if a name matches a category's naming pattern
        function nameMatchesPattern(name, pattern) {
            if (!name || !pattern) return false;

            // If pattern contains #, check if name matches the pattern with any number
            if (pattern.includes('#')) {
                // Convert pattern to regex: "Assignment #" -> "Assignment \d+"
                const regexPattern = pattern.replace('#', '\\d+');
                const regex = new RegExp(`^${regexPattern}$`);
                return regex.test(name);
            } else {
                // If pattern doesn't contain #, check exact match or pattern + number
                if (name === pattern) return true;
                // Also check if it's pattern + space + number (e.g., "Midterm 1")
                const regex = new RegExp(`^${pattern}\\s+\\d+$`);
                return regex.test(name);
            }
        }

        function applyWeightPreview(assignmentRow, isEditing = false, forceSubject = null, forceCategory = null, overrideRowCategory = null, originalCategory = null) {

            // Only revert if we are doing a "primary" update (derived from row), or maybe we shouldn't revert here at all?
            // If we iterate multiple categories, we don't want to clear previous updates.
            // Let's rely on the caller to revert if needed, or only revert if no force params.
            if (!forceSubject && !forceCategory) {
                revertWeightPreview();
            }

            // Get current subject and category from the row (what the user sees)
            let currentSubject, currentCategory;

            // Try to get from regular assignment selects first
            const subjectSelect = assignmentRow.querySelector('select[name="subject"]');
            const categorySelect = assignmentRow.querySelector('select[name="category"]');

            if (subjectSelect && categorySelect) {
                currentSubject = subjectSelect.value;
                currentCategory = overrideRowCategory || categorySelect.value;
            } else {
                // Handle prediction rows
                const subjectCell = assignmentRow.querySelector('td:nth-child(2)');
                const predictionCategorySelect = assignmentRow.querySelector('.prediction-category-select');

                if (subjectCell) {
                    currentSubject = subjectCell.textContent.trim();
                }
                if (predictionCategorySelect) {
                    currentCategory = overrideRowCategory || predictionCategorySelect.value;
                }
            }

            // Determine target subject/category
            const subject = forceSubject || currentSubject;
            const category = forceCategory || currentCategory;

            if (!subject || !category) return;
            const categoryData = (weightCategoriesMap[subject] || []).find(c => c.name === category);

            if (!categoryData) {
                return;
            }

            // Get existing rows in this subject/category
            const existingRows = Array.from(assignmentTableBody.querySelectorAll('tr[data-id]')).filter(row => {
                // If this is the row being edited, we handle it separately (via countToAdd), so skip it here
                if (isEditing && row === assignmentRow) return false;

                const cells = row.querySelectorAll('td');
                let rowSubject, rowCategory;

                // Check if it's in view mode (not being edited)
                if (cells.length > 1 && cells[2].querySelector('.category-tag')) {
                    rowSubject = cells[1].textContent.trim();
                    rowCategory = cells[2].querySelector('.category-tag').lastChild.textContent.trim();
                }
                // Check if it's in edit mode
                else {
                    const subjectSelect = row.querySelector('select[name="subject"]');
                    const categorySelect = row.querySelector('select[name="category"]');
                    if (subjectSelect && categorySelect) {
                        rowSubject = subjectSelect.value;
                        // If this row is somehow the one being edited (should be caught above, but just in case)
                        if (row === assignmentRow && overrideRowCategory) {
                            rowCategory = overrideRowCategory;
                        } else {
                            rowCategory = categorySelect.value;
                        }
                    }
                    // Check if it's a prediction row
                    else {
                        const predictionCategorySelect = row.querySelector('.prediction-category-select');
                        if (predictionCategorySelect && cells.length > 1) {
                            rowSubject = cells[1].textContent.trim();
                            rowCategory = predictionCategorySelect.value;
                        }
                    }
                }

                // Strict matching
                return rowSubject === subject && rowCategory === category;
            });

            console.log(`Found ${existingRows.length} existing rows for ${category}`);

            // Calculate new weight
            // Note: existingRows already excludes the row being edited (see filter above)
            // When editing and changing categories:
            // - If this is the NEW category (currentCategory), add 1 (the edited row will be in this category)
            // - If this is the ORIGINAL category, don't add or subtract (existingRows already has the correct count without the edited row)
            // - For other categories, use existingRows count as-is
            let countToAdd = 0;
            if (isEditing && assignmentRow) {
                const origCat = originalCategory || assignmentRow.dataset.originalCategory;
                if (currentCategory === category) {
                    // This is the new/target category, add 1 for the edited row
                    countToAdd = 1;
                }
                // For the original category or any other category, existingRows.length is already correct
                // because the edited row is excluded from existingRows
            } else if (!isEditing && assignmentRow && currentSubject === subject && currentCategory === category) {
                // Adding new assignment (not editing)
                countToAdd = 1;
            }

            console.log(`Calculating for ${category}. Row is in ${currentCategory}. Match? ${currentCategory === category}. CountToAdd: ${countToAdd}`);

            const newTotalAssessments = existingRows.length + countToAdd;
            const newCalculatedWeight = newTotalAssessments > 0 ? (categoryData.total_weight / newTotalAssessments) : 0;

            console.log(`New weight for ${category}: ${newCalculatedWeight.toFixed(2)}% (Total: ${newTotalAssessments})`);

            // Helper to update a row's weight
            const updateRowWeight = (row) => {
                const weightCell = row.querySelectorAll('td')[6]; // Weight is now at index 6
                if (weightCell) {
                    // Only save original state if not already saved (preserve true original)
                    if (!weightPreviewState.has(row)) {
                        weightPreviewState.set(row, weightCell.innerHTML);
                        console.log(`Saving original state for row ${row.dataset.id}: ${weightCell.innerHTML}`);
                    }
                    console.log(`Updating row ${row.dataset.id} weight to ${newCalculatedWeight.toFixed(2)}%`);
                    console.log(`  Before: ${weightCell.innerHTML}`);
                    weightCell.innerHTML = `<em>${newCalculatedWeight.toFixed(2)}%</em>`;
                    console.log(`  After: ${weightCell.innerHTML}`);
                }
            };

            // Update existing rows
            existingRows.forEach(updateRowWeight);

            // Update the row being edited/added if it should show in this category
            if (countToAdd === 1 && assignmentRow) {
                updateRowWeight(assignmentRow);
            }
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

        function createCategoryDropdown(subject, selectedCategory, assignmentId) {
            const categories = weightCategoriesMap[subject] || [];
            let options = '<option value="" disabled>-- Select Category --</option>';

            categories.forEach(cat => {
                const selected = cat.name === selectedCategory ? 'selected' : '';
                options += `<option value="${cat.name}" ${selected}>${cat.name}</option>`;
            });

            return `<select class="prediction-category-select" data-id="${assignmentId}" style="width: 120px; padding: 4px;">${options}</select>`;
        }

        function renderAssignmentTable(assignments, summaryData, subject) {
            assignmentTableBody.innerHTML = '';
            const onDashboard = isDashboard();

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
                            ${onDashboard ? '' : '<td>-</td>'}
                        `;

                    thead.appendChild(summaryRow);
                }
            }

            assignments.forEach((log, index) => {
                if (index < 3 || index >= assignments.length - 3) {
                    console.log(`Rendering assignment ${index}:`, { id: log.id, name: log.assignment_name, category: log.category, is_prediction: log.is_prediction, weight: log.weight });
                }
                const row = document.createElement('tr');
                row.dataset.id = log.id;

                // Add prediction class if this is a prediction
                if (log.is_prediction) {
                    row.classList.add('prediction-row');
                    row.dataset.isPrediction = 'true';
                }

                // Build the row HTML based on whether it's a prediction
                // On dashboard: show drag handle only. Otherwise: show drag handle + checkbox
                const firstCellHtml = onDashboard
                    ? `<td><span class="drag-handle" title="Drag" aria-label="Drag to reorder">⋮⋮</span></td>`
                    : `<td><span class="drag-handle" title="Drag" aria-label="Drag to reorder">⋮⋮</span><input type="checkbox" class="select-assignment" data-id="${log.id}"></td>`;

                if (log.is_prediction) {
                    // Create category dropdown for predictions
                    const categoryDropdownHtml = createCategoryDropdown(log.subject, log.category, log.id);

                    const predictionActionsHtml = onDashboard ? '' : '<td><button class="action-btn predict-btn">Predict</button><button class="action-btn add-prediction-btn">Add</button><button class="action-btn delete-btn">Delete</button></td>';
                    row.innerHTML = `${firstCellHtml}<td>${log.subject}</td><td class="prediction-category-cell" data-id="${log.id}"></td><td><input type="number" name="study_time" class="prediction-input hours-input" data-id="${log.id}" value="${log.study_time || 0}" step="0.1" style="width: 80px;"> hours</td><td class="prediction-name-cell" contenteditable="true" data-id="${log.id}">${log.assignment_name}</td><td><input type="number" name="grade" class="prediction-input grade-input" data-id="${log.id}" value="${log.grade || ''}" step="1" style="width: 80px;">%</td><td>${parseFloat(log.weight).toFixed(2)}%</td>${predictionActionsHtml}`;

                    // Insert the category dropdown
                    const categoryCell = row.querySelector('.prediction-category-cell');
                    if (categoryCell) {
                        categoryCell.innerHTML = categoryDropdownHtml;
                    }

                    // --- NEW: Mutual Exclusivity for Persisted Prediction Rows ---
                    const hoursInput = row.querySelector('.hours-input');
                    const gradeInput = row.querySelector('.grade-input');

                    if (hoursInput && gradeInput) {
                        hoursInput.addEventListener('input', function () {
                            if (this.value) {
                                gradeInput.value = '';
                            }
                        });

                        gradeInput.addEventListener('input', function () {
                            if (this.value) {
                                hoursInput.value = '';
                            }
                        });
                    }
                } else {
                    const regularActionsHtml = onDashboard ? '' : '<td><button class="action-btn edit-btn">Edit</button><button class="action-btn delete-btn">Delete</button></td>';
                    row.innerHTML = `${firstCellHtml}<td>${log.subject}</td><td><span class="category-tag"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg> ${log.category}</span></td><td>${parseFloat(log.study_time).toFixed(1)} hours</td><td>${log.assignment_name}</td><td>${log.grade !== null ? log.grade + '%' : '-'}</td><td>${parseFloat(log.weight).toFixed(2)}%</td>${regularActionsHtml}`;
                }

                assignmentTableBody.appendChild(row);
            });

            // Update delete button state after rendering (clears stale selection counts)
            if (typeof updateDeleteButton === 'function') {
                updateDeleteButton();
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

        // REMOVED: Nested duplicate of renderAssignmentTable (now at outer scope)

        async function handleAssignmentSave(row, suppressToast = false, forceAssignment = false) {
            // --- FIX: Do not revert the preview if validation fails ---
            if (!validateRow(row)) return;
            
            // Determine if this is a prediction row
            const isPredictionRow = row.dataset.isPrediction === 'true' || row.classList.contains('prediction-row');
            
            // Only revert weight preview when saving actual assignments (not predictions)
            // Predictions don't trigger weight recalculation, so previews should stay
            if (!isPredictionRow || forceAssignment) {
                revertWeightPreview();
            }

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
                    // Check if it's a prediction row with dropdown
                    const categorySelect = categoryCell.querySelector('.prediction-category-select');
                    if (categorySelect) {
                        formData.append('category', categorySelect.value);
                    } else {
                        // Regular row with category tag
                        const categorySpan = categoryCell.querySelector('.category-tag');
                        if (categorySpan) {
                            formData.append('category', categorySpan.lastChild.textContent.trim());
                        } else {
                            formData.append('category', categoryCell.textContent.trim());
                        }
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

            // For prediction rows, extract weight from the weight cell (it's displayed as text, not an input)
            if (!formData.has('weight')) {
                const weightCell = row.querySelector('td:nth-child(7)');
                if (weightCell) {
                    const weightText = weightCell.textContent.trim();
                    const weightValue = parseFloat(weightText);
                    if (!isNaN(weightValue)) {
                        formData.append('weight', weightValue);
                    }
                }
            }

            const currentSubjectFilter = subjectFilterDropdown.value;
            formData.append('current_filter', currentSubjectFilter);

            // Determine is_prediction status
            // If forceAssignment is true, we are converting to assignment, so is_prediction = false
            // Otherwise, check both dataset (for client-created rows) and class (for server-rendered rows)
            let isPrediction = row.dataset.isPrediction === 'true' || row.classList.contains('prediction-row');
            if (forceAssignment) {
                isPrediction = false;
            }
            formData.append('is_prediction', isPrediction ? 'true' : 'false');
            try {
                console.log('Sending save request to:', url);
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                console.log('Save response:', response.ok, result);
                if (!response.ok) {
                    showToast(result.message, 'error');
                    return;
                }
                if (!suppressToast) {
                    console.log('Calling showToast with:', result.message);
                    showToast(result.message, 'success');
                } else {
                    console.log('Toast suppressed');
                }
                
                // Hide the empty state after successful save
                const emptyState = document.getElementById('empty-state-container');
                if (emptyState) {
                    emptyState.style.display = 'none';
                }
                
                // Clear old weight preview state before re-render (DOM elements will be replaced)
                weightPreviewState.clear();
                
                renderAssignmentTable(result.updated_assignments, result.summary, currentSubjectFilter);
                if (typeof ensureDragHandles === 'function') {
                    ensureDragHandles();
                }
                if (isNew) {
                    updateCategoryTableRow(result.log.subject, result.log.category);
                }
                
                // Re-apply weight preview if this was a prediction save (not converting to assignment)
                // This keeps the preview showing for other rows in the same category
                if (isPrediction && !forceAssignment) {
                    // Find the newly saved prediction row and re-apply preview
                    const newPredictionRow = assignmentTableBody.querySelector(`tr[data-id="${result.log.id}"]`);
                    if (newPredictionRow) {
                        const subject = result.log.subject;
                        const category = result.log.category;
                        // Pass isEditing=true so it doesn't add +1 (the row is already saved and counted)
                        applyWeightPreview(newPredictionRow, true, subject, category);
                    }
                }
                
                // Update subject prediction (remaining weight)
                updateSubjectPrediction(null);
            } catch (error) {
                console.error('Save failed:', error);
                showToast('A network error occurred.', 'error');
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

        // REMOVED: Duplicate handleAssignmentSave (missing weight extraction logic)

        // Store pending category save data for naming update modal
        let pendingCategorySave = null;

        async function handleCategorySave(row, updateAssignments = null) {
            console.log('handleCategorySave called', row, updateAssignments);
            if (!validateRow(row)) {
                console.log('validateRow returned false');
                return;
            }
            console.log('validateRow passed');
            const catId = row.dataset.id;
            const isNew = !catId;
            console.log('catId:', catId, 'isNew:', isNew);

            // Get the new default_name value
            const defaultNameInput = row.querySelector('input[name="default_name"]');
            const newDefaultName = defaultNameInput ? defaultNameInput.value : '';
            console.log('newDefaultName:', newDefaultName);

            // For existing categories, check if default_name changed (only if updateAssignments not already decided)
            if (!isNew && updateAssignments === null && newDefaultName) {
                console.log('Checking if default_name changed...');
                try {
                    // Fetch the current category to compare default_name
                    console.log('Fetching category:', `/category/get/${catId}`);
                    const catResponse = await fetch(`/category/get/${catId}`);
                    console.log('catResponse.ok:', catResponse.ok);
                    if (catResponse.ok) {
                        const catResult = await catResponse.json();
                        console.log('catResult:', catResult);

                        if (catResult.status === 'success' && catResult.category) {
                            const oldDefaultName = catResult.category.default_name || '';
                            console.log('oldDefaultName:', oldDefaultName, 'newDefaultName:', newDefaultName);

                            // If default_name changed and both old and new have values, show the modal
                            if (oldDefaultName && oldDefaultName !== newDefaultName) {
                                console.log('Names are different, showing modal');
                                // Store the pending save data
                                pendingCategorySave = { row, catId, oldDefaultName, newDefaultName };

                                // Show the naming update modal
                                const updateNamingModal = document.getElementById('update-naming-modal');
                                const updateNamingExample = document.getElementById('update-naming-example');
                                console.log('updateNamingModal:', updateNamingModal);

                                if (updateNamingModal) {
                                    // Create an example of the change (number goes exactly where # is)
                                    const oldExample = oldDefaultName.replace('#', '1');
                                    const newExample = newDefaultName.replace('#', '1');
                                    updateNamingExample.textContent = `Example: "${oldExample}" → "${newExample}"`;
                                    updateNamingModal.classList.add('active');
                                    console.log('Modal should be visible now');
                                    return; // Wait for modal response
                                }
                            } else {
                                console.log('Names are the same or old is empty, proceeding with save');
                            }
                        }
                    } else {
                        console.log('catResponse not ok, status:', catResponse.status);
                    }
                } catch (error) {
                    console.error('Failed to fetch category for comparison:', error);
                    // Continue with save without the naming update option
                }
            } else {
                console.log('Skipping default_name check. isNew:', isNew, 'updateAssignments:', updateAssignments, 'newDefaultName:', newDefaultName);
            }

            console.log('Proceeding with the save...');
            // Proceed with the save
            const url = isNew ? '/category/add' : `/category/update/${catId}`;
            const formData = new FormData();
            row.querySelectorAll('input').forEach(input => formData.append(input.name, input.value));
            const subject = subjectFilterDropdown.value;
            formData.append('subject', subject);

            // Add the update_assignments flag if specified
            if (updateAssignments !== null) {
                formData.append('update_assignments', updateAssignments ? 'true' : 'false');
            }

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

        // Handle naming update modal buttons
        const updateNamingModal = document.getElementById('update-naming-modal');
        const updateNamingYes = document.getElementById('update-naming-yes');
        const updateNamingNo = document.getElementById('update-naming-no');

        if (updateNamingYes) {
            updateNamingYes.addEventListener('click', function () {
                if (updateNamingModal) updateNamingModal.classList.remove('active');
                if (pendingCategorySave) {
                    handleCategorySave(pendingCategorySave.row, true);
                    pendingCategorySave = null;
                }
            });
        }

        if (updateNamingNo) {
            updateNamingNo.addEventListener('click', function () {
                if (updateNamingModal) updateNamingModal.classList.remove('active');
                if (pendingCategorySave) {
                    handleCategorySave(pendingCategorySave.row, false);
                    pendingCategorySave = null;
                }
            });
        }

        if (confirmNoBtn) {
            confirmNoBtn.addEventListener('click', hideConfirmation);
        }
        if (confirmYesBtn) {
            confirmYesBtn.addEventListener('click', async function () {
                if (itemToDelete.row) {
                    // Clear any validation alerts when deleting
                    showValidationAlert([]);

                    const { row, type } = itemToDelete;

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
                        // Update delete button state after removing row
                        if (type === 'assignment' && typeof updateDeleteButton === 'function') {
                            updateDeleteButton();
                        }
                        // Show empty state if no more assignments (saved or unsaved)
                        if (type === 'assignment') {
                            const remainingRows = assignmentTableBody.querySelectorAll('tr.assignment-row');
                            if (remainingRows.length === 0) {
                                const emptyState = document.getElementById('empty-state-container');
                                if (emptyState) {
                                    emptyState.style.display = '';
                                }
                            }
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
                                
                                // Show empty state if no more assignments
                                const emptyState = document.getElementById('empty-state-container');
                                if (emptyState && result.updated_assignments && result.updated_assignments.length === 0) {
                                    emptyState.style.display = '';
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
                console.log('Category table clicked', event.target);
                const button = event.target.closest('.action-btn');
                if (!button) {
                    console.log('No action button found');
                    return;
                }
                console.log('Button found:', button.className);
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
                    console.log('Save button clicked, calling handleCategorySave');
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

            // Check if there are any categories defined for the current subject
            const currentSubjectFilter = subjectFilterDropdown ? subjectFilterDropdown.value : 'all';
            const isSubjectFiltered = currentSubjectFilter && currentSubjectFilter !== 'all';
            const allSubjects = Object.keys(weightCategoriesMap);
            
            // Determine which subject to check for categories
            const subjectToCheck = isSubjectFiltered ? currentSubjectFilter : (allSubjects[0] || '');
            const categoriesForSubject = weightCategoriesMap[subjectToCheck] || [];
            
            // If no categories defined, show info toast and don't add the row
            if (categoriesForSubject.length === 0) {
                if (isSubjectFiltered) {
                    showToast(`Please define a grading scheme for ${subjectToCheck} first. Use the Add Grading Scheme Category button below.`, 'info');
                } else if (allSubjects.length === 0) {
                    showToast('Please add a subject first using the Subjects dropdown menu.', 'info');
                } else {
                    showToast('Please define a grading scheme first. Use the Add Grading Scheme Category button below.', 'info');
                }
                return;
            }

            const newRow = document.createElement('tr');
            newRow.classList.add('assignment-row');               // <-- DnD relies on this
            if (isPrediction) {
                newRow.classList.add('prediction-row');
                newRow.dataset.isPrediction = 'true';
            }

            // Determine grade lock based on current subject filter or default to true
            const currentSubject = subjectFilterVisible ? subjectFilterVisible.value : 'all';
            const isGradeLockOn = currentSubject !== 'all' ? getGradeLock(currentSubject) : true;
            const gradeAttrs = isGradeLockOn ? 'min="0" max="100"' : 'min="0"';

            // Create subject select (reuse the variables we already have)
            const subjectSelect = document.createElement('select');
            subjectSelect.name = 'subject';
            subjectSelect.required = true;
            subjectSelect.setAttribute('autocomplete', 'off');

            if (isSubjectFiltered) {
                // If filtered, only show the filtered subject
                const option = document.createElement('option');
                option.value = currentSubjectFilter;
                option.textContent = currentSubjectFilter;
                option.selected = true;
                subjectSelect.appendChild(option);
            } else {
                // Show all subjects
                allSubjects.forEach(subj => {
                    const option = document.createElement('option');
                    option.value = subj;
                    option.textContent = subj;
                    subjectSelect.appendChild(option);
                });
            }

            // Create category select
            const categorySelect = document.createElement('select');
            categorySelect.name = 'category';
            categorySelect.required = true;
            categorySelect.setAttribute('autocomplete', 'off');

            // Populate categories based on selected subject
            const selectedSubject = isSubjectFiltered ? currentSubjectFilter : (allSubjects[0] || '');
            const categories = weightCategoriesMap[selectedSubject] || [];
            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.name;
                option.textContent = cat.name;
                categorySelect.appendChild(option);
            });

            // Add change handler for subject to update categories
            subjectSelect.addEventListener('change', function () {
                const newSubject = this.value;
                const newCategories = weightCategoriesMap[newSubject] || [];
                categorySelect.innerHTML = '';
                newCategories.forEach(cat => {
                    const option = document.createElement('option');
                    option.value = cat.name;
                    option.textContent = cat.name;
                    categorySelect.appendChild(option);
                });
            });

            // Create TD elements
            const subjectTd = document.createElement('td');
            subjectTd.appendChild(subjectSelect);

            const categoryTd = document.createElement('td');
            categoryTd.appendChild(categorySelect);

            newRow.appendChild(document.createElement('td')); // Checkbox
            newRow.appendChild(subjectTd);
            newRow.appendChild(categoryTd);

            // Inputs
            if (isPrediction) {
                newRow.innerHTML += `
                <td><input type="number" name="study_time" class="prediction-input hours-input" step="0.1" min="0" placeholder="Hours" style="width: 70px;"> hours</td>
                <td><input type="text" name="assignment_name" class="prediction-input" placeholder="Assignment Name" value="Prediction" style="width: 150px;"></td>
                <td><input type="number" name="grade" class="prediction-input grade-input" step="1" ${gradeAttrs} placeholder="Grade" style="width: 60px;">%</td>
                <td class="weight-display">0.00%</td>
                <td><button class="action-btn predict-btn">Predict</button><button class="action-btn delete-btn">Delete</button></td>
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

            // Re-append subject and category cells because innerHTML += wipes them out
            const cells = newRow.querySelectorAll('td');
            cells[1].innerHTML = '';
            cells[1].appendChild(subjectSelect);
            cells[2].innerHTML = '';
            cells[2].appendChild(categorySelect);

            assignmentTableBody.appendChild(newRow);
            
            // Hide empty state when a new row is added
            const emptyState = document.getElementById('empty-state-container');
            if (emptyState) {
                emptyState.style.display = 'none';
            }

            // If subject is filtered, trigger change event to populate categories and potentially default name
            if (isSubjectFiltered) {
                subjectSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }

            // Autofill name and weight for both regular and prediction rows
            if (categorySelect.value) {
                const subject = subjectSelect.value;
                const categoryName = categorySelect.value;
                const categoryData = (weightCategoriesMap[subject] || []).find(c => c.name === categoryName);
                
                if (categoryData) {
                    // Count existing assignments in this category
                    const existingCount = Array.from(assignmentTableBody.querySelectorAll('tr[data-id]')).filter(r => {
                        const rCells = r.querySelectorAll('td');
                        if (rCells.length < 2) return false;
                        const rSubject = rCells[1].textContent.trim();
                        if (rSubject !== subject) return false;
                        const categoryTag = rCells[2].querySelector('.category-tag');
                        if (categoryTag) {
                            return categoryTag.lastChild.textContent.trim() === categoryName;
                        }
                        const predSelect = rCells[2].querySelector('.prediction-category-select');
                        if (predSelect) {
                            return predSelect.value === categoryName;
                        }
                        return false;
                    }).length;

                    // Fill in weight display
                    const weightCell = cells[6];
                    if (weightCell) {
                        const newWeight = categoryData.total_weight / (existingCount + 1);
                        weightCell.innerHTML = `<em>${newWeight.toFixed(2)}%</em>`;
                    }

                    // Fill in assignment name
                    const assignmentNameInput = newRow.querySelector('input[name="assignment_name"]');
                    if (assignmentNameInput && categoryData.default_name) {
                        if (categoryData.default_name.includes('#')) {
                            assignmentNameInput.value = categoryData.default_name.replace('#', existingCount + 1);
                        } else {
                            assignmentNameInput.value = categoryData.default_name;
                        }
                    }

                    // Apply weight preview for existing rows in this category
                    applyWeightPreview(newRow, false);
                }
            }

            // --- NEW: Mutual Exclusivity for Prediction Row Inputs ---
            if (isPrediction) {
                const hoursInput = newRow.querySelector('.hours-input');
                const gradeInput = newRow.querySelector('.grade-input');

                if (hoursInput && gradeInput) {
                    hoursInput.addEventListener('input', function () {
                        if (this.value) {
                            gradeInput.value = '';
                        }
                    });

                    gradeInput.addEventListener('input', function () {
                        if (this.value) {
                            hoursInput.value = '';
                        }
                    });
                }
            }
        }

        if (addRowBtn) {
            addRowBtn.addEventListener('click', () => addNewRow(false));
        }

        const addPredictionBtn = document.getElementById('addPredictionBtn');
        if (addPredictionBtn) {
            addPredictionBtn.addEventListener('click', () => {
                // Check if subject filter is set


                const currentSubjectFilter = subjectFilterDropdown ? subjectFilterDropdown.value : 'all';
                const isSubjectFiltered = currentSubjectFilter && currentSubjectFilter !== 'all';

                const allSubjects = Object.keys(weightCategoriesMap);

                // subject <select>
                const subjectSelect = document.createElement('select');
                subjectSelect.name = 'subject';
                subjectSelect.required = true;
                subjectSelect.setAttribute('autocomplete', 'off');


                // Create an editable prediction row (NOT saved to database yet)
                // User must select category and click "Predict" or save manually
                addNewRow(true);  // true = is a prediction
                showToast('Select a category and enter details, then click Predict', 'info');
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

                    // Store original category on the row for weight preview calculations
                    row.dataset.originalCategory = categoryText;
                    const studyTimeText = cells[3].textContent.trim();
                    const studyTimeValue = parseFloat(studyTimeText) || 0;
                    const assignmentNameText = cells[4].textContent.trim();
                    const gradeText = cells[5].textContent.trim();
                    const gradeValue = gradeText === '-' ? '' : parseInt(gradeText, 10);

                    // Get grade lock state for this row's subject
                    const rowGradeLock = getGradeLock(subjectText);
                    const gradeAttributes = rowGradeLock ? 'min="0" max="100"' : 'min="0"';

                    // Get all subjects from weightCategoriesMap
                    const allSubjects = Object.keys(weightCategoriesMap);

                    // Create subject select dropdown
                    let subjectSelectHtml = '<select name="subject" required>';
                    allSubjects.forEach(subj => {
                        const selected = subj === subjectText ? ' selected' : '';
                        subjectSelectHtml += `<option value="${subj}"${selected}>${subj}</option>`;
                    });
                    subjectSelectHtml += '</select>';

                    // Create category select dropdown (will be populated based on subject)
                    const categories = weightCategoriesMap[subjectText] || [];
                    let categorySelectHtml = '<select name="category" required>';
                    categories.forEach(cat => {
                        const selected = cat.name === categoryText ? ' selected' : '';
                        categorySelectHtml += `<option value="${cat.name}"${selected}>${cat.name}</option>`;
                    });
                    categorySelectHtml += '</select>';

                    // Replace cells with input fields
                    cells[1].innerHTML = subjectSelectHtml;
                    cells[2].innerHTML = categorySelectHtml;
                    cells[3].innerHTML = `<input type="number" name="study_time" value="${studyTimeValue}" step="0.1" min="0" required style="width: 70px;"> hours`;
                    cells[4].innerHTML = `<input type="text" name="assignment_name" value="${assignmentNameText}" required style="width: 150px;">`;
                    cells[5].innerHTML = `<input type="number" name="grade" value="${gradeValue}" step="1" ${gradeAttributes} style="width: 60px;">%`;

                    // Add change handler for subject select to update category options
                    const subjectSelect = cells[1].querySelector('select[name="subject"]');
                    if (subjectSelect) {
                        subjectSelect.addEventListener('change', function () {
                            const newSubject = this.value;
                            const newCategories = weightCategoriesMap[newSubject] || [];
                            const categorySelect = cells[2].querySelector('select[name="category"]');
                            if (categorySelect) {
                                categorySelect.innerHTML = '';
                                newCategories.forEach(cat => {
                                    const option = document.createElement('option');
                                    option.value = cat.name;
                                    option.textContent = cat.name;
                                    categorySelect.appendChild(option);
                                });
                            }
                        });
                    }

                    // Add change handler for category select to update weight preview
                    const categorySelect = cells[2].querySelector('select[name="category"]');
                    if (categorySelect) {
                        categorySelect.addEventListener('change', function (e) {
                            const isEditing = !!row.dataset.id;
                            const currentSubject = cells[1].querySelector('select[name="subject"]').value;
                            const originalCat = row.dataset.originalCategory;

                            console.log(`========== CATEGORY CHANGED ==========`);
                            console.log(`New category: ${this.value}, Original category: ${originalCat}`);
                            console.log(`weightPreviewState size before revert: ${weightPreviewState.size}`);

                            // Revert any existing previews first to prevent stale state
                            revertWeightPreview();

                            console.log(`weightPreviewState size after revert: ${weightPreviewState.size}`);

                            // Update ALL categories for this subject to handle moving assignments between categories
                            const categories = weightCategoriesMap[currentSubject] || [];
                            console.log(`Processing ${categories.length} categories:`, categories.map(c => c.name));
                            categories.forEach(cat => {
                                console.log(`--- Starting category: ${cat.name} ---`);
                                applyWeightPreview(row, isEditing, currentSubject, cat.name, this.value, originalCat);
                            });
                            console.log(`========== DONE ==========`);

                            // Stop propagation to prevent the assignmentTableBody change handler from running
                            e.stopPropagation();
                        });
                    }
                } else if (button.classList.contains('save-btn')) {
                    await handleAssignmentSave(row);
                } else if (button.classList.contains('delete-btn')) {
                    showConfirmation("Are you sure you want to delete this assessment?", row, 'assignment');
                } else if (button.classList.contains('add-prediction-btn')) {
                    // Convert prediction to assignment - clear the grade first
                    const gradeInput = row.querySelector('.grade-input');
                    if (gradeInput) gradeInput.value = '';
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

                    // Validate: need either hours OR grade (target), but not both populated for prediction
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

                    // Get subject - check for select element first (new row), then text content
                    const subjectCell = row.querySelector('td:nth-child(2)');
                    const subjectSelect = subjectCell.querySelector('select');
                    const subject = subjectSelect ? subjectSelect.value : subjectCell.textContent.trim();
                    
                    // Get category - check for any select element first (prediction dropdown or new row select)
                    const categoryCell = row.querySelector('td:nth-child(3)');
                    const categorySelect = categoryCell.querySelector('select');  // Any select in the category cell
                    let category;
                    if (categorySelect) {
                        category = categorySelect.value;
                    } else {
                        const categoryTag = categoryCell.querySelector('.category-tag');
                        if (categoryTag) {
                            // Get only the text node, not child elements
                            const textNodes = Array.from(categoryTag.childNodes).filter(n => n.nodeType === Node.TEXT_NODE);
                            category = textNodes.map(n => n.textContent).join('').trim();
                        } else {
                            category = categoryCell.textContent.trim();
                        }
                    }

                    const formData = new FormData();
                    formData.append('subject', subject);
                    formData.append('weight', weight);
                    formData.append('grade_lock', getGradeLock(subject) ? 'true' : 'false');
                    formData.append('category', category);
                    
                    // Pass the row ID if it exists, so the prediction excludes this row from history
                    const rowId = row.dataset.id;
                    if (rowId) {
                        formData.append('exclude_id', rowId);
                    }

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
                                    gradeInput.classList.add('predicted-value');
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
            assignmentTableBody.addEventListener('change', function (event) {
                const target = event.target;
                if (target.name === 'category') {
                    const row = target.closest('tr');

                    // Revert any existing weight preview first
                    revertWeightPreview();

                    // Clear all fields except subject, category, and assignment name (name cleared conditionally below)
                    const studyTimeInput = row.querySelector('input[name="study_time"]');
                    const assignmentNameInput = row.querySelector('input[name="assignment_name"]');
                    const gradeInput = row.querySelector('input[name="grade"]');
                    const weightInput = row.querySelector('input[name="weight"]');

                    // Save current name to check if it should be updated
                    const currentName = assignmentNameInput ? assignmentNameInput.value.trim() : '';

                    if (studyTimeInput) studyTimeInput.value = '';
                    if (gradeInput) gradeInput.value = '';
                    if (weightInput) weightInput.value = '';

                    // Fill in defaults if category is selected
                    const subject = row.querySelector('select[name="subject"]').value;
                    const categoryName = target.value;

                    if (subject && categoryName) {
                        const categoryData = (weightCategoriesMap[subject] || []).find(c => c.name === categoryName);
                        if (categoryData) {
                            // Fill in weight - calculate what the weight will be after adding this assignment
                            // Count current assignments in this category (from the table, not cached data)
                            const currentCount = Array.from(assignmentTableBody.querySelectorAll('tr[data-id]')).filter(r => {
                                const cells = r.querySelectorAll('td');
                                if (cells.length < 2) return false;

                                const rowSubject = cells[1].textContent.trim();
                                if (rowSubject !== subject) return false;

                                // Check category using same logic as applyWeightPreview
                                const categoryTag = cells[2].querySelector('.category-tag');
                                if (categoryTag) {
                                    return categoryTag.lastChild.textContent.trim() === categoryName;
                                }

                                // Also check for prediction rows
                                const predictionCategorySelect = cells[2].querySelector('.prediction-category-select');
                                if (predictionCategorySelect) {
                                    return predictionCategorySelect.value === categoryName;
                                }

                                return false;
                            }).length;

                            // Fill in weight - calculate what the weight will be after adding this assignment
                            if (weightInput) {
                                // New weight will be total_weight / (current + 1)
                                const newWeight = categoryData.total_weight / (currentCount + 1);
                                weightInput.value = newWeight.toFixed(2);

                                console.log('New Assignment Weight Calculation:', {
                                    subject,
                                    category: categoryName,
                                    totalWeight: categoryData.total_weight,
                                    currentCount,
                                    newWeight: newWeight.toFixed(2)
                                });
                            }

                            // Fill in default assignment name if available
                            // Only update if: name is empty OR matches any category's naming pattern
                            if (assignmentNameInput && categoryData.default_name) {
                                const isNewRow = !row.dataset.id;

                                // Check if current name matches any category pattern for this subject
                                let matchesAnyPattern = false;
                                if (currentName && !isNewRow) {
                                    const allCategories = weightCategoriesMap[subject] || [];
                                    matchesAnyPattern = allCategories.some(cat => {
                                        return cat.default_name && nameMatchesPattern(currentName, cat.default_name);
                                    });
                                }

                                const shouldUpdateName = isNewRow || !currentName || matchesAnyPattern;

                                if (shouldUpdateName) {
                                    if (categoryData.default_name.includes('#')) {
                                        // Use the precise count from currentCount variable calculated above
                                        const newCount = currentCount + 1;
                                        assignmentNameInput.value = categoryData.default_name.replace('#', newCount);
                                    } else {
                                        assignmentNameInput.value = categoryData.default_name;
                                    }
                                }
                            }    // else: preserve the custom name
                        }

                        // Apply weight preview for both new and edited assignments
                        const isEditing = !!row.dataset.id;
                        applyWeightPreview(row, isEditing);
                    }
                }
            });
            assignmentTableBody.addEventListener('keydown', async function (event) {
                if (event.key === 'Enter' && event.target.matches('input, select')) {
                    // Don't handle Enter for prediction rows (they have their own handler)
                    const row = event.target.closest('tr');
                    if (row && row.classList.contains('prediction-row')) {
                        return;
                    }

                    event.preventDefault();
                    showValidationAlert([]); // Clear old errors before trying to save all
                    const editedRows = assignmentTableBody.querySelectorAll('tr:has(.save-btn)');
                    // Only suppress toast if there are multiple rows being saved
                    const suppressToast = editedRows.length > 1;
                    for (const row of editedRows) {
                        await handleAssignmentSave(row, suppressToast);
                    }
                    // Show a single toast if multiple rows were saved
                    if (editedRows.length > 1) {
                        showToast(`${editedRows.length} assessments saved!`, 'success');
                    }
                }
            });




            // --- Prediction Feature Event Listeners ---
            if (assignmentTableBody) {
                // Note: Enter key handling for predictions is done by the handler at line ~1652
                // which clicks the predict button when Enter is pressed in .prediction-input fields

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

                // Handle prediction name editing - save on blur
                assignmentTableBody.addEventListener('blur', async function (event) {
                    const target = event.target;
                    if (!target.classList.contains('prediction-name-cell')) return;

                    const assignmentId = target.dataset.id;
                    const newName = target.textContent.trim();
                    const row = target.closest('tr');

                    if (!assignmentId || !newName || !row) return;

                    // Save the updated name
                    const subjectCell = row.querySelector('td:nth-child(2)');
                    const categoryCell = row.querySelector('td:nth-child(3)');
                    const hoursInput = row.querySelector('.hours-input');
                    const gradeInput = row.querySelector('.grade-input');
                    const weightCell = row.querySelector('td:nth-child(7)');

                    const formData = new FormData();
                    formData.append('assignment_name', newName);
                    formData.append('subject', subjectCell.textContent.trim());

                    const categorySelect = categoryCell.querySelector('.prediction-category-select');
                    if (categorySelect) {
                        formData.append('category', categorySelect.value);
                    }

                    formData.append('study_time', hoursInput ? hoursInput.value : 0);
                    formData.append('grade', gradeInput ? gradeInput.value : '');
                    formData.append('weight', parseFloat(weightCell.textContent) || 0);
                    formData.append('is_prediction', 'true');

                    try {
                        await fetch(`/update/${assignmentId}`, {
                            method: 'POST',
                            body: formData
                        });
                    } catch (error) {
                        console.error('Failed to update prediction name:', error);
                    }
                }, true);

                // Handle prediction name editing - save on Enter key
                assignmentTableBody.addEventListener('keydown', function (event) {
                    if (event.key === 'Enter' && event.target.classList.contains('prediction-name-cell')) {
                        event.preventDefault();
                        event.target.blur(); // Trigger blur to save
                    }
                }, true);

                // Handle category dropdown change for predictions
                assignmentTableBody.addEventListener('change', function (event) {
                    const target = event.target;
                    if (!target.classList.contains('prediction-category-select')) return;

                    const assignmentId = target.dataset.id;
                    const newCategory = target.value;
                    const row = target.closest('tr');

                    if (!assignmentId || !newCategory || !row) return;

                    // Clear study time and grade fields when category changes
                    const hoursInput = row.querySelector('.hours-input');
                    const gradeInput = row.querySelector('.grade-input');
                    const assignmentNameCell = row.querySelector('td:nth-child(5)');

                    // Save current name to check if it should be updated
                    const currentName = assignmentNameCell ? assignmentNameCell.textContent.trim() : '';

                    if (hoursInput) hoursInput.value = '';
                    if (gradeInput) gradeInput.value = '';

                    // Calculate and update weight display (but don't save to database yet)
                    const subjectCell = row.querySelector('td:nth-child(2)');
                    const subject = subjectCell.textContent.trim();
                    const categories = weightCategoriesMap[subject] || [];
                    const categoryDef = categories.find(c => c.name === newCategory);

                    if (categoryDef) {
                        // Count existing assignments in this category (excluding this prediction)
                        const existingInCategory = Array.from(assignmentTableBody.querySelectorAll('tr[data-id]')).filter(r => {
                            if (r.dataset.id === assignmentId) return false; // Exclude current prediction
                            const rSubject = r.querySelector('td:nth-child(2)')?.textContent.trim();
                            const rCategoryCell = r.querySelector('td:nth-child(3)');
                            let rCategory = '';

                            // Handle both dropdown and text category cells
                            const categorySelect = rCategoryCell?.querySelector('.prediction-category-select');
                            if (categorySelect) {
                                rCategory = categorySelect.value;
                            } else {
                                const categoryTag = rCategoryCell?.querySelector('.category-tag');
                                rCategory = categoryTag?.lastChild?.textContent?.trim() || '';
                            }

                            return rSubject === subject && rCategory === newCategory;
                        }).length;

                        const weight = categoryDef.total_weight / (existingInCategory + 1);

                        // Update weight display in the row
                        const weightCell = row.querySelector('td:nth-child(7)');
                        if (weightCell) {
                            weightCell.textContent = weight.toFixed(2) + '%';
                        }

                        // Update assignment name smartly - only if name is empty OR matches a naming pattern
                        if (assignmentNameCell) {
                            // Check if current name matches any category pattern for this subject
                            let matchesAnyPattern = false;
                            if (currentName) {
                                const allCategories = categories || [];
                                matchesAnyPattern = allCategories.some(cat => {
                                    return cat.default_name && nameMatchesPattern(currentName, cat.default_name);
                                });
                                // Also check if it's just "Prediction"
                                if (currentName === 'Prediction') {
                                    matchesAnyPattern = true;
                                }
                            }

                            const shouldUpdateName = !currentName || matchesAnyPattern;

                            if (shouldUpdateName) {
                                // If name was empty or matches a pattern, set to new category's default or 'Prediction'
                                if (categoryDef.default_name) {
                                    if (categoryDef.default_name.includes('#')) {
                                        const count = existingInCategory + 1;
                                        assignmentNameCell.textContent = categoryDef.default_name.replace('#', count);
                                    } else {
                                        assignmentNameCell.textContent = categoryDef.default_name;
                                    }
                                } else {
                                    assignmentNameCell.textContent = 'Prediction';
                                }
                            }
                            // else: preserve the custom name
                        }
                    }

                    // Apply weight preview to show how weights will change for this category
                    applyWeightPreview(row, true);
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
                    formData.append('grade_lock', getGradeLock(subject) ? 'true' : 'false');

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

            // --- Retire Subject Button Handler ---
            const retireSubjectBtn = document.getElementById('retire-subject-btn');
            const retireSubjectModal = document.getElementById('retire-subject-modal');
            const retireSubjectMessage = document.getElementById('retire-subject-message');
            const retireSubjectConfirm = document.getElementById('retire-subject-confirm');
            const retireSubjectCancel = document.getElementById('retire-subject-cancel');

            if (retireSubjectBtn && retireSubjectModal) {
                let subjectToRetire = '';

                retireSubjectBtn.addEventListener('click', function () {
                    subjectToRetire = this.dataset.subject;
                    retireSubjectMessage.textContent = `Are you sure you want to retire "${subjectToRetire}"?\n\nRetired subjects won't appear in the main subjects list, but you can still access them from "Retired Subjects" in the menu.`;
                    retireSubjectModal.style.display = 'flex';
                });

                retireSubjectCancel.addEventListener('click', function () {
                    retireSubjectModal.style.display = 'none';
                });

                retireSubjectConfirm.addEventListener('click', function () {
                    retireSubjectModal.style.display = 'none';
                    fetch('/retire_subject', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: new URLSearchParams({ subject_name: subjectToRetire })
                    })
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'success') {
                                showToast(data.message, 'success');
                                // Reload page to update sidebar
                                setTimeout(() => window.location.reload(), 1000);
                            } else {
                                showToast(data.message, 'error');
                            }
                        })
                        .catch(error => {
                            showToast('Error retiring subject: ' + error.message, 'error');
                        });
                });
            }

            // --- Restore Subject Button Handler ---
            const restoreSubjectBtn = document.getElementById('restore-subject-btn');
            const restoreSubjectModal = document.getElementById('restore-subject-modal');
            const restoreSubjectMessage = document.getElementById('restore-subject-message');
            const restoreSubjectConfirm = document.getElementById('restore-subject-confirm');
            const restoreSubjectCancel = document.getElementById('restore-subject-cancel');

            if (restoreSubjectBtn && restoreSubjectModal) {
                let subjectToRestore = '';

                restoreSubjectBtn.addEventListener('click', function () {
                    subjectToRestore = this.dataset.subject;
                    restoreSubjectMessage.textContent = `Restore "${subjectToRestore}" to active subjects?`;
                    restoreSubjectModal.style.display = 'flex';
                });

                restoreSubjectCancel.addEventListener('click', function () {
                    restoreSubjectModal.style.display = 'none';
                });

                restoreSubjectConfirm.addEventListener('click', function () {
                    restoreSubjectModal.style.display = 'none';
                    fetch('/unretire_subject', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: new URLSearchParams({ subject_name: subjectToRestore })
                    })
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'success') {
                                showToast(data.message, 'success');
                                // Reload page to update sidebar
                                setTimeout(() => window.location.reload(), 1000);
                            } else {
                                showToast(data.message, 'error');
                            }
                        })
                        .catch(error => {
                            showToast('Error restoring subject: ' + error.message, 'error');
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
                    deleteSubjectMessage.textContent = `Are you sure you want to delete the subject "${subjectToDelete}"?\n\nThis will delete ALL assessments and categories for this subject.`;
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
                        modalMessage.textContent = `Are you sure you want to delete ${ids.length} assessment${ids.length > 1 ? 's' : ''}? This cannot be undone.`;
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
                                        
                                        // Show empty state if no more assignments
                                        const emptyState = document.getElementById('empty-state-container');
                                        if (emptyState && data.updated_assignments && data.updated_assignments.length === 0) {
                                            emptyState.style.display = '';
                                        }
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

                    // Update grade lock button for new subject
                    updateGradeLockButton();

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

                // Query for all tr elements, not just those with assignment-row class
                tb.querySelectorAll('tr[data-id]').forEach(tr => {
                    const td = tr.cells && tr.cells[0];
                    if (!td) return;
                    // Add assignment-row class if not present
                    if (!tr.classList.contains('assignment-row')) tr.classList.add('assignment-row');
                    // Add drag handle if not present
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
                    // Watch rows being added/removed/replaced AND changes to descendants
                    _mo.observe(tb, { childList: true, subtree: true, characterData: true });
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
                const onDashboard = isDashboard();
                // On dashboard: show drag handle only. Otherwise: show drag handle + checkbox
                const firstCell = onDashboard
                    ? `<td><span class="drag-handle" title="Drag" aria-label="Drag to reorder" draggable="true">⋮⋮</span></td>`
                    : `<td><span class="drag-handle" title="Drag" aria-label="Drag to reorder" draggable="true">⋮⋮</span><input type="checkbox" class="select-assignment" data-id="${row.id}"></td>`;

                // keep your prediction/non-prediction cells exactly like the Jinja template
                const studyTd = row.is_prediction
                    ? `<td><input type="number" class="prediction-input hours-input" data-id="${row.id}" value="${row.study_time}" step="0.1" min="0" style="width: 80px;"> hours</td>`
                    : `<td>${Number(row.study_time).toFixed(1)} hours</td>`;

                const gradeTd = row.is_prediction
                    ? `<td><input type="number" class="prediction-input grade-input" data-id="${row.id}" value="${row.grade}" step="1" min="0" style="width: 80px;">%</td>`
                    : `<td>${row.grade != null ? row.grade + '%' : '-'}</td>`;

                const actionsTd = onDashboard ? '' : (row.is_prediction
                    ? `<td><button class="action-btn predict-btn">Predict</button><button class="action-btn add-prediction-btn">Add</button><button class="action-btn delete-btn">Delete</button></td>`
                    : `<td><button class="action-btn edit-btn">Edit</button><button class="action-btn delete-btn">Delete</button></td>`);

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
        } // Closing brace for the tbody-dependent code block

        // Convert server-rendered prediction categories to dropdowns on page load
        function convertPredictionCategoriesToDropdowns() {
            if (!assignmentTableBody) return;

            const predictionRows = assignmentTableBody.querySelectorAll('tr.prediction-row[data-id]');
            predictionRows.forEach(row => {
                const assignmentId = row.dataset.id;
                const categoryCell = row.querySelector('td:nth-child(3)');
                if (!categoryCell) return;

                // Check if already converted (has a dropdown)
                if (categoryCell.querySelector('.prediction-category-select')) return;

                // Extract current category from the text
                const categoryTag = categoryCell.querySelector('.category-tag');
                if (!categoryTag) return;

                const currentCategory = categoryTag.lastChild.textContent.trim();
                const subjectCell = row.querySelector('td:nth-child(2)');
                const subject = subjectCell ? subjectCell.textContent.trim() : '';

                if (subject && currentCategory) {
                    // Replace content with dropdown
                    categoryCell.classList.add('prediction-category-cell');
                    categoryCell.innerHTML = createCategoryDropdown(subject, currentCategory, assignmentId);
                }
            });
        }

        // Initialize prediction rows (dropdowns + mutual exclusivity)
        function initializePredictionRows() {
            convertPredictionCategoriesToDropdowns();

            if (!assignmentTableBody) return;
            const predictionRows = assignmentTableBody.querySelectorAll('tr.prediction-row');

            predictionRows.forEach(row => {
                const hoursInput = row.querySelector('.hours-input');
                const gradeInput = row.querySelector('.grade-input');

                if (hoursInput && gradeInput) {
                    // Remove existing listeners to avoid duplicates?
                    // It's hard to remove anonymous functions.
                    // But this runs once on load, so it should be fine.

                    hoursInput.addEventListener('input', function () {
                        if (this.value) {
                            gradeInput.value = '';
                        }
                    });

                    gradeInput.addEventListener('input', function () {
                        if (this.value) {
                            hoursInput.value = '';
                        }
                    });
                }
            });
        }

        // Run initialization
        initializePredictionRows();

    });

// ============================================
// TOAST NOTIFICATION SYSTEM
// ============================================
window.showToast = function(message, type = 'info', duration = 4000) {
    // Get or create toast container
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-message">${message}</span>`;
    
    // Add to container
    container.appendChild(toast);
    
    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });
    
    // Auto dismiss
    setTimeout(() => {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => toast.remove());
    }, duration);
    
    return toast;
};

// ============================================
// CONFIRMATION MODAL SYSTEM
// ============================================
window.showConfirmModal = function(options) {
    const {
        title = 'Confirm Action',
        message = 'Are you sure you want to proceed?',
        confirmText = 'Confirm',
        cancelText = 'Cancel',
        type = 'warning', // 'warning', 'danger', 'info'
        onConfirm = () => {},
        onCancel = () => {}
    } = options;
    
    // Create modal HTML
    const modalHTML = `
        <div class="modal-overlay" id="confirm-modal-overlay">
            <div class="modal-content">
                <div class="modal-icon ${type}">
                    ${type === 'danger' ? '⚠️' : type === 'warning' ? '⚡' : 'ℹ️'}
                </div>
                <h3>${title}</h3>
                <p>${message}</p>
                <div class="modal-buttons">
                    <button class="modal-btn modal-btn-cancel" id="modal-cancel-btn">${cancelText}</button>
                    <button class="modal-btn ${type === 'danger' ? 'modal-btn-confirm' : 'modal-btn-primary'}" id="modal-confirm-btn">${confirmText}</button>
                </div>
            </div>
        </div>
    `;
    
    // Add to DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    const overlay = document.getElementById('confirm-modal-overlay');
    const confirmBtn = document.getElementById('modal-confirm-btn');
    const cancelBtn = document.getElementById('modal-cancel-btn');
    
    // Show modal
    requestAnimationFrame(() => {
        overlay.classList.add('active');
    });
    
    // Handle confirm
    confirmBtn.addEventListener('click', () => {
        overlay.classList.remove('active');
        setTimeout(() => overlay.remove(), 300);
        onConfirm();
    });
    
    // Handle cancel
    cancelBtn.addEventListener('click', () => {
        overlay.classList.remove('active');
        setTimeout(() => overlay.remove(), 300);
        onCancel();
    });
    
    // Handle overlay click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.classList.remove('active');
            setTimeout(() => overlay.remove(), 300);
            onCancel();
        }
    });
    
    // Handle escape key
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            overlay.classList.remove('active');
            setTimeout(() => overlay.remove(), 300);
            onCancel();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
    
    return overlay;
};

// ============================================
// BUTTON LOADING STATE
// ============================================
window.setButtonLoading = function(button, loading = true) {
    if (loading) {
        button.classList.add('btn-loading');
        button.disabled = true;
        button.dataset.originalText = button.textContent;
    } else {
        button.classList.remove('btn-loading');
        button.disabled = false;
        if (button.dataset.originalText) {
            button.textContent = button.dataset.originalText;
        }
    }
};

// ============================================
// FORM VALIDATION HELPERS
// ============================================
window.validateInput = function(input, validator, errorMessage) {
    const isValid = validator(input.value);
    const validationIcon = input.parentElement.querySelector('.validation-icon');
    const validationMsg = input.parentElement.querySelector('.validation-message');
    
    if (isValid) {
        input.classList.remove('invalid');
        input.classList.add('valid');
        if (validationIcon) {
            validationIcon.classList.remove('invalid');
            validationIcon.classList.add('valid');
        }
    } else {
        input.classList.remove('valid');
        input.classList.add('invalid');
        if (validationIcon) {
            validationIcon.classList.remove('valid');
            validationIcon.classList.add('invalid');
        }
        if (validationMsg) {
            validationMsg.textContent = errorMessage;
        }
    }
    
    return isValid;
};
