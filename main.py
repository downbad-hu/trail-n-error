import os
import sys
import shutil
import subprocess
import re
from datetime import datetime

# ========= PyInstaller Compatibility ==========
def resource_path(relative_path):
    try:
        return os.path.join(sys._MEIPASS, relative_path)
    except Exception:
        return os.path.abspath(relative_path)

# ========= Config ==========
APKTOOL = resource_path("apktool.jar")
ZIPALIGN = resource_path("build-tools\\zipalign.exe")
SIGNER = resource_path("build-tools\\apksigner.bat")
KEYSTORE = resource_path("debug.keystore")
ALIAS = "androiddebugkey"
PASSWORD = "android"

# ========= Logging ==========
def log(msg):
    print(f"[🛠] {msg}")

# ========= Run Command ==========
def run(cmd):
    log(f"▶ {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        log(f"❌ Error during: {cmd}")
        input("Press Enter to exit.")
        exit(1)

# ========= Find APK ==========
def find_apk():
    folder = "drop_apk_here"
    os.makedirs(folder, exist_ok=True)
    for file in os.listdir(folder):
        if file.endswith(".apk"):
            return os.path.join(folder, file)
    log("❌ No APK found in drop_apk_here folder.")
    input("Press Enter to exit.")
    exit(1)

# ========= Decompile APK ==========
def decompile_apk(apk_path):
    if os.path.exists("decompiled_apk"):
        shutil.rmtree("decompiled_apk")
    run(f'java -jar "{APKTOOL}" d "{apk_path}" -o decompiled_apk -f')

# ========= Clean Manifest ==========
def clean_manifest():
    manifest = "decompiled_apk/AndroidManifest.xml"
    if not os.path.exists(manifest):
        log("Manifest not found.")
        return
    with open(manifest, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r'<uses-permission[^>]*(AD_ID|INTERNET|NETWORK).*?/>', '', content)
    content = re.sub(r'<meta-data[^>]+ads[^>]+/>', '', content, flags=re.IGNORECASE)
    with open(manifest, "w", encoding="utf-8") as f:
        f.write(content)
    log("✅ Cleaned manifest")

# ========= Smali Ad Scanner ==========
def scan_smali():
    ad_keywords = [
        "com/google/ads", "com/facebook/ads",
        "com/unity3d/ads", "AdView", "AdRequest", "AdListener"
    ]
    count = 0
    for root, _, files in os.walk("decompiled_apk"):
        for file in files:
            if file.endswith(".smali"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                new_lines = [line for line in lines if not any(keyword in line for keyword in ad_keywords)]
                if lines != new_lines:
                    with open(path, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)
                    count += 1
    log(f"✅ Smali ad references removed from {count} files")

# ========= Build, Align & Sign ==========
def build_aligned_signed_apk():
    log("🔨 Rebuilding APK...")
    run(f'java -jar "{APKTOOL}" b decompiled_apk -o temp_unsigned.apk')

    log("📏 Aligning APK...")
    run(f'"{ZIPALIGN}" -p 4 temp_unsigned.apk aligned.apk')

    log("🔏 Signing APK...")
    run(f'"{SIGNER}" sign --ks "{KEYSTORE}" --ks-key-alias "{ALIAS}" --ks-pass pass:{PASSWORD} aligned.apk')

    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_name = f"output\\final_cleaned_{timestamp}.apk"
    if os.path.exists("aligned.apk"):
        shutil.move("aligned.apk", final_name)
        log(f"✅ Final APK saved to: {final_name}")
    else:
        log("❌ Signing failed — aligned.apk not found.")
        input("Press Enter to exit.")
        exit(1)

# ========= Main Logic ==========
def main():
    log("Starting APK Ad Remover Tool")
    apk = find_apk()
    log(f"✅ Found APK: {apk}")

    decompile_apk(apk)
    clean_manifest()
    scan_smali()
    build_aligned_signed_apk()

    # Clean temp files
    for f in ["temp_unsigned.apk", "aligned.apk"]:
        if os.path.exists(f):
            os.remove(f)

    log("✅ Done!")
    input("Press Enter to exit.")

if __name__ == "__main__":
    main()
