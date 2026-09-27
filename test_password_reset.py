"""
Comprehensive Test Suite for Forgot & Reset Password Feature
Tests all security requirements, token handling, expiration, anti-enumeration,
password hashing, and end-to-end user workflows.
"""

import unittest
import hashlib
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash

from app import app, send_reset_email
from db import execute_query, execute_update, execute_insert


class PasswordResetTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Clean up any leftover test data
        execute_update("DELETE FROM users WHERE email = 'test_reset_user@example.com'")
        execute_update("DELETE FROM password_resets WHERE user_id NOT IN (SELECT id FROM users)")

        # Create a dedicated test user for password reset tests
        self.test_password = 'OriginalPassword@123'
        self.test_password_hash = generate_password_hash(self.test_password)
        self.test_user_id = execute_insert(
            """INSERT INTO users (name, email, password_hash, age, gender, height_cm, weight_kg, activity_level)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            ('Test Reset User', 'test_reset_user@example.com', self.test_password_hash, 25, 'Female', 165.0, 60.0, 'Moderately Active')
        )

        # Clear any tokens for this user
        execute_update("DELETE FROM password_resets WHERE user_id = %s", (self.test_user_id,))

    def tearDown(self):
        # Clean up test user and associated password_resets
        execute_update("DELETE FROM password_resets WHERE user_id = %s", (self.test_user_id,))
        execute_update("DELETE FROM users WHERE email = 'test_reset_user@example.com'")

        # Ensure demo user John Doe has his standard password restored
        execute_update(
            "UPDATE users SET password_hash = %s WHERE id = 1 AND email = 'john@example.com'",
            ('scrypt:32768:8:1$4rmMbrQglfcWpdSn$dc7741c6e9a57d91b245381e509d58d60652cfc379892ab13d24d1b8d314936dba7acc358663d2e55c85514d545cfc0760920459489876ce76203fb715282ee6',)
        )

    def test_01_login_page_has_forgot_password_link(self):
        """Requirement 1: Login page must display a clearly visible 'Forgot Password?' link"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertIn('Forgot Password?', html)
        self.assertIn('/forgot-password', html)

    def test_02_forgot_password_page_renders(self):
        """Requirement 2: Forgot Password page displays email input form with matching theme"""
        response = self.client.get('/forgot-password')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertIn('Forgot Password?', html)
        self.assertIn('name="email"', html)
        self.assertIn('Send Password Reset Link', html)
        self.assertIn('/login', html)

    def test_03_anti_enumeration_generic_response(self):
        """Requirement 3: Protect against email enumeration by showing identical generic message"""
        # Test with existing email
        res_existing = self.client.post('/forgot-password', data={'email': 'test_reset_user@example.com'})
        self.assertEqual(res_existing.status_code, 200)
        html_existing = res_existing.data.decode('utf-8')
        expected_msg = "If an account exists for this email, a password reset link has been sent."
        self.assertIn(expected_msg, html_existing)

        # Test with non-existent email
        res_nonexistent = self.client.post('/forgot-password', data={'email': 'nobody_exists_12345@example.com'})
        self.assertEqual(res_nonexistent.status_code, 200)
        html_nonexistent = res_nonexistent.data.decode('utf-8')
        self.assertIn(expected_msg, html_nonexistent)

        # Ensure no token was created for non-existent email
        token_count = execute_query(
            "SELECT COUNT(*) as cnt FROM password_resets pr JOIN users u ON pr.user_id = u.id WHERE u.email = 'nobody_exists_12345@example.com'",
            fetch_one=True
        )
        self.assertEqual(token_count['cnt'], 0)

    def test_04_token_security_and_storage(self):
        """Requirement 4 & 5: Cryptographically secure token, hashed in DB, 15-30m expiration, never plaintext"""
        response = self.client.post('/forgot-password', data={'email': 'test_reset_user@example.com'})
        self.assertEqual(response.status_code, 200)

        # Retrieve stored reset records for this user
        records = execute_query(
            "SELECT id, user_id, token_hash, expires_at, used FROM password_resets WHERE user_id = %s",
            (self.test_user_id,)
        )
        self.assertEqual(len(records), 1)
        record = records[0]

        # Verify token_hash is a 64-character SHA-256 hex string
        self.assertEqual(len(record['token_hash']), 64)
        self.assertEqual(record['used'], 0)

        # Verify expiration is between 15 and 30 minutes in the future
        now = datetime.now()
        expires_at = record['expires_at']
        diff_minutes = (expires_at - now).total_seconds() / 60.0
        self.assertGreaterEqual(diff_minutes, 14.0)
        self.assertLessEqual(diff_minutes, 31.0)

        # Verify plaintext token is NOT stored anywhere in the database record
        html = response.data.decode('utf-8')
        # In dev mode, the link is in the response; extract raw token from dev link
        if 'reset-password/' in html:
            raw_token = html.split('reset-password/')[1].split('"')[0]
            # Ensure raw_token is not equal to token_hash
            self.assertNotEqual(raw_token, record['token_hash'])
            # Verify SHA256 of raw_token matches stored token_hash
            computed_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
            self.assertEqual(computed_hash, record['token_hash'])

    def test_05_invalid_token_rejected(self):
        """Requirement 6: Invalid token is rejected and redirects to forgot password"""
        response = self.client.get('/reset-password/invalid_non_existent_token_1234567890', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertIn('The password reset link is invalid or does not exist', html)

    def test_06_expired_token_rejected(self):
        """Requirement 5: Expired token is rejected"""
        # Create an expired token manually
        fake_token = "expired_token_test_string_1234567890"
        fake_hash = hashlib.sha256(fake_token.encode('utf-8')).hexdigest()
        expired_time = datetime.now() - timedelta(minutes=10)

        execute_insert(
            """INSERT INTO password_resets (user_id, token_hash, expires_at, used)
               VALUES (%s, %s, %s, 0)""",
            (self.test_user_id, fake_hash, expired_time)
        )

        response = self.client.get(f'/reset-password/{fake_token}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertIn('This password reset link has expired', html)

    def test_07_successful_password_reset_and_login(self):
        """Requirement 6 & 12: Successful reset, hashing with Werkzeug, token marked used, can log in with new password"""
        # Request password reset
        res_forgot = self.client.post('/forgot-password', data={'email': 'test_reset_user@example.com'})
        html_forgot = res_forgot.data.decode('utf-8')

        # Extract token from development mode link
        self.assertIn('/reset-password/', html_forgot)
        raw_token = html_forgot.split('/reset-password/')[1].split('"')[0]

        # 1. GET reset page with valid token
        res_reset_page = self.client.get(f'/reset-password/{raw_token}')
        self.assertEqual(res_reset_page.status_code, 200)
        self.assertIn('Reset Password', res_reset_page.data.decode('utf-8'))

        # 2. Test password length validation (< 6 chars)
        res_short = self.client.post(f'/reset-password/{raw_token}', data={
            'password': '123',
            'confirm_password': '123'
        })
        self.assertEqual(res_short.status_code, 200)
        self.assertIn('Password must be at least 6 characters long', res_short.data.decode('utf-8'))

        # 3. Test password mismatch validation
        res_mismatch = self.client.post(f'/reset-password/{raw_token}', data={
            'password': 'NewPassword@2026',
            'confirm_password': 'DifferentPassword@2026'
        })
        self.assertEqual(res_mismatch.status_code, 200)
        self.assertIn('Passwords do not match', res_mismatch.data.decode('utf-8'))

        # 4. Perform successful password reset
        new_password = 'BrandNewPassword@2026'
        res_success = self.client.post(f'/reset-password/{raw_token}', data={
            'password': new_password,
            'confirm_password': new_password
        }, follow_redirects=True)
        self.assertEqual(res_success.status_code, 200)
        html_success = res_success.data.decode('utf-8')
        self.assertIn('Your password has been reset successfully', html_success)

        # 5. Verify token is marked as used in DB
        token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
        token_record = execute_query(
            "SELECT used FROM password_resets WHERE token_hash = %s",
            (token_hash,),
            fetch_one=True
        )
        self.assertEqual(token_record['used'], 1)

        # 6. Verify user password_hash in DB is updated and hashed with Werkzeug
        user_record = execute_query(
            "SELECT password_hash FROM users WHERE id = %s",
            (self.test_user_id,),
            fetch_one=True
        )
        self.assertNotEqual(user_record['password_hash'], self.test_password_hash)
        self.assertTrue(check_password_hash(user_record['password_hash'], new_password))
        self.assertFalse(check_password_hash(user_record['password_hash'], self.test_password))

        # 7. Test token cannot be reused
        res_reuse = self.client.get(f'/reset-password/{raw_token}', follow_redirects=True)
        self.assertEqual(res_reuse.status_code, 200)
        self.assertIn('This password reset link has already been used', res_reuse.data.decode('utf-8'))

        # 8. Test old password no longer works
        res_old_login = self.client.post('/login', data={
            'email': 'test_reset_user@example.com',
            'password': self.test_password
        }, follow_redirects=True)
        self.assertEqual(res_old_login.status_code, 200)
        self.assertIn('Invalid email or password', res_old_login.data.decode('utf-8'))

        # 9. Test new password successfully logs in
        res_new_login = self.client.post('/login', data={
            'email': 'test_reset_user@example.com',
            'password': new_password
        }, follow_redirects=True)
        self.assertEqual(res_new_login.status_code, 200)
        self.assertIn('Welcome back, Test Reset User', res_new_login.data.decode('utf-8'))

    def test_08_existing_users_unaffected(self):
        """Requirement 12: Existing users (John Doe) and Admins remain unaffected and can log in normally"""
        # User login
        res_user = self.client.post('/login', data={
            'email': 'john@example.com',
            'password': 'User@123'
        }, follow_redirects=True)
        self.assertEqual(res_user.status_code, 200)
        self.assertIn('Welcome back', res_user.data.decode('utf-8'))

        # Admin login
        res_admin = self.client.post('/admin/login', data={
            'identifier': 'admin@nutrition.com',
            'password': 'Rakshitha@456'
        }, follow_redirects=True)
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn('Admin Dashboard', res_admin.data.decode('utf-8'))

    def test_09_smtp_sending_when_configured(self):
        """Requirement 8: Verify SMTP sending when mail server credentials are configured in environment"""
        from unittest.mock import patch, MagicMock

        # Save previous config
        orig_server = self.app.config.get('MAIL_SERVER')
        orig_user = self.app.config.get('MAIL_USERNAME')
        orig_pw = self.app.config.get('MAIL_PASSWORD')

        try:
            self.app.config['MAIL_SERVER'] = 'smtp.example.com'
            self.app.config['MAIL_PORT'] = 587
            self.app.config['MAIL_USERNAME'] = 'notifications@nutrianalyzer.com'
            self.app.config['MAIL_PASSWORD'] = 'smtp_secret_pass'
            self.app.config['MAIL_USE_TLS'] = True

            with patch('smtplib.SMTP') as mock_smtp:
                mock_instance = MagicMock()
                mock_smtp.return_value.__enter__.return_value = mock_instance

                status, error_msg, dev_link = send_reset_email(
                    'test_reset_user@example.com',
                    'Test Reset User',
                    'http://localhost/reset-password/sample_token_123'
                )

                self.assertEqual(status, 'sent')
                self.assertIsNone(error_msg)
                self.assertIsNone(dev_link)
                mock_smtp.assert_called_with('smtp.example.com', 587, timeout=15)
                mock_instance.starttls.assert_called_once()
                mock_instance.login.assert_called_with('notifications@nutrianalyzer.com', 'smtp_secret_pass')
                self.assertTrue(mock_instance.send_message.called)
        finally:
            self.app.config['MAIL_SERVER'] = orig_server
            self.app.config['MAIL_USERNAME'] = orig_user
            self.app.config['MAIL_PASSWORD'] = orig_pw

    def test_10_no_raw_link_when_smtp_succeeds(self):
        """Requirement 5: When SMTP is configured and succeeds, raw reset URL must NOT be displayed on page"""
        from unittest.mock import patch, MagicMock

        orig_server = self.app.config.get('MAIL_SERVER')
        orig_user = self.app.config.get('MAIL_USERNAME')
        orig_pw = self.app.config.get('MAIL_PASSWORD')

        try:
            self.app.config['MAIL_SERVER'] = 'smtp.gmail.com'
            self.app.config['MAIL_PORT'] = 587
            self.app.config['MAIL_USERNAME'] = 'mailer@example.com'
            self.app.config['MAIL_PASSWORD'] = 'test_app_password'

            with patch('smtplib.SMTP') as mock_smtp:
                mock_instance = MagicMock()
                mock_smtp.return_value.__enter__.return_value = mock_instance

                response = self.client.post('/forgot-password', data={'email': 'test_reset_user@example.com'})
                self.assertEqual(response.status_code, 200)
                html = response.data.decode('utf-8')

                # Normal success message must be shown
                self.assertIn("If an account exists for this email, a password reset link has been sent.", html)
                # Raw reset link container or test shortcut must NOT be shown
                self.assertNotIn("Development / Local Testing Mode", html)
                self.assertNotIn("/reset-password/", html)
        finally:
            self.app.config['MAIL_SERVER'] = orig_server
            self.app.config['MAIL_USERNAME'] = orig_user
            self.app.config['MAIL_PASSWORD'] = orig_pw

    def test_11_clear_error_handling_when_smtp_fails(self):
        """Requirement 7: Clear error handling displayed when SMTP email sending fails"""
        import smtplib
        from unittest.mock import patch

        orig_server = self.app.config.get('MAIL_SERVER')
        orig_user = self.app.config.get('MAIL_USERNAME')
        orig_pw = self.app.config.get('MAIL_PASSWORD')

        try:
            self.app.config['MAIL_SERVER'] = 'smtp.gmail.com'
            self.app.config['MAIL_PORT'] = 587
            self.app.config['MAIL_USERNAME'] = 'mailer@example.com'
            self.app.config['MAIL_PASSWORD'] = 'wrong_password'

            with patch('smtplib.SMTP') as mock_smtp:
                # Simulate Gmail authentication rejection (535)
                mock_smtp.side_effect = smtplib.SMTPAuthenticationError(535, b"5.7.8 Username and Password not accepted")

                response = self.client.post('/forgot-password', data={'email': 'test_reset_user@example.com'})
                self.assertEqual(response.status_code, 200)
                html = response.data.decode('utf-8')

                self.assertIn("Email delivery error", html)
                self.assertIn("SMTP authentication failed", html)
                # Password must NOT be logged or displayed
                self.assertNotIn("wrong_password", html)
        finally:
            self.app.config['MAIL_SERVER'] = orig_server
            self.app.config['MAIL_USERNAME'] = orig_user
            self.app.config['MAIL_PASSWORD'] = orig_pw


if __name__ == '__main__':
    unittest.main()
