from werkzeug.security import generate_password_hash

# Defina a senha que você quer usar
senha_pura = "admin123"

# Gera o hash usando o mesmo método que usamos no banco (importante!)
# pbkdf2:sha256 com 600.000 iterações
hash_gerado = generate_password_hash(senha_pura, method="pbkdf2:sha256:600000")

print("--- SEU NOVO HASH ---")
print(hash_gerado)
print("-----------------------")