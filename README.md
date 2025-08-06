# APK Patch Toolkit

## 📦 Description

A beginner-friendly Python tool for **automating the APK patching pipeline** — from pulling APKs off an Android device, unpacking, modifying, rebuilding, signing, and installing them — all through a guided command-line interface.

This script is useful for Android enthusiasts, modders, researchers, or developers who want to reverse engineer APK files to analyze, modify, or clean up applications, such as removing ads, customizing behavior, or conducting educational research.

---

## 🎯 Why I Built This

I was inspired by the need to simplify the tedious and repetitive tasks involved in modifying Android apps. Pulling an APK, unpacking, editing, resigning, and reinstalling it manually every time can be overwhelming, especially for beginners.

This project automates the full workflow and includes built-in support for:

-   Pulling APKs from your Android device using `adb`
-   Unpacking using `apktool`
-   Rebuilding and signing using `uber-apk-signer`
-   Optional keyword search in decompiled source
-   Installing the final APK back to your device

It provides a terminal-based, interactive menu that walks you through each step.

Think of it as your **offline alternative** to GUI tools like APK Easy Tool — but fully scriptable and customizable.

---

## 🛠 Features

-   ✅ Check and install required dependencies automatically
-   ✅ Pull APK from a connected Android device
-   ✅ Select APK manually from your local drive
-   ✅ Unpack APK using apktool
-   ✅ Rebuild APK after editing
-   ✅ Sign APKs with Uber APK Signer
-   ✅ Install signed APKs back to your device via ADB
-   ✅ Search for keywords in the decompiled app folder
-   ✅ Clean up all previous build files

---

## 📁 File Structure

After running the script, all files are managed under:

~/Desktop/Apk_Patch/
│
├── dependencies/ # All tools and JARs downloaded automatically
├── base/ # Decompiled APK contents
├── signed/ # Final signed APKs ready to install
└── \*\_patched.apk # Intermediate rebuilt APK

---

## 🔧 Setup Instructions

### 1. Prerequisites

-   Windows OS (Tested)
-   Python 3.6+
-   Java (for apktool and uber-apk-signer)
-   ADB (Android Debug Bridge)

> ✅ No need to pre-install apktool, bundletool, etc. — this script downloads all required tools for you.

---

### 2. How to Use

1. **Download** or clone the repo:

```bash
`git clone https://github.com/HighLord/Apk-Patch-Toolkit.git`
`cd Apk-Patch-Toolkit`

Run the script

`python PatchApk.py`

follow the menu

[+] 1. Check & Install Dependencies
[+] 2. Select/Import Apk to Patch
[+] 3. Unpack APK
[+] 4. Pack APK
[+] 5. Sign APK
[+] 6. Install Signed APK via ADB
[+] 7. Clear old APK files
[+] 8. Search for keyword(s) in base folder

Each step includes prompts and instructions, even letting you search for specific code or phrases (like ads, firebase, or billing) in the decompiled APK.

📦 What the Code Does
check_dependency()
Downloads all required binaries such as apktool, uber-apk-signer, bundletool, and platform-tools if not found. Also guides you to download JADX for visual exploration of code.

select_Apk()
Lets you either:

Pull APKs directly from your connected phone using adb, or

Select APK/XAPK files manually from any location on your PC

unpack_Apk()
Uses apktool to decompile the APK so you can edit its smali, XML, or asset files.

pack_Apk()
Rebuilds the decompiled app folder into an unsigned APK using apktool.

sign_Apk()
Uses uber-apk-signer to sign the APK for installation. Automatically handles file renaming and cleanup.

install_Apk()
Installs the final APK to your Android device via ADB.

search()
Lets you search for comma-separated phrases in the decompiled folder. Useful for quickly locating code or tracking features like ads or tracking libraries.

clear_old_apk_files()
Deletes everything except the dependencies folder to start fresh.

🎓 Real World Example / Inspiration
Inspired by this article:
Reverse [engineering YI Home app to remove ads]
(https://scognito.wordpress.com/2025/05/20/reverse-engineering-yi-home-app-to-remove-ads/)

That blog walks through a manual workflow to remove advertisements from an Android camera app. My script automates that process and provides a repeatable setup for future mods.

```

🧠 Tips for Beginners
Enable USB Debugging on your phone (found in Developer Options)

If your device isn’t detected, check if adb is working or if you have authorized your computer

After unpacking, you can edit .smali, res/values/strings.xml, or AndroidManifest.xml

Use search() to locate keywords like admob, firebase, analytics, or license

🤝 Contribution
Pull requests are welcome! If you find bugs or want to suggest improvements, feel free to open an issue.

🙌 Acknowledgments
iBotPeaches/apktool

patrickfav/uber-apk-signer

Google's bundletool

Skylot/jadx
