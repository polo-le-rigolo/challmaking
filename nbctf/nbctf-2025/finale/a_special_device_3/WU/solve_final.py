import base64

key = base64.b64decode("7LK71MmLlGkFoxUBhN7MAw==")
host_enc = base64.b64decode("idbfraTq+AZwjXNz")
path_enc = base64.b64decode("w+fTmKDq5jxQyFp74Lu6bq/n3+O+wN0tMuAsbfGwqkiZ")
def xor_bytes(data, key):
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

host = xor_bytes(host_enc, key).decode()
path = xor_bytes(path_enc, key).decode()

print("Host:", host)
print("Path:", path)
