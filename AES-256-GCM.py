AES-256-GCM:

pip install cryptography azure-identity azure-keyvault-secrets


import os
import base64
import threading
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class EncryptionService:

    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")

        self.key = key
        self._lock = threading.Lock()

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt string and return Base64 encoded ciphertext
        """

        with self._lock:

            aesgcm = AESGCM(self.key)

            nonce = os.urandom(12)

            ciphertext = aesgcm.encrypt(
                nonce,
                plaintext.encode("utf-8"),
                None
            )

            encrypted = nonce + ciphertext

            return base64.b64encode(encrypted).decode("utf-8")

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt Base64 encoded ciphertext
        """

        with self._lock:

            encrypted_bytes = base64.b64decode(encrypted_text)

            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]

            aesgcm = AESGCM(self.key)

            plaintext = aesgcm.decrypt(
                nonce,
                ciphertext,
                None
            )

            return plaintext.decode("utf-8")



TEST.py:

import os

key = os.urandom(32)

crypto = EncryptionService(key)

text = "患者は頭痛があります 🤒"

enc = crypto.encrypt(text)

print("Encrypted:", enc)

dec = crypto.decrypt(enc)

print("Decrypted:", dec)


###Generate key:
Value must be base64 encoded 32 byte key.

  import os, base64
print(base64.b64encode(os.urandom(32)).decode())

Python Code to Load Key From Key Vault:
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import base64

VAULT_URL = "https://yourvault.vault.azure.net"

credential = DefaultAzureCredential()

client = SecretClient(
    vault_url=VAULT_URL,
    credential=credential
)

secret = client.get_secret("health-data-key")

key = base64.b64decode(secret.value)

crypto = EncryptionService(key)

Use Managed Identity for authentication.

