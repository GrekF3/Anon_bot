from cryptography.fernet import Fernet

# Генерация ключа
def generate_key():
    return Fernet.generate_key()

# Шифрование данных
def encrypt_data(data: bytes, key: bytes) -> bytes:
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data)
    return encrypted_data

# Дешифрование данных
def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data)
    return decrypted_data
