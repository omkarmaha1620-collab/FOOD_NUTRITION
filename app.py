"""
Food Nutrition Analyzer - Main Flask Application
College Mini Project Web Application
"""

import os
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from db import execute_query, execute_insert, execute_update
from nutrition_calc import calculate_nutrient_consumed, calculate_bmi, calculate_calorie_requirement

app = Flask(__name__)
app.config.from_object(Config)

# -----------------------------------------------------------------------------
# AUTHENTICATION DECORATORS & HELPERS
# -----------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session or not session.get('is_admin'):
            flash('Administrator authentication required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_current_year_and_user():
    """Make current year and session user details globally available in all templates"""
    return {
        'current_year': datetime.now().year,
        'today_date': date.today().isoformat(),
        'session_user_name': session.get('user_name'),
        'is_logged_in': 'user_id' in session,
        'is_admin_logged_in': 'admin_id' in session
    }

def calculate_progress_metric(consumed, recommended):
    """
    Calculate dynamic percentage and visual bar fill width with safety caps.
    Used for dashboard calorie and macronutrient progress indicators.
    """
    consumed_val = float(consumed or 0.0)
    recommended_val = float(recommended or 0.0)

    if recommended_val <= 0.0 or consumed_val <= 0.0:
        return {
            'consumed': max(0.0, consumed_val),
            'recommended': max(0.0, recommended_val),
            'percentage': 0.0,
            'fill_width': 0.0,
            'display_pct': 0
        }

    raw_pct = (consumed_val / recommended_val) * 100.0

    if raw_pct < 1.0:
        display_pct = round(raw_pct, 2)
    else:
        display_pct = round(raw_pct, 1)

    fill_width = round(max(0.0, min(100.0, raw_pct)), 2)

    return {
        'consumed': consumed_val,
        'recommended': recommended_val,
        'percentage': round(raw_pct, 1),
        'fill_width': fill_width,
        'display_pct': display_pct
    }

# -----------------------------------------------------------------------------
# PUBLIC ROUTES
# -----------------------------------------------------------------------------

@app.route('/')
def index():
    """Home landing page with system overview and features"""
    try:
        sample_foods = execute_query(
            "SELECT name, category, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g FROM food_items LIMIT 6"
        )
    except Exception:
        sample_foods = []
    return render_template('index.html', sample_foods=sample_foods)

# -----------------------------------------------------------------------------
# MODULE 1: USER REGISTRATION & LOGIN
# -----------------------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with input validation and password hashing"""
    if request.method == 'GET' and 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', 'Male')
        height_cm = request.form.get('height_cm', '').strip()
        weight_kg = request.form.get('weight_kg', '').strip()
        activity_level = request.form.get('activity_level', 'Moderately Active')

        # Form Validation
        errors = []
        if not name or len(name) < 2:
            errors.append('Please provide a valid full name (at least 2 characters).')
        if not email or '@' not in email or '.' not in email:
            errors.append('Please provide a valid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        try:
            age_int = int(age)
            if age_int < 10 or age_int > 120:
                errors.append('Age must be between 10 and 120 years.')
        except ValueError:
            errors.append('Please enter a valid number for age.')

        try:
            height_flt = float(height_cm)
            if height_flt < 50 or height_flt > 250:
                errors.append('Height must be between 50 cm and 250 cm.')
        except ValueError:
            errors.append('Please enter a valid number for height (cm).')

        try:
            weight_flt = float(weight_kg)
            if weight_flt < 20 or weight_flt > 300:
                errors.append('Weight must be between 20 kg and 300 kg.')
        except ValueError:
            errors.append('Please enter a valid number for weight (kg).')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html', form_data=request.form)

        # Check if email is already registered
        try:
            existing_user = execute_query(
                "SELECT id FROM users WHERE email = %s",
                (email,),
                fetch_one=True
            )
            if existing_user:
                flash('An account with this email already exists. Please log in.', 'warning')
                return render_template('register.html', form_data=request.form)

            # Hash password securely
            password_hash = generate_password_hash(password)

            # Insert into database
            user_id = execute_insert(
                """INSERT INTO users (name, email, password_hash, age, gender, height_cm, weight_kg, activity_level)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (name, email, password_hash, age_int, gender, height_flt, weight_flt, activity_level)
            )

            session.clear()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f'Database error during registration: {str(e)}', 'danger')
            return render_template('register.html', form_data=request.form)

    return render_template('register.html', form_data={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Session-based authentication with password verification"""
    if request.method == 'GET' and 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('login.html')

        try:
            user = execute_query(
                "SELECT id, name, email, password_hash FROM users WHERE email = %s",
                (email,),
                fetch_one=True
            )

            if user and check_password_hash(user['password_hash'], password):
                # Set session variables
                session.clear()
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                flash(f"Welcome back, {user['name']}!", 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Invalid email or password. Please try again.', 'danger')

        except Exception as e:
            flash(f'Database error during login: {str(e)}', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Clear session data and log out"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# -----------------------------------------------------------------------------
# MODULE 2: USER PROFILE & HEALTH METRICS (MODULE 8 & MODULE 9)
# -----------------------------------------------------------------------------

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management, BMI calculation, and daily calorie target"""
    user_id = session['user_id']

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', 'Male')
        height_cm = request.form.get('height_cm', '').strip()
        weight_kg = request.form.get('weight_kg', '').strip()
        activity_level = request.form.get('activity_level', 'Moderately Active')

        errors = []
        if not name:
            errors.append('Name cannot be empty.')
        try:
            age_int = int(age)
            if age_int < 10 or age_int > 120:
                errors.append('Age must be between 10 and 120.')
        except ValueError:
            errors.append('Invalid age.')
        try:
            height_flt = float(height_cm)
            if height_flt < 50 or height_flt > 250:
                errors.append('Height must be between 50 and 250 cm.')
        except ValueError:
            errors.append('Invalid height.')
        try:
            weight_flt = float(weight_kg)
            if weight_flt < 20 or weight_flt > 300:
                errors.append('Weight must be between 20 and 300 kg.')
        except ValueError:
            errors.append('Invalid weight.')

        if errors:
            for err in errors:
                flash(err, 'danger')
        else:
            try:
                execute_update(
                    """UPDATE users
                       SET name = %s, age = %s, gender = %s, height_cm = %s, weight_kg = %s, activity_level = %s
                       WHERE id = %s""",
                    (name, age_int, gender, height_flt, weight_flt, activity_level, user_id)
                )
                session['user_name'] = name
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile'))
            except Exception as e:
                flash(f'Error updating profile: {str(e)}', 'danger')

    # Fetch user data
    user = execute_query(
        "SELECT id, name, email, age, gender, height_cm, weight_kg, activity_level, created_at FROM users WHERE id = %s",
        (user_id,),
        fetch_one=True
    )

    if not user:
        flash('User profile not found.', 'danger')
        return redirect(url_for('logout'))

    # Calculate BMI (Module 8)
    bmi_info = calculate_bmi(user['weight_kg'], user['height_cm'])

    # Calculate Daily Calorie Requirement (Module 9)
    calorie_info = calculate_calorie_requirement(
        user['weight_kg'],
        user['height_cm'],
        user['age'],
        user['gender'],
        user['activity_level']
    )

    return render_template('profile.html', user=user, bmi=bmi_info, calories=calorie_info)

# -----------------------------------------------------------------------------
# MODULE 10: NUTRITION DASHBOARD
# -----------------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard displaying calorie target vs consumed, macros, and meal logs"""
    user_id = session['user_id']
    selected_date = request.args.get('date', date.today().isoformat())

    # Get user profile metrics
    user = execute_query(
        "SELECT id, name, age, gender, height_cm, weight_kg, activity_level FROM users WHERE id = %s",
        (user_id,),
        fetch_one=True
    )

    if not user:
        flash('User profile not found. Please log in again.', 'warning')
        return redirect(url_for('logout'))

    bmi_info = calculate_bmi(user['weight_kg'], user['height_cm'])
    calorie_info = calculate_calorie_requirement(
        user['weight_kg'],
        user['height_cm'],
        user['age'],
        user['gender'],
        user['activity_level']
    )

    # Fetch today's meal entries
    meals = execute_query(
        """SELECT m.id, m.food_id, m.meal_type, m.quantity_grams, m.calories, m.protein, m.carbs, m.fat, m.fiber, m.entry_date,
                  f.name as food_name, f.category
           FROM meal_entries m
           JOIN food_items f ON m.food_id = f.id
           WHERE m.user_id = %s AND m.entry_date = %s
           ORDER BY m.id ASC""",
        (user_id, selected_date)
    )

    # Group meals by category and compute totals
    meal_groups = {
        'Breakfast': {'items': [], 'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'fiber': 0.0},
        'Lunch':     {'items': [], 'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'fiber': 0.0},
        'Dinner':    {'items': [], 'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'fiber': 0.0},
        'Snacks':    {'items': [], 'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'fiber': 0.0}
    }

    daily_totals = {
        'calories': 0.0,
        'protein': 0.0,
        'carbs': 0.0,
        'fat': 0.0,
        'fiber': 0.0
    }

    for item in meals:
        mtype = item['meal_type']
        if mtype in meal_groups:
            meal_groups[mtype]['items'].append(item)
            meal_groups[mtype]['calories'] += item['calories']
            meal_groups[mtype]['protein'] += item['protein']
            meal_groups[mtype]['carbs'] += item['carbs']
            meal_groups[mtype]['fat'] += item['fat']
            meal_groups[mtype]['fiber'] += item['fiber']

        daily_totals['calories'] += item['calories']
        daily_totals['protein'] += item['protein']
        daily_totals['carbs'] += item['carbs']
        daily_totals['fat'] += item['fat']
        daily_totals['fiber'] += item['fiber']

    # Round totals
    for k in daily_totals:
        daily_totals[k] = round(daily_totals[k], 1)
    for mtype in meal_groups:
        for k in ['calories', 'protein', 'carbs', 'fat', 'fiber']:
            meal_groups[mtype][k] = round(meal_groups[mtype][k], 1)

    target_calories = calorie_info['tdee']
    consumed_calories = daily_totals['calories']
    remaining_calories = max(0.0, round(target_calories - consumed_calories, 1))

    calorie_progress = calculate_progress_metric(consumed_calories, target_calories)
    calorie_percentage = calorie_progress['display_pct']

    rec_macros = calorie_info.get('recommended_macros', {})
    macro_progress = {
        'protein': calculate_progress_metric(daily_totals['protein'], rec_macros.get('protein_g', 0.0)),
        'carbs': calculate_progress_metric(daily_totals['carbs'], rec_macros.get('carbs_g', 0.0)),
        'fat': calculate_progress_metric(daily_totals['fat'], rec_macros.get('fat_g', 0.0)),
        'fiber': calculate_progress_metric(daily_totals['fiber'], rec_macros.get('fiber_g', 0.0)),
    }

    return render_template(
        'dashboard.html',
        user=user,
        bmi=bmi_info,
        calorie_info=calorie_info,
        daily_totals=daily_totals,
        remaining_calories=remaining_calories,
        calorie_percentage=calorie_percentage,
        calorie_progress=calorie_progress,
        macro_progress=macro_progress,
        meal_groups=meal_groups,
        selected_date=selected_date
    )

# -----------------------------------------------------------------------------
# MODULE 4: FOOD SEARCH & MODULE 5: NUTRITION CALCULATION
# -----------------------------------------------------------------------------

@app.route('/foods')
@login_required
def food_search():
    """Search and browse food database with category filters"""
    query = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()

    sql = "SELECT * FROM food_items WHERE 1=1"
    params = []

    if query:
        sql += " AND name LIKE %s"
        params.append(f"%{query}%")

    if category and category != 'All':
        sql += " AND category = %s"
        params.append(category)

    sql += " ORDER BY category ASC, name ASC"

    foods = execute_query(sql, params)

    categories = [
        'All', 'Fruits', 'Vegetables', 'Grains', 'Pulses',
        'Dairy', 'Eggs', 'Meat', 'Snacks', 'Beverages'
    ]

    return render_template(
        'food_search.html',
        foods=foods,
        search_query=query,
        selected_category=category or 'All',
        categories=categories
    )

@app.route('/foods/<int:food_id>')
@login_required
def food_details(food_id):
    """View details of a specific food item with interactive quantity calculator"""
    food = execute_query(
        "SELECT * FROM food_items WHERE id = %s",
        (food_id,),
        fetch_one=True
    )
    if not food:
        flash('Food item not found.', 'danger')
        return redirect(url_for('food_search'))

    return render_template('food_details.html', food=food)

@app.route('/api/calculate-nutrition', methods=['POST'])
@login_required
def api_calculate_nutrition():
    """
    JSON API for Module 5: Quantity-based nutrition calculation
    Formula: Nutrient consumed = (Nutrient per 100g * quantity in grams) / 100
    """
    data = request.get_json() or {}
    try:
        food_id = int(data.get('food_id', 0))
        quantity_grams = float(data.get('quantity_grams', 100))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid input values.'}), 400

    if quantity_grams <= 0:
        return jsonify({'success': False, 'message': 'Quantity must be greater than zero.'}), 400

    food = execute_query(
        "SELECT * FROM food_items WHERE id = %s",
        (food_id,),
        fetch_one=True
    )
    if not food:
        return jsonify({'success': False, 'message': 'Food item not found.'}), 404

    calculated = {
        'food_id': food['id'],
        'food_name': food['name'],
        'quantity_grams': quantity_grams,
        'calories': calculate_nutrient_consumed(food['calories_per_100g'], quantity_grams),
        'protein': calculate_nutrient_consumed(food['protein_per_100g'], quantity_grams),
        'carbs': calculate_nutrient_consumed(food['carbs_per_100g'], quantity_grams),
        'fat': calculate_nutrient_consumed(food['fat_per_100g'], quantity_grams),
        'fiber': calculate_nutrient_consumed(food['fiber_per_100g'], quantity_grams)
    }

    return jsonify({'success': True, 'data': calculated})

# -----------------------------------------------------------------------------
# MODULE 6: MEAL MANAGEMENT & MODULE 7: DAILY TRACKING
# -----------------------------------------------------------------------------

@app.route('/meals/add', methods=['GET', 'POST'])
@login_required
def add_meal():
    """Add a food item to user's daily meal log with calculated nutritional values"""
    if request.method == 'POST':
        user_id = session['user_id']
        food_id = request.form.get('food_id')
        meal_type = request.form.get('meal_type', 'Breakfast')
        quantity_grams = request.form.get('quantity_grams', '100')
        entry_date = request.form.get('entry_date') or date.today().isoformat()

        errors = []
        try:
            food_id_int = int(food_id)
        except (ValueError, TypeError):
            errors.append('Invalid food selection.')

        try:
            quantity_flt = float(quantity_grams)
            if quantity_flt <= 0:
                errors.append('Quantity must be greater than 0 grams.')
            elif quantity_flt > 5000:
                errors.append('Quantity is unrealistically high (max 5000g).')
        except (ValueError, TypeError):
            errors.append('Please enter a valid number for quantity.')

        if meal_type not in ['Breakfast', 'Lunch', 'Dinner', 'Snacks']:
            errors.append('Invalid meal type selected.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return redirect(request.referrer or url_for('food_search'))

        # Fetch food details to calculate nutrition
        food = execute_query("SELECT * FROM food_items WHERE id = %s", (food_id_int,), fetch_one=True)
        if not food:
            flash('Food item not found in database.', 'danger')
            return redirect(url_for('food_search'))

        # Calculate nutrition according to quantity
        calories = calculate_nutrient_consumed(food['calories_per_100g'], quantity_flt)
        protein = calculate_nutrient_consumed(food['protein_per_100g'], quantity_flt)
        carbs = calculate_nutrient_consumed(food['carbs_per_100g'], quantity_flt)
        fat = calculate_nutrient_consumed(food['fat_per_100g'], quantity_flt)
        fiber = calculate_nutrient_consumed(food['fiber_per_100g'], quantity_flt)

        try:
            execute_insert(
                """INSERT INTO meal_entries (user_id, food_id, meal_type, quantity_grams, calories, protein, carbs, fat, fiber, entry_date)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, food_id_int, meal_type, quantity_flt, calories, protein, carbs, fat, fiber, entry_date)
            )
            flash(f"Added {quantity_flt}g of {food['name']} to {meal_type} successfully!", 'success')
            return redirect(url_for('tracking', date=entry_date))

        except Exception as e:
            flash(f'Error adding meal: {str(e)}', 'danger')
            return redirect(url_for('food_search'))

    # GET request - Show add meal form
    foods = execute_query("SELECT id, name, category, calories_per_100g FROM food_items ORDER BY name ASC")
    preselected_food_id = request.args.get('food_id', type=int)
    return render_template('meals.html', foods=foods, preselected_food_id=preselected_food_id)

@app.route('/meals/edit/<int:meal_id>', methods=['POST'])
@login_required
def edit_meal(meal_id):
    """Edit quantity of an existing meal entry and recalculate nutrients"""
    user_id = session['user_id']
    quantity_grams = request.form.get('quantity_grams', '').strip()
    return_date = request.form.get('return_date') or date.today().isoformat()

    try:
        quantity_flt = float(quantity_grams)
        if quantity_flt <= 0:
            flash('Quantity must be greater than zero.', 'danger')
            return redirect(url_for('tracking', date=return_date))
    except ValueError:
        flash('Invalid quantity entered.', 'danger')
        return redirect(url_for('tracking', date=return_date))

    # Verify meal belongs to user
    meal = execute_query(
        """SELECT m.id, m.food_id, f.calories_per_100g, f.protein_per_100g, f.carbs_per_100g, f.fat_per_100g, f.fiber_per_100g
           FROM meal_entries m
           JOIN food_items f ON m.food_id = f.id
           WHERE m.id = %s AND m.user_id = %s""",
        (meal_id, user_id),
        fetch_one=True
    )

    if not meal:
        flash('Meal entry not found or unauthorized.', 'danger')
        return redirect(url_for('tracking', date=return_date))

    # Recalculate
    calories = calculate_nutrient_consumed(meal['calories_per_100g'], quantity_flt)
    protein = calculate_nutrient_consumed(meal['protein_per_100g'], quantity_flt)
    carbs = calculate_nutrient_consumed(meal['carbs_per_100g'], quantity_flt)
    fat = calculate_nutrient_consumed(meal['fat_per_100g'], quantity_flt)
    fiber = calculate_nutrient_consumed(meal['fiber_per_100g'], quantity_flt)

    execute_update(
        """UPDATE meal_entries
           SET quantity_grams = %s, calories = %s, protein = %s, carbs = %s, fat = %s, fiber = %s
           WHERE id = %s AND user_id = %s""",
        (quantity_flt, calories, protein, carbs, fat, fiber, meal_id, user_id)
    )

    flash('Meal quantity and nutrition updated successfully!', 'success')
    return redirect(url_for('tracking', date=return_date))

@app.route('/meals/delete/<int:meal_id>', methods=['POST'])
@login_required
def delete_meal(meal_id):
    """Delete a meal entry"""
    user_id = session['user_id']
    return_date = request.form.get('return_date') or date.today().isoformat()

    affected = execute_update(
        "DELETE FROM meal_entries WHERE id = %s AND user_id = %s",
        (meal_id, user_id)
    )
    if affected > 0:
        flash('Meal entry removed.', 'info')
    else:
        flash('Unable to delete meal entry.', 'danger')

    return redirect(url_for('tracking', date=return_date))

@app.route('/tracking')
@login_required
def tracking():
    """
    Daily Nutrition Tracking page (Module 7)
    Displays meals grouped by Breakfast, Lunch, Dinner, Snacks for selected date
    """
    user_id = session['user_id']
    selected_date_str = request.args.get('date', date.today().isoformat())

    try:
        current_date_obj = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        current_date_obj = date.today()
        selected_date_str = current_date_obj.isoformat()

    prev_date_str = (current_date_obj - timedelta(days=1)).isoformat()
    next_date_str = (current_date_obj + timedelta(days=1)).isoformat()

    # User calorie target
    user = execute_query(
        "SELECT weight_kg, height_cm, age, gender, activity_level FROM users WHERE id = %s",
        (user_id,),
        fetch_one=True
    )
    if not user:
        flash('User profile not found. Please log in again.', 'warning')
        return redirect(url_for('logout'))

    calorie_info = calculate_calorie_requirement(
        user['weight_kg'], user['height_cm'], user['age'], user['gender'], user['activity_level']
    )

    # Fetch meals for this day
    meals = execute_query(
        """SELECT m.id, m.food_id, m.meal_type, m.quantity_grams, m.calories, m.protein, m.carbs, m.fat, m.fiber,
                  f.name as food_name, f.category, f.calories_per_100g, f.protein_per_100g, f.carbs_per_100g, f.fat_per_100g, f.fiber_per_100g
           FROM meal_entries m
           JOIN food_items f ON m.food_id = f.id
           WHERE m.user_id = %s AND m.entry_date = %s
           ORDER BY m.id ASC""",
        (user_id, selected_date_str)
    )

    # Group by meal type
    meal_groups = {
        'Breakfast': {'items': [], 'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'fiber': 0.0},
        'Lunch':     {'items': [], 'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'fiber': 0.0},
        'Dinner':    {'items': [], 'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'fiber': 0.0},
        'Snacks':    {'items': [], 'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'fiber': 0.0}
    }

    daily_totals = {
        'calories': 0.0,
        'protein': 0.0,
        'carbs': 0.0,
        'fat': 0.0,
        'fiber': 0.0,
        'count': len(meals)
    }

    for item in meals:
        mtype = item['meal_type']
        if mtype in meal_groups:
            meal_groups[mtype]['items'].append(item)
            meal_groups[mtype]['calories'] += item['calories']
            meal_groups[mtype]['protein'] += item['protein']
            meal_groups[mtype]['carbs'] += item['carbs']
            meal_groups[mtype]['fat'] += item['fat']
            meal_groups[mtype]['fiber'] += item['fiber']

        daily_totals['calories'] += item['calories']
        daily_totals['protein'] += item['protein']
        daily_totals['carbs'] += item['carbs']
        daily_totals['fat'] += item['fat']
        daily_totals['fiber'] += item['fiber']

    for k in ['calories', 'protein', 'carbs', 'fat', 'fiber']:
        daily_totals[k] = round(daily_totals[k], 1)
    for mtype in meal_groups:
        for k in ['calories', 'protein', 'carbs', 'fat', 'fiber']:
            meal_groups[mtype][k] = round(meal_groups[mtype][k], 1)

    target_calories = calorie_info['tdee']
    remaining_calories = max(0, round(target_calories - daily_totals['calories'], 1))

    return render_template(
        'tracking.html',
        selected_date=selected_date_str,
        prev_date=prev_date_str,
        next_date=next_date_str,
        meal_groups=meal_groups,
        daily_totals=daily_totals,
        target_calories=target_calories,
        remaining_calories=remaining_calories,
        is_today=(selected_date_str == date.today().isoformat())
    )

# -----------------------------------------------------------------------------
# MODULE 11: NUTRITION REPORTS & VISUALIZATION
# -----------------------------------------------------------------------------

@app.route('/reports')
@login_required
def reports():
    """
    Nutrition Report page with Chart.js charts and printable summary
    Options: Today, Specific Date, or Weekly Summary (Last 7 Days)
    """
    user_id = session['user_id']
    view_type = request.args.get('view', 'weekly')  # 'today', 'custom', 'weekly'
    selected_date_str = request.args.get('date', date.today().isoformat())

    # User profile for target comparison
    user = execute_query(
        "SELECT name, age, gender, height_cm, weight_kg, activity_level FROM users WHERE id = %s",
        (user_id,),
        fetch_one=True
    )
    if not user:
        flash('User profile not found. Please log in again.', 'warning')
        return redirect(url_for('logout'))

    calorie_info = calculate_calorie_requirement(
        user['weight_kg'], user['height_cm'], user['age'], user['gender'], user['activity_level']
    )
    bmi_info = calculate_bmi(user['weight_kg'], user['height_cm'])

    labels = []
    calories_trend = []
    protein_trend = []
    carbs_trend = []
    fat_trend = []

    report_items = []
    summary_totals = {
        'calories': 0.0,
        'protein': 0.0,
        'carbs': 0.0,
        'fat': 0.0,
        'fiber': 0.0,
        'meal_count': 0,
        'days_count': 1
    }

    if view_type == 'today':
        start_date = date.today().isoformat()
        end_date = start_date
        report_title = f"Today's Nutrition Report ({start_date})"
    elif view_type == 'custom':
        start_date = selected_date_str
        end_date = selected_date_str
        report_title = f"Nutrition Report for {selected_date_str}"
    else:  # weekly (last 7 days)
        view_type = 'weekly'
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=6)).isoformat()
        report_title = f"Weekly Nutrition Summary ({start_date} to {end_date})"
        summary_totals['days_count'] = 7

    # Fetch meals in range
    meals = execute_query(
        """SELECT m.id, m.meal_type, m.quantity_grams, m.calories, m.protein, m.carbs, m.fat, m.fiber, m.entry_date,
                  f.name as food_name, f.category
           FROM meal_entries m
           JOIN food_items f ON m.food_id = f.id
           WHERE m.user_id = %s AND m.entry_date BETWEEN %s AND %s
           ORDER BY m.entry_date DESC, m.id DESC""",
        (user_id, start_date, end_date)
    )
    report_items = meals

    for item in meals:
        summary_totals['calories'] += item['calories']
        summary_totals['protein'] += item['protein']
        summary_totals['carbs'] += item['carbs']
        summary_totals['fat'] += item['fat']
        summary_totals['fiber'] += item['fiber']
        summary_totals['meal_count'] += 1

    for k in ['calories', 'protein', 'carbs', 'fat', 'fiber']:
        summary_totals[k] = round(summary_totals[k], 1)

    avg_daily_calories = round(summary_totals['calories'] / summary_totals['days_count'], 1)

    # Build trend data for charts
    if view_type == 'weekly':
        # Generate all 7 days even if empty
        cur = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        date_map = {}
        while cur <= end:
            d_str = cur.isoformat()
            date_map[d_str] = {'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0}
            cur += timedelta(days=1)

        for item in meals:
            d_str = str(item['entry_date'])
            if d_str in date_map:
                date_map[d_str]['calories'] += item['calories']
                date_map[d_str]['protein'] += item['protein']
                date_map[d_str]['carbs'] += item['carbs']
                date_map[d_str]['fat'] += item['fat']

        for d_str, vals in sorted(date_map.items()):
            # Format label as 'Mon DD'
            d_obj = datetime.strptime(d_str, '%Y-%m-%d')
            labels.append(d_obj.strftime('%a, %b %d'))
            calories_trend.append(round(vals['calories'], 1))
            protein_trend.append(round(vals['protein'], 1))
            carbs_trend.append(round(vals['carbs'], 1))
            fat_trend.append(round(vals['fat'], 1))
    else:
        # Single day breakdown by meal types
        m_types = ['Breakfast', 'Lunch', 'Dinner', 'Snacks']
        m_calories = {m: 0.0 for m in m_types}
        for item in meals:
            m = item['meal_type']
            if m in m_calories:
                m_calories[m] += item['calories']
        labels = m_types
        calories_trend = [round(m_calories[m], 1) for m in m_types]

    return render_template(
        'reports.html',
        report_title=report_title,
        view_type=view_type,
        selected_date=selected_date_str,
        start_date=start_date,
        end_date=end_date,
        summary_totals=summary_totals,
        avg_daily_calories=avg_daily_calories,
        target_calories=calorie_info['tdee'],
        user=user,
        bmi=bmi_info,
        calorie_info=calorie_info,
        report_items=report_items,
        chart_labels=labels,
        calories_trend=calories_trend,
        macro_pie_data=[summary_totals['protein'], summary_totals['carbs'], summary_totals['fat']]
    )

# -----------------------------------------------------------------------------
# MODULE 12: ADMIN PANEL
# -----------------------------------------------------------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Separate login portal for administrators"""
    if request.method == 'GET' and 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()  # email or username
        password = request.form.get('password', '')

        if not identifier or not password:
            flash('Please enter your admin credentials.', 'warning')
            return render_template('admin_login.html')

        try:
            admin = execute_query(
                "SELECT id, username, email, password_hash, full_name FROM admins WHERE email = %s OR username = %s",
                (identifier, identifier),
                fetch_one=True
            )

            if admin and check_password_hash(admin['password_hash'], password):
                session.clear()
                session['admin_id'] = admin['id']
                session['admin_username'] = admin['username']
                session['admin_name'] = admin['full_name']
                session['is_admin'] = True
                flash(f"Welcome, Administrator {admin['full_name']}!", 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid administrator credentials.', 'danger')

        except Exception as e:
            flash(f'Database error during admin login: {str(e)}', 'danger')

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.clear()
    flash('Admin logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin overview with system metrics and registered users"""
    try:
        user_count = execute_query("SELECT COUNT(*) as count FROM users", fetch_one=True)['count']
        food_count = execute_query("SELECT COUNT(*) as count FROM food_items", fetch_one=True)['count']
        meal_count = execute_query("SELECT COUNT(*) as count FROM meal_entries", fetch_one=True)['count']

        recent_users = execute_query(
            """SELECT u.id, u.name, u.email, u.age, u.gender, u.activity_level, u.created_at,
                      COUNT(m.id) as total_meals
               FROM users u
               LEFT JOIN meal_entries m ON u.id = m.user_id
               GROUP BY u.id
               ORDER BY u.created_at DESC
               LIMIT 10"""
        )

        category_counts = execute_query(
            "SELECT category, COUNT(*) as count FROM food_items GROUP BY category ORDER BY count DESC"
        )

    except Exception as e:
        flash(f"Error loading dashboard metrics: {str(e)}", 'danger')
        user_count = food_count = meal_count = 0
        recent_users = []
        category_counts = []

    return render_template(
        'admin_dashboard.html',
        user_count=user_count,
        food_count=food_count,
        meal_count=meal_count,
        recent_users=recent_users,
        category_counts=category_counts
    )

@app.route('/admin/foods')
@admin_required
def admin_foods():
    """Admin Food Items management table with search and filtering"""
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()

    sql = "SELECT * FROM food_items WHERE 1=1"
    params = []

    if search:
        sql += " AND name LIKE %s"
        params.append(f"%{search}%")
    if category and category != 'All':
        sql += " AND category = %s"
        params.append(category)

    sql += " ORDER BY id DESC"
    foods = execute_query(sql, params)

    categories = ['All', 'Fruits', 'Vegetables', 'Grains', 'Pulses', 'Dairy', 'Eggs', 'Meat', 'Snacks', 'Beverages']

    return render_template(
        'manage_food.html',
        foods=foods,
        search=search,
        selected_category=category or 'All',
        categories=categories
    )

@app.route('/admin/foods/add', methods=['POST'])
@admin_required
def admin_add_food():
    """Add a new food item into the food database"""
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    serving_size = request.form.get('serving_size', '100g').strip()
    calories = request.form.get('calories_per_100g', '').strip()
    protein = request.form.get('protein_per_100g', '').strip()
    carbs = request.form.get('carbs_per_100g', '').strip()
    fat = request.form.get('fat_per_100g', '').strip()
    fiber = request.form.get('fiber_per_100g', '0.0').strip()
    micronutrients = request.form.get('micronutrients', '').strip()

    errors = []
    if not name:
        errors.append('Food name is required.')
    if not category:
        errors.append('Category is required.')

    try:
        cal_val = float(calories)
        pro_val = float(protein)
        carb_val = float(carbs)
        fat_val = float(fat)
        fib_val = float(fiber) if fiber else 0.0

        if min(cal_val, pro_val, carb_val, fat_val, fib_val) < 0:
            errors.append('Nutritional values cannot be negative.')
    except ValueError:
        errors.append('Nutrition metrics must be valid numeric values.')

    if errors:
        for err in errors:
            flash(err, 'danger')
        return redirect(url_for('admin_foods'))

    try:
        execute_insert(
            """INSERT INTO food_items (name, category, serving_size, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, fiber_per_100g, micronutrients)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (name, category, serving_size, cal_val, pro_val, carb_val, fat_val, fib_val, micronutrients)
        )
        flash(f"Food item '{name}' added successfully to the database!", 'success')
    except Exception as e:
        flash(f"Error adding food: {str(e)}", 'danger')

    return redirect(url_for('admin_foods'))

@app.route('/admin/foods/edit/<int:food_id>', methods=['POST'])
@admin_required
def admin_edit_food(food_id):
    """Edit existing food item in database"""
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    serving_size = request.form.get('serving_size', '100g').strip()
    calories = request.form.get('calories_per_100g', '').strip()
    protein = request.form.get('protein_per_100g', '').strip()
    carbs = request.form.get('carbs_per_100g', '').strip()
    fat = request.form.get('fat_per_100g', '').strip()
    fiber = request.form.get('fiber_per_100g', '0.0').strip()
    micronutrients = request.form.get('micronutrients', '').strip()

    try:
        cal_val = float(calories)
        pro_val = float(protein)
        carb_val = float(carbs)
        fat_val = float(fat)
        fib_val = float(fiber) if fiber else 0.0

        execute_update(
            """UPDATE food_items
               SET name = %s, category = %s, serving_size = %s, calories_per_100g = %s,
                   protein_per_100g = %s, carbs_per_100g = %s, fat_per_100g = %s,
                   fiber_per_100g = %s, micronutrients = %s
               WHERE id = %s""",
            (name, category, serving_size, cal_val, pro_val, carb_val, fat_val, fib_val, micronutrients, food_id)
        )
        flash(f"Food item '{name}' updated successfully!", 'success')
    except Exception as e:
        flash(f"Error updating food item: {str(e)}", 'danger')

    return redirect(url_for('admin_foods'))

@app.route('/admin/foods/delete/<int:food_id>', methods=['POST'])
@admin_required
def admin_delete_food(food_id):
    """Delete food item from database"""
    try:
        execute_update("DELETE FROM food_items WHERE id = %s", (food_id,))
        flash('Food item deleted successfully.', 'info')
    except Exception as e:
        flash(f"Error deleting food item: {str(e)}", 'danger')

    return redirect(url_for('admin_foods'))

# -----------------------------------------------------------------------------
# ERROR HANDLERS
# -----------------------------------------------------------------------------

@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html', custom_content="<div class='container py-5 text-center'><h2>404 - Page Not Found</h2><p>The requested page does not exist.</p><a href='/' class='btn btn-primary'>Return Home</a></div>"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('base.html', custom_content="<div class='container py-5 text-center'><h2>500 - Server Error</h2><p>An unexpected server error occurred. Please verify database connectivity.</p><a href='/' class='btn btn-primary'>Return Home</a></div>"), 500

# -----------------------------------------------------------------------------
# APPLICATION ENTRYPOINT
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.PORT, debug=True)
