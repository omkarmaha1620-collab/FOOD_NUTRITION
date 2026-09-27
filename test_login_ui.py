from app import app

client = app.test_client()

# 1. GET /login test
res_get = client.get('/login')
assert res_get.status_code == 200, f"GET /login returned {res_get.status_code}"
html = res_get.data.decode('utf-8')

assert "Welcome to Food Nutrition Analyzer" in html, "Headline missing"
assert "Understand your food. Track your nutrition. Build healthier habits." in html, "Subtitle missing"
assert "login-quote-text" in html, "Quote container id missing"
assert "Small changes in your meals can create big changes in your health." in html, "Default quote missing"
assert 'name="email"' in html, "email input missing"
assert 'name="password"' in html, "password input missing"
assert "btn-login-action" in html, "Login action button class missing"
assert "btn-toggle-password" in html, "Password toggle button missing"
assert "btn-fill-demo" in html, "Quick fill demo button missing"
print("[PASS] Test 1: GET /login and template elements verified successfully!")

# 2. Invalid login test
res_invalid = client.post('/login', data={'email': 'wrong@example.com', 'password': 'wrongpassword'}, follow_redirects=True)
assert res_invalid.status_code == 200
html_invalid = res_invalid.data.decode('utf-8')
assert "Invalid email or password. Please try again." in html_invalid, "Invalid login error flash missing"
print("[PASS] Test 2: Invalid login error flash verified successfully!")

# 3. Empty credentials test
res_empty = client.post('/login', data={'email': '', 'password': ''}, follow_redirects=True)
assert res_empty.status_code == 200
html_empty = res_empty.data.decode('utf-8')
assert "Please enter both email and password." in html_empty, "Empty credentials validation warning missing"
print("[PASS] Test 3: Empty credentials validation verified successfully!")

# 4. Valid login test
res_valid = client.post('/login', data={'email': 'john@example.com', 'password': 'User@123'}, follow_redirects=True)
assert res_valid.status_code == 200
html_valid = res_valid.data.decode('utf-8')
assert "Welcome back" in html_valid and "Doe" in html_valid, "Dashboard greeting missing on successful login"
print("[PASS] Test 4: Valid login and redirect to dashboard verified successfully!")

print("\nALL LOGIN UI VERIFICATIONS PASSED!")
