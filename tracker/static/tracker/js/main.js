/**
 * AI Protein Intake Calculator & Diet Food Tracker
 * Client-Side Interactivity and Reactive Macro Calculations
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Native <dialog> Modal Controllers
    const logModal = document.getElementById('logMealModal');
    const openLogButtons = document.querySelectorAll('[data-open-modal="logMealModal"]');
    const closeModalButtons = document.querySelectorAll('[data-close-modal]');

    openLogButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const mealType = btn.getAttribute('data-meal-type');
            const foodId = btn.getAttribute('data-food-id');
            const foodName = btn.getAttribute('data-food-name');
            const servingG = btn.getAttribute('data-serving-g');

            if (logModal) {
                if (mealType) {
                    const mealSelect = logModal.querySelector('#modal_meal_type');
                    if (mealSelect) mealSelect.value = mealType;
                }
                if (foodId) {
                    const foodSelect = logModal.querySelector('#modal_food_select');
                    if (foodSelect) {
                        foodSelect.value = foodId;
                        foodSelect.dispatchEvent(new Event('change'));
                    }
                }
                if (servingG) {
                    const servingInput = logModal.querySelector('#modal_serving_g');
                    if (servingInput) {
                        servingInput.value = servingG;
                        servingInput.dispatchEvent(new Event('input'));
                    }
                }
                logModal.showModal();
            }
        });
    });

    closeModalButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('dialog');
            if (modal) modal.close();
        });
    });

    // Close dialog when clicking on backdrop
    if (logModal) {
        logModal.addEventListener('click', (e) => {
            const rect = logModal.getBoundingClientRect();
            const isInDialog = (
                rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
                rect.left <= e.clientX && e.clientX <= rect.left + rect.width
            );
            if (!isInDialog) {
                logModal.close();
            }
        });
    }

    // 2. Dynamic Serving Size Macro Recalculation in Modal
    const foodSelect = document.getElementById('modal_food_select');
    const servingInput = document.getElementById('modal_serving_g');
    const caloriesInput = document.getElementById('modal_calories');
    const proteinInput = document.getElementById('modal_protein');
    const carbsInput = document.getElementById('modal_carbs');
    const fatInput = document.getElementById('modal_fat');
    const foodNameInput = document.getElementById('modal_food_name');

    function updateCalculatedMacros() {
        if (!foodSelect) return;
        const selectedOption = foodSelect.options[foodSelect.selectedIndex];
        if (!selectedOption || !selectedOption.value) return;

        const cal100 = parseFloat(selectedOption.getAttribute('data-cals')) || 0;
        const p100 = parseFloat(selectedOption.getAttribute('data-protein')) || 0;
        const c100 = parseFloat(selectedOption.getAttribute('data-carbs')) || 0;
        const f100 = parseFloat(selectedOption.getAttribute('data-fat')) || 0;
        const servingG = parseFloat(servingInput.value) || 100;

        const factor = servingG / 100.0;
        if (caloriesInput) caloriesInput.value = (cal100 * factor).toFixed(1);
        if (proteinInput) proteinInput.value = (p100 * factor).toFixed(1);
        if (carbsInput) carbsInput.value = (c100 * factor).toFixed(1);
        if (fatInput) fatInput.value = (f100 * factor).toFixed(1);
        if (foodNameInput) foodNameInput.value = selectedOption.text.split('(')[0].trim();
    }

    if (foodSelect) {
        foodSelect.addEventListener('change', () => {
            const selectedOption = foodSelect.options[foodSelect.selectedIndex];
            const defaultServing = selectedOption.getAttribute('data-default-serving');
            if (defaultServing && servingInput) {
                servingInput.value = defaultServing;
            }
            updateCalculatedMacros();
        });
    }

    if (servingInput) {
        servingInput.addEventListener('input', updateCalculatedMacros);
    }

    // 3. AI Natural Language Quick Parse
    const quickLogBtn = document.getElementById('aiQuickLogBtn');
    const quickLogInput = document.getElementById('aiQuickLogInput');
    const quickLogStatus = document.getElementById('aiQuickLogStatus');

    if (quickLogBtn && quickLogInput) {
        quickLogBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const text = quickLogInput.value.trim();
            if (!text) return;

            if (quickLogStatus) {
                quickLogStatus.textContent = 'AI is analyzing your meal query...';
                quickLogStatus.style.display = 'block';
            }

            try {
                const response = await fetch(`/api/parse-food/?query=${encodeURIComponent(text)}`);
                const result = await response.json();

                if (result.success && result.data) {
                    const data = result.data;
                    if (logModal) {
                        if (foodSelect) foodSelect.value = data.food_id;
                        if (servingInput) servingInput.value = data.serving_g;
                        if (foodNameInput) foodNameInput.value = data.name;
                        if (caloriesInput) caloriesInput.value = data.calories;
                        if (proteinInput) proteinInput.value = data.protein_g;
                        if (carbsInput) carbsInput.value = data.carbs_g;
                        if (fatInput) fatInput.value = data.fat_g;

                        if (quickLogStatus) {
                            quickLogStatus.textContent = `Found: ${data.name} (${data.serving_g}g, ${data.protein_g}g Protein)`;
                        }
                        logModal.showModal();
                    }
                } else {
                    if (quickLogStatus) {
                        quickLogStatus.textContent = result.message || 'No direct match found in USDA database.';
                    }
                }
            } catch (err) {
                console.error('AI Parse error:', err);
                if (quickLogStatus) quickLogStatus.textContent = 'Error connecting to AI nutrition engine.';
            }
        });
    }
});
