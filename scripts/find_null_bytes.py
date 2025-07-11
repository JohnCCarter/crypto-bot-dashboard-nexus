import sys

def find_null_bytes(filepath):
    with open(filepath, 'rb') as f:
        content = f.read()
        if b'\x00' in content:
            print(f"[!] Null byte found in: {filepath}")

if __name__ == "__main__":
    files = sys.argv[1:]
    for file in files:
        find_null_bytes(file) 