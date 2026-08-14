import re

class Validators:
    @staticmethod
    def is_valid_username(username: str) -> tuple:
        if not username or len(username) < 3 or len(username) > 30:
            return False, "Username must be between 3 and 30 characters long."
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores."
        return True, ""

    @staticmethod
    def is_valid_email(email: str) -> tuple:
        if not email or len(email) > 120:
            return False, "Invalid email length."
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            return False, "Please enter a valid email address."
        return True, ""

    @staticmethod
    def check_password_strength(password: str) -> tuple:
        """
        Validates password strength rules:
        - At least 8 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains digit
        - Contains special character
        Returns (is_valid, score_percent, feedback_message)
        """
        if not password:
            return False, 0, "Password is required."

        score = 0
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 20
        if re.search(r'[A-Z]', password):
            score += 20
        if re.search(r'[a-z]', password):
            score += 20
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[^A-Za-z0-9]', password):
            score += 10

        if len(password) < 8:
            return False, score, "Password must be at least 8 characters long."
        if not re.search(r'[A-Z]', password):
            return False, score, "Password must contain at least one uppercase letter."
        if not re.search(r'[a-z]', password):
            return False, score, "Password must contain at least one lowercase letter."
        if not re.search(r'\d', password):
            return False, score, "Password must contain at least one number."
        if not re.search(r'[^A-Za-z0-9]', password):
            return False, score, "Password must contain at least one special character (!@#$%^&*)."

        return True, score, "Strong password"
