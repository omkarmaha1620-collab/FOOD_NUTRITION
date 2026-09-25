"""
Nutrition and Health Metric Calculation Helper Module
Contains mathematical equations for:
1. Quantity-based nutrient scaling
2. Body Mass Index (BMI) & categorization
3. Basal Metabolic Rate (BMR) using Mifflin-St Jeor Equation
4. Total Daily Energy Expenditure (TDEE) / Calorie requirements
"""

def calculate_nutrient_consumed(nutrient_per_100g: float, quantity_grams: float) -> float:
    """
    Module 5: Quantity-based nutrition formula
    Formula: (Nutrient per 100g * quantity in grams) / 100
    """
    if quantity_grams <= 0 or nutrient_per_100g <= 0:
        return 0.0
    return round((float(nutrient_per_100g) * float(quantity_grams)) / 100.0, 1)

def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    """
    Module 8: Body Mass Index (BMI)
    Formula: BMI = weight (kg) / [height (m)]^2
    """
    if height_cm <= 0 or weight_kg <= 0:
        return {
            'bmi': 0.0,
            'category': 'Unknown',
            'color': 'secondary',
            'advice': 'Please enter valid physical measurements.'
        }
    
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m * height_m), 1)

    if bmi < 18.5:
        category = 'Underweight'
        color = 'warning'
        advice = 'Your BMI indicates you may be underweight. Consider nutrient-dense wholesome meals.'
    elif 18.5 <= bmi <= 24.9:
        category = 'Normal weight'
        color = 'success'
        advice = 'Your BMI is within the healthy reference range. Maintain balanced nutrition and activity.'
    elif 25.0 <= bmi <= 29.9:
        category = 'Overweight'
        color = 'warning'
        advice = 'Your BMI indicates you may be overweight. Regular physical activity and mindful portions are advised.'
    else:
        category = 'Obesity'
        color = 'danger'
        advice = 'Your BMI falls into the obesity category. Consult a certified nutritionist or healthcare provider.'

    return {
        'bmi': bmi,
        'category': category,
        'color': color,
        'advice': advice,
        'disclaimer': 'Note: BMI is a general screening indicator and does not replace medical consultation.'
    }

def calculate_calorie_requirement(weight_kg: float, height_cm: float, age: int, gender: str, activity_level: str) -> dict:
    """
    Module 9: Daily Calorie Requirement
    Calculates BMR using the Mifflin-St Jeor Equation and multiplies by Activity Factor.
    """
    if weight_kg <= 0 or height_cm <= 0 or age <= 0:
        return {
            'bmr': 0,
            'tdee': 2000,
            'activity_level': activity_level,
            'multiplier': 1.2
        }

    # 1. Mifflin-St Jeor Equation for BMR (Basal Metabolic Rate)
    # Men:   BMR = 10 * weight(kg) + 6.25 * height(cm) - 5 * age + 5
    # Women: BMR = 10 * weight(kg) + 6.25 * height(cm) - 5 * age - 161
    gender_lower = (gender or 'male').strip().lower()
    base_calc = (10.0 * float(weight_kg)) + (6.25 * float(height_cm)) - (5.0 * float(age))
    
    if gender_lower == 'female':
        bmr = base_calc - 161.0
    elif gender_lower == 'male':
        bmr = base_calc + 5.0
    else:
        # Default or Non-binary midpoint
        bmr = base_calc - 78.0

    bmr = round(max(bmr, 800.0), 1)

    # 2. Activity Multiplier
    multipliers = {
        'Sedentary': 1.2,          # Desk job, little to no exercise
        'Lightly Active': 1.375,   # Light workouts 1-3 days per week
        'Moderately Active': 1.55, # Moderate workouts 3-5 days per week
        'Very Active': 1.725,      # Heavy workouts 6-7 days per week
        'Extra Active': 1.9        # Very heavy workout or physical job
    }
    multiplier = multipliers.get(activity_level, 1.375)

    # 3. Estimated Daily Calorie Requirement (TDEE)
    tdee = int(round(bmr * multiplier))

    # Standard healthy macronutrient distribution recommendation based on TDEE:
    # Protein: ~20% of calories (4 kcal/g)
    # Carbs:   ~50% of calories (4 kcal/g)
    # Fat:     ~30% of calories (9 kcal/g)
    rec_protein_g = round((tdee * 0.20) / 4.0, 1)
    rec_carbs_g = round((tdee * 0.50) / 4.0, 1)
    rec_fat_g = round((tdee * 0.30) / 9.0, 1)
    rec_fiber_g = 28.0 # Recommended daily fiber intake in grams

    return {
        'bmr': bmr,
        'activity_level': activity_level,
        'multiplier': multiplier,
        'tdee': tdee,
        'recommended_macros': {
            'protein_g': rec_protein_g,
            'carbs_g': rec_carbs_g,
            'fat_g': rec_fat_g,
            'fiber_g': rec_fiber_g
        },
        'disclaimer': 'Estimated calorie requirement based on Mifflin-St Jeor formula. For informational use only.'
    }
