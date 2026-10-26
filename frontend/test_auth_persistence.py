import unittest
from datetime import datetime, timedelta

from components.auth_ui import clear_auth_cookies, save_auth_cookies


class FakeCookieManager:
    def __init__(self):
        self.cookies = {}
        self.options = {}

    def set(self, name, value, key, **options):
        self.cookies[name] = value
        self.options[name] = options

    def delete(self, name, key):
        del self.cookies[name]


class AuthPersistenceTests(unittest.TestCase):
    def test_access_and_refresh_tokens_get_persistent_cookies(self):
        cookie_manager = FakeCookieManager()
        save_auth_cookies(
            cookie_manager,
            {
                "access_token": "access",
                "refresh_token": "refresh",
                "user_id": "user-id"
            },
            "user@example.com"
        )

        self.assertEqual(cookie_manager.cookies["auth_token"], "access")
        self.assertEqual(cookie_manager.cookies["refresh_token"], "refresh")
        self.assertEqual(cookie_manager.cookies["user_email"], "user@example.com")
        self.assertEqual(cookie_manager.cookies["user_id"], "user-id")
        self.assertEqual(cookie_manager.options["refresh_token"]["same_site"], "lax")
        self.assertGreater(
            cookie_manager.options["refresh_token"]["expires_at"],
            datetime.now() + timedelta(days=29)
        )

    def test_sign_out_removes_all_auth_cookies(self):
        cookie_manager = FakeCookieManager()
        cookie_manager.cookies = {
            "auth_token": "access",
            "refresh_token": "refresh",
            "user_email": "user@example.com",
            "user_id": "user-id"
        }

        clear_auth_cookies(cookie_manager)

        self.assertEqual(cookie_manager.cookies, {})


if __name__ == "__main__":
    unittest.main()
