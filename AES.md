## production-ready example that combines:

AES-256-GCM encryption

Managed Identity authentication

Key retrieval from Azure Key Vault

simple encrypt() / decrypt() methods

safe UTF-8 multilingual support

key caching (avoid repeated Key Vault calls)

#1. Architecture
Application
   |
Managed Identity
   |
Azure Key Vault  → encryption key
   |
Encryption Service (AES-256-GCM)
   |
Database (Cosmos DB / SQL / etc)

##2. Install Dependencies
pip install cryptography azure-identity azure-keyvault-secrets

#3. Environment Variables
export KEY_VAULT_URL=https://your-vault-name.vault.azure.net/
export ENCRYPTION_SECRET_NAME=health-data-key

##4. Create Encryption Key (One Time)
import os, base64
print(base64.b64encode(os.urandom(32)).decode())
## Store this value as a secret in Azure Key Vault

### Encryption Service Code
import os
import base64
import threading

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


class AzureKeyVaultKeyProvider:
    """
    Fetch and cache encryption key from Azure Key Vault
    using Managed Identity
    """

    def __init__(self, vault_url: str, secret_name: str):
        self.vault_url = vault_url
        self.secret_name = secret_name
        self._key = None
        self._lock = threading.Lock()

        credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=credential)

    def get_key(self) -> bytes:

        if self._key:
            return self._key

        with self._lock:

            if not self._key:
                secret = self.client.get_secret(self.secret_name)
                self._key = base64.b64decode(secret.value)

        return self._key


class EncryptionService:
    """
    AES-256-GCM encryption service
    """

    def __init__(self, key_provider: AzureKeyVaultKeyProvider):

        self.key_provider = key_provider

    def encrypt(self, plaintext: str) -> str:

        key = self.key_provider.get_key()

        aesgcm = AESGCM(key)

        nonce = os.urandom(12)

        ciphertext = aesgcm.encrypt(
            nonce,
            plaintext.encode("utf-8"),
            None
        )

        encrypted = nonce + ciphertext

        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt(self, encrypted_text: str) -> str:

        key = self.key_provider.get_key()

        encrypted_bytes = base64.b64decode(encrypted_text)

        nonce = encrypted_bytes[:12]
        ciphertext = encrypted_bytes[12:]

        aesgcm = AESGCM(key)

        plaintext = aesgcm.decrypt(
            nonce,
            ciphertext,
            None
        )

        return plaintext.decode("utf-8")

##6. Initialize the Service
import os

vault_url = os.environ["KEY_VAULT_URL"]
secret_name = os.environ["ENCRYPTION_SECRET_NAME"]

key_provider = AzureKeyVaultKeyProvider(
    vault_url,
    secret_name
)

crypto_service = EncryptionService(key_provider)

##7. Encrypt Example
text = "患者は頭痛があります 🤒"

encrypted_value = crypto_service.encrypt(text)

print("Encrypted:", encrypted_value)

##8. Decrypt Example
decrypted_value = crypto_service.decrypt(encrypted_value)

print("Decrypted:", decrypted_value)

##9. Example With Database Storage
doc = {
    "id": "user123",
    "symptoms_enc": crypto_service.encrypt("Severe headache 🤕"),
    "doctor_notes_enc": crypto_service.encrypt("Patient reports pain for 2 days")
}

After reading from DB:
symptoms = crypto_service.decrypt(doc["symptoms_enc"])
notes = crypto_service.decrypt(doc["doctor_notes_enc"])

###12. Security Features

✔ AES-256-GCM encryption
✔ multilingual support (UTF-8)
✔ Managed Identity authentication
✔ Key Vault secure key storage
✔ Base64 safe storage format
        

