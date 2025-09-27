import json
import hashlib
import secrets
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class EncryptionService:
    """Service for encrypting and decrypting credential data using Fernet symmetric encryption"""

    def __init__(self):
        self.iterations = 100000  # PBKDF2 iterations for key derivation

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from user password and salt using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.iterations,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def _generate_salt(self) -> bytes:
        """Generate a random salt for key derivation"""
        return secrets.token_bytes(32)

    def encrypt_credential_data(self, data: Dict[str, Any], user_password: str) -> tuple[bytes, str]:
        """
        Encrypt credential data with user-derived key

        Args:
            data: Dictionary containing credential data
            user_password: User's password for key derivation

        Returns:
            Tuple of (encrypted_data, encryption_key_id)
        """
        # Generate salt and derive key
        salt = self._generate_salt()
        key = self._derive_key(user_password, salt)

        # Create Fernet cipher
        fernet = Fernet(key)

        # Serialize credential data to JSON
        json_data = json.dumps(data).encode()
        encrypted_data = fernet.encrypt(json_data)

        # Prepend salt to encrypted data for storage
        final_data = salt + encrypted_data

        # Generate key ID for tracking (hash of salt)
        key_id = hashlib.sha256(salt).hexdigest()[:16]

        return final_data, key_id

    def decrypt_credential_data(self, encrypted_data: bytes, user_password: str) -> Dict[str, Any]:
        """
        Decrypt credential data with user-derived key

        Args:
            encrypted_data: Encrypted credential data (salt + encrypted_data)
            user_password: User's password for key derivation

        Returns:
            Decrypted credential data dictionary

        Raises:
            ValueError: If decryption fails or data is corrupted
        """
        try:
            # Extract salt from the beginning of encrypted data
            salt = encrypted_data[:32]  # First 32 bytes are the salt
            actual_encrypted_data = encrypted_data[32:]  # Rest is the encrypted data

            # Derive key using extracted salt
            key = self._derive_key(user_password, salt)
            fernet = Fernet(key)

            # Decrypt and parse JSON
            decrypted_data = fernet.decrypt(actual_encrypted_data)
            credential_data = json.loads(decrypted_data.decode())

            return credential_data

        except Exception as e:
            raise ValueError(f"Failed to decrypt credential data: {str(e)}")

    def validate_credential_type(self, credential_type: str, data: Dict[str, Any]) -> bool:
        """
        Validate credential data structure based on type

        Args:
            credential_type: Type of credential (api_key, user_pass, etc.)
            data: Credential data to validate

        Returns:
            True if valid, False otherwise
        """
        validation_schemas = {
            "api_key": {"required": ["api_key"], "optional": ["headers", "base_url"]},
            "user_pass": {"required": ["username", "password"], "optional": ["domain"]},
            "oauth": {"required": ["access_token"], "optional": ["refresh_token", "expires_in", "token_type"]},
            "ssh_key": {"required": ["private_key"], "optional": ["public_key", "passphrase"]},
            "db_connection": {"required": ["connection_string"], "optional": ["username", "password", "database"]},
            "custom": {"required": [], "optional": []}  # Custom allows any structure
        }

        if credential_type not in validation_schemas:
            return False

        schema = validation_schemas[credential_type]

        # Check required fields
        for field in schema["required"]:
            if field not in data:
                return False

        return True

    def mask_sensitive_data(self, credential_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a masked version of credential data for safe display

        Args:
            credential_type: Type of credential
            data: Original credential data

        Returns:
            Masked version of the data
        """
        masked_data = data.copy()

        sensitive_fields = {
            "api_key": ["api_key"],
            "user_pass": ["password"],
            "oauth": ["access_token", "refresh_token"],
            "ssh_key": ["private_key", "passphrase"],
            "db_connection": ["password"],
            "custom": []  # For custom, we'll mask any field containing 'password', 'key', 'token'
        }

        fields_to_mask = sensitive_fields.get(credential_type, [])

        for field in fields_to_mask:
            if field in masked_data:
                value = str(masked_data[field])
                if len(value) > 8:
                    masked_data[field] = value[:4] + "*" * (len(value) - 8) + value[-4:]
                else:
                    masked_data[field] = "*" * len(value)

        # For custom type, mask fields that look sensitive
        if credential_type == "custom":
            for key, value in masked_data.items():
                if any(term in key.lower() for term in ["password", "key", "token", "secret"]):
                    if isinstance(value, str) and len(value) > 8:
                        masked_data[key] = value[:4] + "*" * (len(value) - 8) + value[-4:]
                    elif isinstance(value, str):
                        masked_data[key] = "*" * len(value)

        return masked_data