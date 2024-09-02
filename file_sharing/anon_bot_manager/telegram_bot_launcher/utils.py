# utils.py
import random
import string

def generate_unique_key(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
