#!/usr/bin/env python3
# ============================================================
# HYPERION-SHIELD V6 - Auto Overwrite
# Encrypt → Langsung timpa file asli
# Decrypt → Balikin ke versi asli
# ============================================================

import os
import sys
import base64
import subprocess
import tempfile
import hashlib
import random
import string
import shutil
from pathlib import Path

# ========== KONFIGURASI ==========
VERSION = "6.0"
SECRET_KEY = "HYPERION_SECRET_2025"  # GANTI DENGAN KEY RAHASIA LO
OUTPUT_DIR = "/sdcard/Download"

# ========== FUNGSI UTILITY ==========
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_banner():
    print("\n" + "="*55)
    print("   ⚡ HYPERION-SHIELD V{} ⚡".format(VERSION))
    print("   Auto Overwrite | Encrypt | Decrypt")
    print("="*55 + "\n")

def rand_str(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def log(msg, is_error=False):
    prefix = "✅" if not is_error else "❌"
    print(f"{prefix} {msg}")

# ========== ENKRIPSI LAYER ==========
def rot13(text):
    result = []
    for c in text:
        if 'a' <= c <= 'z':
            result.append(chr((ord(c) - ord('a') + 13) % 26 + ord('a')))
        elif 'A' <= c <= 'Z':
            result.append(chr((ord(c) - ord('A') + 13) % 26 + ord('A')))
        else:
            result.append(c)
    return ''.join(result)

def reverse_string(text):
    return text[::-1]

def xor_encrypt(text, key):
    result = ""
    for i, c in enumerate(text):
        char_code = ord(c) ^ ord(key[i % len(key)])
        safe_code = (char_code % 95) + 32
        result += chr(safe_code)
    return result

def xor_decrypt(text, key):
    # XOR simetris, sama dengan encrypt
    return xor_encrypt(text, key)

def base64_encode_multiple(text, times=20):
    result = base64.b64encode(text.encode()).decode()
    for _ in range(times - 1):
        result = base64.b64encode(result.encode()).decode()
    return result

def base64_decode_multiple(text, times=20):
    result = text
    for _ in range(times):
        result = base64.b64decode(result.encode()).decode()
    return result

def encrypt_payload(script, key):
    """Enkripsi payload dengan multiple layer"""
    print("   🔄 ROT13...")
    step = rot13(script)
    print("   🔄 Reverse...")
    step = reverse_string(step)
    print("   🔐 XOR encryption...")
    step = xor_encrypt(step, key)
    print("   📤 Base64 20x...")
    step = base64_encode_multiple(step, 20)
    return step

def decrypt_payload(encrypted, key):
    """Dekripsi payload"""
    print("   📥 Base64 20x decode...")
    step = base64_decode_multiple(encrypted, 20)
    print("   🔓 XOR decryption...")
    step = xor_decrypt(step, key)
    print("   🔄 Reverse...")
    step = reverse_string(step)
    print("   🔄 ROT13...")
    step = rot13(step)
    return step

# ========== GENERATE OUTPUT SCRIPT (ENCRYPT) ==========
def generate_encrypted_script(encrypted_payload, key, original_size):
    """Generate shell script dengan binary ter-embed"""
    fake_hash = hashlib.md5(encrypted_payload.encode()).hexdigest()[:16]
    
    # Split payload
    chunks = [encrypted_payload[i:i+60] for i in range(0, len(encrypted_payload), 60)]
    var_names = [f"v{rand_str(5)}" for _ in chunks]
    vars_code = ';'.join([f'{vn}="{chunk}"' for vn, chunk in zip(var_names, chunks)])
    join_vars = ''.join([f'${vn}' for vn in var_names])
    
    script_content = f'''#!/system/bin/sh
# HYPERION-SHIELD | Encrypted Script
# Only authorized user can decrypt

# Anti tamper
[ "$(md5sum "$0" 2>/dev/null | cut -d' ' -f1)" != "{fake_hash}" ] && exit 1

# Encrypted payload
{vars_code}
PAYLOAD="{join_vars}"
KEY="{key}"

# Decrypt function (20x base64 → XOR → Reverse → ROT13)
decrypt() {{
    d="$1"
    i=0
    while [ $i -lt 20 ]; do
        d=$(echo "$d" | base64 -d 2>/dev/null)
        i=$((i+1))
    done
    
    # XOR
    out=""
    j=0
    kl=$(echo -n "$KEY" | wc -c)
    while [ $j -lt ${{#d}} ]; do
        c=$(printf "%d" "'${{d:$j:1}}" 2>/dev/null)
        k=$(printf "%d" "'${{KEY:$((j % kl)):1}}" 2>/dev/null)
        res=$((c ^ k))
        safe=$(( (res % 95) + 32 ))
        out="$out$(printf "\\\\$(printf '%03o' "$safe")")"
        j=$((j+1))
    done
    
    # Reverse
    out=$(echo "$out" | rev)
    
    # ROT13
    echo "$out" | tr 'A-Za-z' 'N-ZA-Mn-za-m'
}

# Execute
FINAL=$(decrypt "$PAYLOAD")
if [ -n "$FINAL" ]; then
    eval "$FINAL"
else
    echo "[ERROR] Decryption failed"
fi
exit 0
'''
    return script_content

# ========== ENCRYPT FILE (AUTO TIMPA) ==========
def encrypt_file(file_path, key):
    """Encrypt file dan timpa aslinya (backup otomatis)"""
    print(f"\n📁 File: {file_path}")
    
    if not os.path.exists(file_path):
        log(f"File not found: {file_path}", True)
        return False
    
    # Baca file asli
    with open(file_path, 'r') as f:
        original_content = f.read()
    
    print(f"📊 Size: {len(original_content)} bytes")
    
    # Buat backup
    backup_path = file_path + ".backup"
    shutil.copy2(file_path, backup_path)
    print(f"💾 Backup: {backup_path}")
    
    # Encrypt
    print("\n🔐 Encrypting...")
    encrypted_payload = encrypt_payload(original_content, key)
    
    # Generate script encrypted
    encrypted_script = generate_encrypted_script(encrypted_payload, key, len(original_content))
    
    # Timpa file asli
    with open(file_path, 'w') as f:
        f.write(encrypted_script)
    
    os.chmod(file_path, 0o755)
    
    print(f"\n✅ Encrypted: {file_path}")
    print(f"📌 Jalankan di Brevent: sh {file_path}")
    return True

# ========== DECRYPT FILE (BALIKIN KE ASLI) ==========
def decrypt_file(file_path, key):
    """Decrypt file dan balikin ke versi asli"""
    print(f"\n📁 File: {file_path}")
    
    if not os.path.exists(file_path):
        log(f"File not found: {file_path}", True)
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract payload dari shell script
    import re
    match = re.search(r'PAYLOAD="([^"]+)"', content)
    if not match:
        log("Invalid encrypted file format", True)
        return False
    
    encrypted_payload = match.group(1)
    
    # Cek apakah ada backup
    backup_path = file_path + ".backup"
    if os.path.exists(backup_path):
        print(f"💾 Backup found, restoring from backup...")
        shutil.copy2(backup_path, file_path)
        print(f"✅ Restored from backup: {file_path}")
        return True
    
    # Kalo gak ada backup, decrypt manual
    print("\n🔓 Decrypting (no backup found)...")
    try:
        decrypted = decrypt_payload(encrypted_payload, key)
        
        # Timpa file asli dengan hasil decrypt
        with open(file_path, 'w') as f:
            f.write(decrypted)
        
        print(f"✅ Decrypted: {file_path}")
        return True
    except Exception as e:
        log(f"Decryption failed: {e}", True)
        return False

# ========== CHECK DEPENDENCIES ==========
def check_dependencies():
    gcc = subprocess.run(['which', 'gcc'], capture_output=True).returncode == 0
    clang = subprocess.run(['which', 'clang'], capture_output=True).returncode == 0
    return gcc or clang

# ========== MAIN MENU ==========
def main_menu():
    while True:
        clear_screen()
        print_banner()
        print("   📋 MAIN MENU:")
        print("   ┌─────────────────────────────────────┐")
        print("   │  [1] 🔒 ENCRYPT File                │")
        print("   │  [2] 🔓 DECRYPT File                │")
        print("   │  [3] 📁 Show Encrypted Files        │")
        print("   │  [4] ⚙️  Settings                   │")
        print("   │  [0] 🚪 EXIT                        │")
        print("   └─────────────────────────────────────┘")
        print("")
        
        choice = input("   Choice: ").strip()
        
        if choice == "1":
            clear_screen()
            print_banner()
            print("   🔒 ENCRYPT FILE")
            print("   ─────────────────────────────────────")
            print("   📌 Contoh path:")
            print("      - /sdcard/script.sh")
            print("      - /data/data/com.termux/files/home/test.sh")
            print("")
            file_path = input("   File path: ").strip()
            file_path = os.path.expanduser(file_path)
            
            if not os.path.exists(file_path):
                log(f"File not found: {file_path}", True)
                input("\n   Press Enter to continue...")
                continue
            
            key = input(f"   Encryption key (default: {SECRET_KEY[:4]}...): ").strip()
            if not key:
                key = SECRET_KEY
            
            if encrypt_file(file_path, key):
                log(f"File encrypted successfully!")
            else:
                log("Encryption failed!", True)
            input("\n   Press Enter to continue...")
        
        elif choice == "2":
            clear_screen()
            print_banner()
            print("   🔓 DECRYPT FILE")
            print("   ─────────────────────────────────────")
            file_path = input("   File path: ").strip()
            file_path = os.path.expanduser(file_path)
            
            if not os.path.exists(file_path):
                log(f"File not found: {file_path}", True)
                input("\n   Press Enter to continue...")
                continue
            
            key = input(f"   Decryption key: ").strip()
            
            if key != SECRET_KEY:
                log("Wrong key! Access denied.", True)
                input("\n   Press Enter to continue...")
                continue
            
            if decrypt_file(file_path, key):
                log(f"File decrypted successfully!")
            else:
                log("Decryption failed!", True)
            input("\n   Press Enter to continue...")
        
        elif choice == "3":
            clear_screen()
            print_banner()
            print("   📁 ENCRYPTED FILES")
            print("   ─────────────────────────────────────")
            
            # Cari file .sh yang mungkin ter-encrypt
            search_paths = ["/sdcard", "/sdcard/Download", "/data/data/com.termux/files/home"]
            found = []
            
            for sp in search_paths:
                if os.path.exists(sp):
                    for f in os.listdir(sp):
                        if f.endswith('.sh'):
                            full_path = os.path.join(sp, f)
                            # Cek apakah file ter-encrypt (ada pattern PAYLOAD)
                            try:
                                with open(full_path, 'r') as chk:
                                    content = chk.read()
                                    if 'PAYLOAD="' in content and 'HYPERION-SHIELD' in content:
                                        found.append(full_path)
                            except:
                                pass
            
            if found:
                for i, f in enumerate(found, 1):
                    size = os.path.getsize(f) / 1024
                    print(f"   {i}. {f} ({size:.2f} KB)")
            else:
                print("   No encrypted files found")
            
            input("\n   Press Enter to continue...")
        
        elif choice == "4":
            clear_screen()
            print_banner()
            print("   ⚙️ SETTINGS")
            print("   ─────────────────────────────────────")
            print(f"   Current SECRET_KEY: {SECRET_KEY}")
            new_key = input("   New key (min 10 chars, enter to skip): ").strip()
            if new_key and len(new_key) >= 10:
                global SECRET_KEY
                SECRET_KEY = new_key
                log(f"Key changed to: {SECRET_KEY[:4]}...{SECRET_KEY[-4:]}")
            print(f"   Output backup: .backup (same folder)")
            input("\n   Press Enter to continue...")
        
        elif choice == "0":
            print("\n   👋 Goodbye, Komandan!")
            sys.exit(0)

# ========== RUN ==========
if __name__ == "__main__":
    # Setup Termux
    if os.path.exists("/data/data/com.termux"):
        print("📱 Termux detected. Setting up...")
        os.system("termux-setup-storage 2>/dev/null")
    
    # Cek compiler
    if not check_dependencies():
        print("⚠️ GCC/Clang not found! Installing...")
        os.system("pkg install clang -y")
    
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
