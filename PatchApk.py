# apk_automation.py
import time
import subprocess
import os
import string
import shutil
import urllib.request
import sys
import webbrowser
import zipfile
import re
import json

# Global variable to store path to Apk_Patch
APK_PATCH_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Apk_Patch")
dependencies_dir = os.path.join(APK_PATCH_DIR, "dependencies")
LOG_FILE = os.path.join(APK_PATCH_DIR, "modification_log.json")

# Ensure the directories exist
os.makedirs(dependencies_dir, exist_ok=True)   

def PORE():
    print("\n[⏸] Press ENTER to Restart or anykey to Exit...")
    message = input()
    if (message):
        exit(1)
    main()
    PORE()
    
def download_with_progress(url, dest):
    def show_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = int(downloaded * 100 / total_size) if total_size > 0 else 0
        bar = f"[{'#' * (percent // 2):<50}] {percent}%"
        sys.stdout.write('\r' + bar)
        sys.stdout.flush()
    urllib.request.urlretrieve(url, dest, reporthook=show_progress)
    print() 

def run_adb_command(args):
    adb_commands = [
        ["adb"] + args,  # system PATH
        [os.path.join(dependencies_dir, "platform-tools", "adb.exe")] + args  # local
    ]

    for adb_cmd in adb_commands:
        try:
            result = subprocess.run(
                adb_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    return False

def check_dependency():

    def ensure_jar_present(name, url, target_name, min_size=None):
        for file in os.listdir(dependencies_dir):
            file_lower = file.lower()
            if target_name in file_lower:
                jar_path = os.path.join(dependencies_dir, file)
                if not min_size or os.path.getsize(jar_path) >= min_size:
                    print(f"[+] {name} found: {file}")
                    return jar_path
        print(f"\n[!] {name} not found. Downloading...\n")

        _, url_ext = os.path.splitext(url)
        if url_ext:
            target_name_with_ext = target_name if target_name.lower().endswith(url_ext.lower()) else f"{target_name}{url_ext}"
        else:
            target_name_with_ext = target_name

        dest_path = os.path.join(dependencies_dir, target_name_with_ext)

        try:
            download_with_progress(url, dest_path)
            print(f"[✔] Downloaded {name} to:\n    {dest_path}")
            return dest_path
        except Exception as e:
            print(f"[✖] Failed to download {name}: {e}")
            return None


    print("\n[+] Checking for dependencies...")


    # === ADB Platform Tools ===
    result = run_adb_command(["devices"])
    if result:
        print("[+] ADB found in PATH.")
    else:
        zip_path = ensure_jar_present(
        name="adb",
        url="https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
        target_name="platform-tools",
        min_size=6_000_000
    )
        if zip_path:
            print(f"[+] Extracting ADB to {dependencies_dir}...")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(dependencies_dir)
                print(f"[✔] Extracted ADB to: {dependencies_dir}")
            except Exception as e:
                print(f"[✖] Failed to unzip ADB: {e}")


    # === apktool ===
    ensure_jar_present(
        name="apktool",
        url="https://github.com/iBotPeaches/Apktool/releases/download/v2.12.0/apktool_2.12.0.jar",
        target_name="apktool",
        min_size=25_000_000
    )

    # === uber-apk-signer ===
    ensure_jar_present(
        name="uber-apk-signer",
        url="https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar",
        target_name="ubersigner",
        min_size=3_000_000
    )

    # === bundletool ===
    ensure_jar_present(
        name="bundletool",
        url="https://github.com/google/bundletool/releases/download/1.18.1/bundletool-all-1.18.1.jar",
        target_name="bundletool",
        min_size=28_000_000
    )

    # === JADX CHECK ===
    jadx_found = False
    for file in os.listdir(dependencies_dir):
        if "jadx" in file.lower():
            jadx_found = True
            print(f"[+] JADX found: {file}")
            break
    
    if not jadx_found:
        print("\n[!] JADX not found.")
        print("    You can download it from:\n    https://github.com/skylot/jadx/releases")
        choice = input("[?] Do you want to open the download page in your browser? (y/n): ").strip().lower()
        if choice == 'y':
            webbrowser.open("https://github.com/skylot/jadx/releases")

def select_Apk():

    def list_drives():
        # Windows-specific drive listing
        drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives

    def list_apk_items(path):
        # Show only folders and .apk/.xapk files
        try:
            entries = os.listdir(path)
            entries = [e for e in entries if os.path.isdir(os.path.join(path, e)) or e.lower().endswith(('.apk', '.xapk'))]
            entries.sort()
            return entries
        except Exception as e:
            print(f"\n[!] Error accessing folder: {e}")
            return []
        
    def pull_apk_from_device():
        try:
            result = run_adb_command(["devices"])
            devices_output = result.stdout.strip().splitlines()

             # Filter devices (ignore the first line: "List of devices attached")
            connected_devices = [
                line for line in devices_output[1:]
                if "\tdevice" in line and not any(state in line for state in ["unauthorized", "offline", "missing"])
            ]

            if not connected_devices:
                print("\n[!] No authorized devices found or device is offline.")
                print("    → Make sure your phone is connected and USB debugging is enabled.")
                return
            print(f"\n[+] {len(connected_devices)} device(s) found.")

            # Prompt for package search query
            query = input("\nEnter part of the app name or package to search for (e.g., whatsapp, face, store): ").strip()
            print(f"\n[+] Searching for installed apps matching: '{query}'")
            pkg_result = run_adb_command(["shell", "pm", "list", "packages"])

            packages = [line.replace("package:", "").strip() for line in pkg_result.stdout.splitlines()]
            matched_packages = [pkg for pkg in packages if query.lower() in pkg.lower()]

            if not matched_packages:
                print("\n[!] No packages found matching your query.")
                pull_apk_from_device()
                return

            print("\nMatched Packages:")
            for idx, pkg in enumerate(matched_packages, start=1):
                print(f"{idx}. {pkg}")

            choice = input("\nEnter the number of the app to pull (or press Enter to cancel): ").strip()
            if not choice.isdigit() or int(choice) < 1 or int(choice) > len(matched_packages):
                print("[!] Invalid selection or canceled.")
                return

            selected_package = matched_packages[int(choice) - 1]
            print(f"\n[+] You selected: {selected_package}")

            # Get APK path on device
            print(f"[+] Getting APK path for: {selected_package}")
            apk_path_result = run_adb_command(["shell", "pm", "path", selected_package])
            apk_path_lines = apk_path_result.stdout.strip().splitlines()
            if not apk_path_lines:
                print("\n[!] Could not find APK path for the selected package.")
                return

            apk_paths = [line.replace("package:", "").strip() for line in apk_path_lines]

            print(f"\n[+] Found {len(apk_paths)} APK file(s):")
            for path in apk_paths:
                print(f"    → {path}")

             # Create Apk_Patch directory on Desktop
            os.makedirs(APK_PATCH_DIR, exist_ok=True)

            # Pull each APK
            for remote_path in apk_paths:
                original_filename = os.path.basename(remote_path)
                local_apk_path = os.path.join(APK_PATCH_DIR, original_filename)

                print(f"\n[+] Pulling: {remote_path}")
                print(f"    → Saving to: {local_apk_path}")
                run_adb_command(["pull", remote_path, local_apk_path])

            print(f"\n[✔] APK(s) pulled successfully to: {APK_PATCH_DIR}")

        except FileNotFoundError:
            print("\n[!] 'adb' not found. Make sure it's installed and added to your system PATH.")

        except subprocess.CalledProcessError as e:
            print("\n[!] ADB command failed:", e)
            return

    def select_apk_from_drive():
        print("\n[+] Scanning for drives...")
        drives = list_drives()

        if not drives:
            print("\n[!] No drives found.")
            return None

        # Step 1: Choose Drive
        while True:
            print("\nAvailable Drives:\n")
            for i, d in enumerate(drives, 1):
                print(f"{i}. {d}")
            print("Or paste a full path to a file or folder:")
            choice = input("Select a drive by number (or press Enter to cancel): ").strip()

            if not choice:
                print("\n[!] Cancelled.")
                return None

            # Handle manual path
            if not choice.isdigit():
                path = os.path.abspath(choice)
                if not os.path.exists(path):
                    print("\n[!] Path not found.")
                    continue
                if os.path.isfile(path) and path.lower().endswith(('.apk', '.xapk')):
                    print(f"\n[✔] APK file selected: {path}")
                    return path
                elif os.path.isdir(path):
                    current_path = path
                    break
                else:
                    print("\n[!] Invalid file type. Only APK/XAPK files or folders allowed.")
                    continue

            # Handle numbered drive selection
            if choice.isdigit():
                idx = int(choice)
                if idx < 1 or idx > len(drives):
                    print("\n[!] Invalid drive number.")
                    continue
                current_path = drives[idx - 1]
                break

        # Step 2: Navigate folders and select APK
        while True:
            print(f"\n[📂] Current path: {current_path}")

            items = list_apk_items(current_path)
            if not items:
                print("\n[!] No APKs or folders here.")
                parent = os.path.dirname(current_path)
                if parent != current_path:
                    current_path = parent
                continue

            print("\nSelect an item:\n")
            for i, item in enumerate(items, 1):
                full_path = os.path.join(current_path, item)
                tag = "[DIR]" if os.path.isdir(full_path) else "[APK]"
                print(f"{i}. {tag}  {item}")

            print("0. 🔙 Go up one folder")
            print("💡 You can also paste a full path to a folder or APK file")
            choice = input("\nEnter your choice: \n").strip()

            # Path input again
            if not choice.isdigit():
                path = os.path.abspath(choice)
                if not os.path.exists(path):
                    print("[!] Path not found.")
                    continue
                if os.path.isfile(path) and path.lower().endswith(('.apk', '.xapk')):
                    print(f"\n[✔] APK file selected: {path}")
                    return path
                elif os.path.isdir(path):
                    current_path = path
                    continue
                else:
                    print("\n[!] Invalid file type.")
                    continue

            if choice == "0":
                parent = os.path.dirname(current_path)
                if parent == current_path:
                    print("\n[!] You're already at the top level.")
                else:
                    current_path = parent
                continue

            if not choice.isdigit():
                print("\n[!] Invalid selection.")
                continue

            idx = int(choice)
            if idx < 1 or idx > len(items):
                print("\n[!] Invalid item number.")
                continue

            selected_item = items[int(choice) - 1]
            selected_path = os.path.join(current_path, selected_item)

            if os.path.isdir(selected_path):
                current_path = selected_path
                continue
            else:
                print(f"\n[✔] APK file selected: {selected_path}")

                destination_path = os.path.join(APK_PATCH_DIR, "base.apk")

                try:
                    shutil.copy2(selected_path, destination_path)
                    print(f"\n[✔] Copied APK to Apk_Patch folder:\n    {destination_path}")
                    return
                except Exception as e:
                    print(f"\n[!] Failed to copy APK: {e}")

    print("\nDo you have the app installed on your phone or do you have the APK files on your PC?")
    print("1. App is installed on the phone (pull from device)")
    print("2. APK files are on my PC")
    print("0. Back to Mainmenu")

    choice = input("\nEnter 1 or 2: ").strip()

    if choice == "1":
        pull_apk_from_device()
    elif choice == "2":
        select_apk_from_drive()
    else:
        print("\nInvalid choice!")
        main()
        return

def unpack_Apk():
    print("\n[+] Scanning for APKs in Apk_Patch directory...")

    if not os.path.exists(APK_PATCH_DIR):
        print("\n[!] Apk_Patch folder doesn't exist yet.")
        return
    
    apk_files = [
        f for f in os.listdir(APK_PATCH_DIR)
        if os.path.isfile(os.path.join(APK_PATCH_DIR, f)) and f.lower().endswith((".apk", ".xapk"))
    ]

    if not apk_files:
        print("\n[!] No APK files found in Apk_Patch.")
        return
    
    print("\nSelect an APK to unpack:\n")
    for idx, apk in enumerate(apk_files, 1):
        print(f"{idx}. {apk}")
    choice = input("\nEnter the number of the APK to unpack (or press Enter to cancel): ").strip()

    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(apk_files):
        print("\n[!] Invalid selection or canceled.")
        return

    selected_apk = apk_files[int(choice) - 1]
    apk_path = os.path.join(APK_PATCH_DIR, selected_apk)
    unpack_folder_name = os.path.splitext(selected_apk)[0]
    unpack_dir = os.path.join(APK_PATCH_DIR, unpack_folder_name)

    print(f"\n[+] Unpacking {selected_apk} to:\n    {unpack_dir}")

    # Create unpack folder
    os.makedirs(unpack_dir, exist_ok=True)

    try:
        subprocess.run(["apktool", "d", apk_path, "-o", unpack_dir, "-f"], check=True)
        print(f"\n[✔] APK successfully unpacked into:\n    {unpack_dir}")
    except FileNotFoundError:
        print("\n[!] 'apktool' not found in system PATH. Trying local dependency...")

        # Try using the jar file from the dependencies folder
        dependencies_dir = os.path.join(APK_PATCH_DIR, "dependencies")
        apktool_jar = None
        for file in os.listdir(dependencies_dir):
            if "apktool" in file.lower() and file.lower().endswith(".jar"):
                apktool_jar = os.path.join(dependencies_dir, file)
                break

        if apktool_jar:
            try:
                subprocess.run(["java", "-jar", apktool_jar, "d", apk_path, "-o", unpack_dir, "-f"], check=True)
                print(f"\n[✔] APK successfully unpacked using local apktool into:\n    {unpack_dir}")
            except subprocess.CalledProcessError as e:
                print(f"\n[!] Failed to unpack APK with local apktool: {e}")
        else:
            print("\n[✖] apktool not found in dependencies folder.")
            print("    → Please run the dependency check from the main menu.")
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Failed to unpack APK: {e}")

def pack_Apk():
    print("\n[+] Packing APK...")

    # Set paths
    dependencies_dir = os.path.join(APK_PATCH_DIR, "dependencies")
    apktool_path = os.path.join(dependencies_dir, "apktool.jar")

    if not os.path.exists(apktool_path):
        print("\n[!] apktool.jar not found in dependencies.")
        return

      # Look for directories in APK_PATCH_DIR excluding 'dependencies'
    subdirs = [
        os.path.join(APK_PATCH_DIR, d)
        for d in os.listdir(APK_PATCH_DIR)
        if os.path.isdir(os.path.join(APK_PATCH_DIR, d)) and d.lower() != "dependencies" and d.lower() != "signed"
    ]

    if not subdirs:
        print("[!] No unpacked APK folder found to rebuild.")
        return
    
    if len(subdirs) > 1:
        print("[!] Multiple folders found. Only one unpacked APK folder should exist.")
        for i, folder in enumerate(subdirs, 1):
            print(f"    {i}. {folder}")
        print("    → Delete extra folders or clarify intent.")
        return
    
    src_folder = subdirs[0]
    folder_name = os.path.basename(src_folder.rstrip(os.sep))
    output_apk_path = os.path.join(APK_PATCH_DIR, f"{folder_name}_patched.apk")

    print(f"\n[+] Building APK from: {src_folder}")

    try:
        result = subprocess.run(
            ["java", "-jar", apktool_path, "b", src_folder, "-o", output_apk_path],
            check=True
        )
        print(f"[✔] APK successfully rebuilt to:\n    {output_apk_path}")

    except subprocess.CalledProcessError as e:
        print("\n[!] Failed to build APK.\n")
        print(e.stderr)

def sign_Apk():
    print("\n[+] Preparing APKs for bulk signing...")

    dependencies_dir = os.path.join(APK_PATCH_DIR, "dependencies")
    signer_path = os.path.join(dependencies_dir, "ubersigner.jar")
    signed_dir = os.path.join(APK_PATCH_DIR, "signed")

    if not os.path.exists(signer_path):
        print("\n[!] ubersigner.jar not found in dependencies.")
        return
    
    # Create the signed output directory
    os.makedirs(signed_dir, exist_ok=True)

    # Step 1: Move *_patched.apk to signed/
    patched_apks = [f for f in os.listdir(APK_PATCH_DIR) if f.endswith("_patched.apk")]
    for patched_file in patched_apks:
        src = os.path.join(APK_PATCH_DIR, patched_file)
        dst = os.path.join(signed_dir, patched_file)
        shutil.move(src, dst)
        print(f"[→] Moved patched APK: {patched_file} → signed/")

     # Step 2: Copy other APKs (excluding base.apk and *_patched.apk)
    other_apks = [
        f for f in os.listdir(APK_PATCH_DIR)
        if f.endswith(".apk") and not f.lower().startswith("base") and not f.endswith("_patched.apk")
    ]
    for apk in other_apks:
        src = os.path.join(APK_PATCH_DIR, apk)
        dst = os.path.join(signed_dir, apk)
        shutil.copy2(src, dst)
        print(f"[+] Copied APK: {apk} → signed/")

    # Step 3: Rename *_patched.apk to base.apk
    for f in os.listdir(signed_dir):
        if f.endswith("_patched.apk"):
            old_path = os.path.join(signed_dir, f)
            new_path = os.path.join(signed_dir, "base.apk")
            os.rename(old_path, new_path)
            print(f"[✎] Renamed: {f} → base.apk")

    # Step 4: Sign all APKs in signed/
    print("\n[🔐] Signing all APKs in 'signed' folder...")
    try:
        subprocess.run(
            ["java", "-jar", signer_path, "-a", "signed", "--allowResign"],
            cwd=APK_PATCH_DIR,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("[!] Signing failed.")
        return
    
    # Cleanup: Delete all .idsig files
    idsig_files = [f for f in os.listdir(signed_dir) if f.endswith(".idsig")]
    for f in idsig_files:
        os.remove(os.path.join(signed_dir, f))
        print(f"[🗑] Deleted .idsig: {f}")

    # Step 6: Delete every .apk in signed that doesn't contain 'debugSigned'
    non_signed_apks = [
        f for f in os.listdir(signed_dir)
        if f.endswith(".apk") and "debugSigned" not in f
    ]
    for f in non_signed_apks:
        os.remove(os.path.join(signed_dir, f))
        print(f"[🗑] Deleted unsigned APK: {f}")

    print("\n[✔] All APKs signed successfully and saved to:")
    print(f"    {signed_dir}")

def install_Apk():
    print("\n[+] Installing APK(s) to device...")

    signed_dir = os.path.join(APK_PATCH_DIR, "signed")

    if not os.path.exists(signed_dir):
        print("\n[!] Signed folder not found.")
        return

    apk_files = [
        f for f in os.listdir(signed_dir)
        if f.endswith(".apk")
    ]

    if not apk_files:
        print("[!] No APK files found in signed folder.")
        return

    # Sort to ensure base.apk is first (important for split APKs)
    apk_files.sort(key=lambda x: (x.lower() != "base.apk", x.lower()))

    apk_paths = [os.path.join(signed_dir, apk) for apk in apk_files]

    try:
        if len(apk_paths) == 1:
            # Just one file, use normal install
            result = subprocess.run(
                ["adb", "install", apk_paths[0]],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"[✔] Install Success:\n{result.stdout}")
        else:
            # Multiple APKs, use install-multiple
            result = subprocess.run(
                ["adb", "install-multiple"] + apk_paths,
                check=True,
                capture_output=True,
                text=True
            )
            print(f"[✔] Install Success:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"[!] Install Failed:\n{e.stderr}")

def clear_old_apk_files():
    print("\n[?] Do you want to clear all old APK files and folders except 'dependencies'?")
    choice = input("    (y/N): ").strip().lower()

    if choice != 'y':
        print("[-] Skipping cleanup.")
        return

    print("[!] Cleaning up old APK files...")

    for item in os.listdir(APK_PATCH_DIR):
        item_path = os.path.join(APK_PATCH_DIR, item)

        if item == "dependencies":
            continue  # skip the dependencies folder

        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"[🗑] Deleted folder: {item}")
            else:
                os.remove(item_path)
                print(f"[🗑] Deleted file: {item}")
        except Exception as e:
            print(f"[!] Error deleting {item}: {e}")

    print("[✔] Cleanup complete. Only 'dependencies' folder remains.")

def search():
    print("\n=== Keyword Search in Base Folder ===\n")

    base_folder = os.path.join(APK_PATCH_DIR, "base")

    if not os.path.exists(base_folder):
        print(f"[!] Base folder not found at: {base_folder}")
        return
    
    keywords_input = input("Enter keyword(s) or sentence(s) separated by |: ").strip()
    if not keywords_input:
        print("[!] No keywords provided.")
        return

    keywords = [' '.join(kw.strip().lower().split()) for kw in keywords_input.split("|") if kw.strip()]

    matched_results = []
    all_files = []
    
    # Gather all files to process
    for root, _, files in os.walk(base_folder):
        for file in files:
            all_files.append((root, file))

    total_files = len(all_files)
    if total_files == 0:
        print("[!] No files found in base folder.")
        return

    # Start search
    print("[*] Scanning files...\n")
    for idx, (root, file) in enumerate(all_files):
        file_path = os.path.join(root, file)
        folder_name = os.path.relpath(root, base_folder)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, start=1):
                    lower_line = line.lower()

                    for keyword in keywords:
                        words = keyword.split()
                        if all(word in lower_line for word in words):
                            matched_results.append(
                                f"{len(matched_results)+1}. {keyword} found in line {line_num} on {file} under {folder_name}"
                            )
                            break  # Stop after first match per line
        except Exception:
            pass  # Ignore unreadable files

        # Progress bar update
        percent = int(((idx + 1) / total_files) * 100)
        sys.stdout.write(f"\rProgress: {percent}%")
        sys.stdout.flush()

    print("\n\n=== Matches Found ===")
    if matched_results:
        for match in matched_results:
            print(match)
    else:
        print("No matches found.")

    print("\n[✓] Search complete.")
    print(f"Total folders scanned: {len(next(os.walk(base_folder))[1])}")
    print(f"Total files scanned: {total_files}")

def delete_or_replace_keywords():
    print("\n=== Keyword Delete or Replace in Base Folder ===\n")
    print("Do you want to:")
    print("1. Delete files containing keyword(s) in filename")
    print("2. Replace keyword(s) inside text files")
    print("0. Back to Mainmenu")

    choice = input("\nEnter 1, 2, or 0: ").strip()
    if choice == "0":
        return
    
    base_folder = os.path.join(APK_PATCH_DIR, "base")
    if not os.path.exists(base_folder):
        print(f"[!] Base folder not found at: {base_folder}")
        return
    
    keywords_input = input("Enter keyword(s) separated by '|': ").strip().lower()
    if not keywords_input:
        print("[!] No keywords provided.")
        return
    keywords = [kw.strip() for kw in keywords_input.split("|") if kw.strip()]

    # Load or initialize modification log
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            mod_log = json.load(f)
    else:
        mod_log = {"deleted_files": [], "replaced_lines": []}

    if choice == "1":
        deleted_files = 0
        print("\n[*] Searching for files to delete...\n")

        # Ask upfront if user wants to delete all matches without further prompts
        delete_all = False
        delete_all_input = input("Type 'yes' to delete ALL matched files without asking, or press Enter to confirm each: ").strip().lower()
        if delete_all_input == "yes":
            delete_all = True

        for root, _, files in os.walk(base_folder):
            for file in files:
                lower_file = file.lower()
                if any(kw in lower_file for kw in keywords):
                    file_path = os.path.join(root, file)
                    print(f"\nFile matched for deletion: {file_path}")
                    if delete_all:
                        confirm = "y"
                    else:
                        confirm = input("Delete this file? (y/n): ").strip().lower()

                    if confirm == "y":
                        try:
                            os.remove(file_path)
                            deleted_files += 1
                            print(f"[Deleted] {file_path}")
                            # Log deleted file
                            mod_log["deleted_files"].append({"file_path": file_path})
                        except Exception as e:
                            print(f"[!] Failed to delete: {file_path} - {e}")

        print(f"\n[✓] Deleted {deleted_files} files matching keyword(s).")


    elif choice == "2":
        replaced_files = 0
        print("\n[*] Searching for keywords inside files for replacement...\n")
        replace_with = input("Enter replacement text: ").strip()

        # Ask upfront if user wants to replace all matches without further prompts
        replace_all = False
        replace_all_input = input("Type 'yes' to replace ALL matched keywords without asking, or press Enter to confirm each: ").strip().lower()
        if replace_all_input == "yes":
            replace_all = True

        import re  # import once, can move outside function if you want

        for root, _, files in os.walk(base_folder):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except Exception:
                    # skip unreadable files (binary, etc)
                    continue

                changed = False
                for i, line in enumerate(lines):
                    lower_line = line.lower()
                    for kw in keywords:
                        if kw in lower_line:
                            print(f"\nFile: {file_path}")
                            print(f"Line {i+1}: {line.strip()}")
                            if replace_all:
                                confirm = "y"
                            else:
                                confirm = input(f"Replace '{kw}' with '{replace_with}' in this line? (y/n): ").strip().lower()

                            if confirm == "y":
                                # Save original before replacement for log
                                mod_log["replaced_lines"].append({
                                    "file_path": file_path,
                                    "line_number": i+1,
                                    "original_line": line.rstrip('\n'),
                                    "keyword": kw,
                                    "replacement": replace_with
                                })
                                # Case-insensitive replace
                                pattern = re.compile(re.escape(kw), re.IGNORECASE)
                                lines[i] = pattern.sub(replace_with, line)
                                changed = True
                            break  # Only first keyword per line for simplicity

                if changed:
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.writelines(lines)
                        replaced_files += 1
                        print(f"[Replaced in] {file_path}")
                    except Exception as e:
                        print(f"[!] Failed to write changes to {file_path} - {e}")

        print(f"\n[✓] Replaced keywords in {replaced_files} files.")

    else:
        print("\nInvalid choice!")
        return
    
    # Save modification log after changes
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(mod_log, f, indent=4)

    print(f"\n[✓] Modification log saved to {LOG_FILE}\n")

def revert_modifications():
    print("\n=== Revert Deleted/Replaced Modifications ===\n")

    if not os.path.exists(LOG_FILE):
        print("[!] No modification log found.")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        mod_log = json.load(f)

    # Revert replaced lines
    replaced = mod_log.get("replaced_lines", [])
    if replaced:
        print(f"Reverting {len(replaced)} replaced lines...\n")
        # Group replacements by file for efficiency
        from collections import defaultdict
        file_changes = defaultdict(list)
        for entry in replaced:
            file_changes[entry["file_path"]].append(entry)

        for file_path, changes in file_changes.items():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception as e:
                print(f"[!] Could not read {file_path}: {e}")
                continue

            changed = False
            for change in changes:
                line_idx = change["line_number"] - 1
                if 0 <= line_idx < len(lines):
                    print(f"Reverting line {change['line_number']} in {file_path}")
                    print(f"Current: {lines[line_idx].strip()}")
                    print(f"Original: {change['original_line']}")
                    lines[line_idx] = change["original_line"] + "\n"
                    changed = True

            if changed:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    print(f"[Reverted] {file_path}")
                except Exception as e:
                    print(f"[!] Failed to write {file_path}: {e}")

    else:
        print("No replaced lines to revert.")

    # Deleted files cannot be restored automatically — just list them
    deleted = mod_log.get("deleted_files", [])
    if deleted:
        print(f"\nNote: {len(deleted)} files were deleted and cannot be restored automatically.")
        print("List of deleted files:")
        for entry in deleted:
            print(f"- {entry['file_path']}")
    else:
        print("No deleted files logged.")

    print("\n[✓] Revert operation completed.")




def main():
    print("\n=== APK Patcher ===\n")
    print("[+] 1. Check & Install Dependicies")
    print("[+] 2. Select/Import Apk to Patch")
    print("[+] 3. Unpack APK")
    print("[+] 4. Pack APK")
    print("[+] 5. Sign APK")
    print("[+] 6. Install Signed APK via ADB")
    print("[+] 7. Clear old APK files")
    print("[+] 8. Search for keyword(s) in base folder")
    print("[+] 9. Delete and replace files/words matching keyword(s) in base folder")
    print("[+] 10. Revert deleted/replaced modifications")
    print("[+] 0. Back to Mainmenu")

    choice = input("\nEnter the number of your choice: ").strip()

    if choice == "1":
        check_dependency()
    elif choice == "2":
        select_Apk()
    elif choice == "3":
        unpack_Apk()
    elif choice == "4":
        pack_Apk()
    elif choice == "5":
        sign_Apk()
    elif choice == "6":
        install_Apk()
    elif choice == "7":
        clear_old_apk_files()
    elif choice == "8":
        search()
    elif choice == "9":
        delete_or_replace_keywords()
    elif choice == "10":
        revert_modifications()
    else:
        return
    
if __name__ == "__main__":
    main()
    PORE()
