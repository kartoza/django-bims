"""
Backward-compatible SHA1 password hasher for Django 6.

Django 6 removed SHA1PasswordHasher. This thin wrapper allows
existing sha1-hashed passwords to still be *verified* (and
automatically upgraded to PBKDF2 on next login).
"""
import hashlib

from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.crypto import constant_time_compare


class LegacySHA1PasswordHasher(BasePasswordHasher):
    """
    Verify-only hasher for legacy ``sha1$<salt>$<hash>`` passwords.

    It is intentionally listed *after* PBKDF2PasswordHasher in
    PASSWORD_HASHERS so it is never used for new passwords.
    """

    algorithm = "sha1"

    def encode(self, password, salt):
        assert password is not None
        assert salt and "$" not in salt
        hash_val = hashlib.sha1(
            (salt + password).encode()
        ).hexdigest()
        return f"{self.algorithm}${salt}${hash_val}"

    def verify(self, password, encoded):
        algorithm, salt, _ = encoded.split("$", 2)
        assert algorithm == self.algorithm
        return constant_time_compare(encoded, self.encode(password, salt))

    def safe_summary(self, encoded):
        from django.contrib.auth.hashers import mask_hash
        algorithm, salt, hash_val = encoded.split("$", 2)
        return {
            "algorithm": algorithm,
            "salt": mask_hash(salt, show=2),
            "hash": mask_hash(hash_val),
        }

    def harden_runtime(self, password, encoded):
        pass
