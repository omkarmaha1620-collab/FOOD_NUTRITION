/**
 * Food Nutrition Analyzer - Client JavaScript
 * Handles dynamic live quantity calculation, instant search filtering,
 * modal data binding, and print reports.
 */

document.addEventListener('DOMContentLoaded', () => {

  // --------------------------------------------------------------------------
  // 1. LIVE NUTRITION CALCULATOR (Module 5)
  // Formula: Nutrient consumed = (Nutrient per 100g * quantity in grams) / 100
  // --------------------------------------------------------------------------
  const quantityInput = document.getElementById('calc-quantity-grams');
  if (quantityInput) {
    const calPer100 = parseFloat(quantityInput.dataset.calories || 0);
    const proPer100 = parseFloat(quantityInput.dataset.protein || 0);
    const carbPer100 = parseFloat(quantityInput.dataset.carbs || 0);
    const fatPer100 = parseFloat(quantityInput.dataset.fat || 0);
    const fiberPer100 = parseFloat(quantityInput.dataset.fiber || 0);

    const updateCalculations = () => {
      let grams = parseFloat(quantityInput.value);
      if (isNaN(grams) || grams < 0) grams = 0;

      const calcCal = ((calPer100 * grams) / 100).toFixed(1);
      const calcPro = ((proPer100 * grams) / 100).toFixed(1);
      const calcCarb = ((carbPer100 * grams) / 100).toFixed(1);
      const calcFat = ((fatPer100 * grams) / 100).toFixed(1);
      const calcFiber = ((fiberPer100 * grams) / 100).toFixed(1);

      // Update DOM targets
      const elCal = document.getElementById('calc-val-calories');
      const elPro = document.getElementById('calc-val-protein');
      const elCarb = document.getElementById('calc-val-carbs');
      const elFat = document.getElementById('calc-val-fat');
      const elFiber = document.getElementById('calc-val-fiber');
      const elGramsDisplay = document.getElementById('calc-val-grams-display');

      if (elCal) elCal.textContent = calcCal;
      if (elPro) elPro.textContent = calcPro;
      if (elCarb) elCarb.textContent = calcCarb;
      if (elFat) elFat.textContent = calcFat;
      if (elFiber) elFiber.textContent = calcFiber;
      if (elGramsDisplay) elGramsDisplay.textContent = grams;
    };

    quantityInput.addEventListener('input', updateCalculations);
    quantityInput.addEventListener('change', updateCalculations);
    // Initial run
    updateCalculations();
  }

  // --------------------------------------------------------------------------
  // 2. INSTANT CLIENT-SIDE SEARCH FILTER (Module 4)
  // --------------------------------------------------------------------------
  const liveSearchInput = document.getElementById('live-food-search');
  if (liveSearchInput) {
    liveSearchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      const foodCards = document.querySelectorAll('.food-search-item');
      let visibleCount = 0;

      foodCards.forEach(card => {
        const foodName = card.dataset.name ? card.dataset.name.toLowerCase() : '';
        const foodCat = card.dataset.category ? card.dataset.category.toLowerCase() : '';
        if (foodName.includes(query) || foodCat.includes(query)) {
          card.style.display = '';
          visibleCount++;
        } else {
          card.style.display = 'none';
        }
      });

      const noResultsEl = document.getElementById('no-search-results');
      if (noResultsEl) {
        noResultsEl.style.display = (visibleCount === 0) ? 'block' : 'none';
      }
    });
  }

  // --------------------------------------------------------------------------
  // 3. EDIT MEAL MODAL BINDING (Module 6)
  // --------------------------------------------------------------------------
  const editMealModal = document.getElementById('editMealModal');
  if (editMealModal) {
    editMealModal.addEventListener('show.bs.modal', (event) => {
      const button = event.relatedTarget;
      if (!button) return;

      const mealId = button.getAttribute('data-meal-id');
      const foodName = button.getAttribute('data-food-name');
      const quantity = button.getAttribute('data-quantity');
      const mealType = button.getAttribute('data-meal-type');

      const modalForm = editMealModal.querySelector('#editMealForm');
      const modalFoodName = editMealModal.querySelector('#editModalFoodName');
      const modalQuantity = editMealModal.querySelector('#editModalQuantity');
      const modalMealType = editMealModal.querySelector('#editModalMealType');

      if (modalForm) modalForm.action = `/meals/edit/${mealId}`;
      if (modalFoodName) modalFoodName.textContent = foodName;
      if (modalQuantity) modalQuantity.value = quantity;
      if (modalMealType) modalMealType.textContent = mealType;
    });
  }

  // --------------------------------------------------------------------------
  // 4. PRINT REPORT BUTTON (Module 11)
  // --------------------------------------------------------------------------
  const printReportBtn = document.getElementById('btn-print-report');
  if (printReportBtn) {
    printReportBtn.addEventListener('click', () => {
      window.print();
    });
  }

  // --------------------------------------------------------------------------
  // 5. AUTO-DISMISS FLASH ALERTS
  // --------------------------------------------------------------------------
  const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 6000);
  });
});
