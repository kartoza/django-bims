import hashlib

from django.test import TestCase, override_settings
from django.contrib.auth.hashers import check_password, make_password, identify_hasher

from bims.hashers import LegacySHA1PasswordHasher


PASSWORD_HASHERS_WITH_SHA1 = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'bims.hashers.LegacySHA1PasswordHasher',
]


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS_WITH_SHA1)
class LegacySHA1PasswordHasherTest(TestCase):

    def _make_sha1_encoded(self, password, salt="abcdef"):
        hash_val = hashlib.sha1((salt + password).encode()).hexdigest()
        return f"sha1${salt}${hash_val}"

    def test_encode_produces_correct_format(self):
        hasher = LegacySHA1PasswordHasher()
        encoded = hasher.encode("secret", "mysalt")
        self.assertTrue(encoded.startswith("sha1$mysalt$"))
        parts = encoded.split("$")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "sha1")
        self.assertEqual(parts[1], "mysalt")

    def test_verify_correct_password(self):
        hasher = LegacySHA1PasswordHasher()
        encoded = hasher.encode("mypassword", "salt123")
        self.assertTrue(hasher.verify("mypassword", encoded))

    def test_verify_wrong_password(self):
        hasher = LegacySHA1PasswordHasher()
        encoded = hasher.encode("mypassword", "salt123")
        self.assertFalse(hasher.verify("wrongpassword", encoded))

    def test_check_password_with_legacy_hash(self):
        encoded = self._make_sha1_encoded("testpass")
        self.assertTrue(check_password("testpass", encoded))
        self.assertFalse(check_password("badpass", encoded))

    def test_identify_hasher(self):
        encoded = self._make_sha1_encoded("pw")
        hasher = identify_hasher(encoded)
        self.assertIsInstance(hasher, LegacySHA1PasswordHasher)

    def test_new_passwords_use_pbkdf2_not_sha1(self):
        encoded = make_password("newpassword")
        self.assertTrue(encoded.startswith("pbkdf2_sha256$"))

    def test_safe_summary(self):
        hasher = LegacySHA1PasswordHasher()
        encoded = hasher.encode("pw", "saltydog")
        summary = hasher.safe_summary(encoded)
        self.assertEqual(summary["algorithm"], "sha1")
        self.assertIn("*", summary["salt"])
        self.assertIn("*", summary["hash"])
