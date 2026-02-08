# GemiPersona 🚀

A streamlined automation tool designed for efficiency and ease of use.

## 🛠 Prerequisites for Beginners

Before you start, your computer needs one essential piece of software. If you already have Python installed, you can skip to the **Installation** section.

1. **Install Python 3.10+**
* Download the latest version from [python.org](https://www.python.org/downloads/).
* **CRITICAL:** During installation, make sure to check the box that says **"Add Python.exe to PATH"**. If you miss this step, the installer will not work.



---

## 📥 Installation

Follow these steps to set up the environment automatically:

1. **Download the Project**
   * **Option A (Easiest):** Click the green **"Code"** button and select **"Download ZIP"**. Extract the files to a folder.
   * **Option B (For Git users):** Open your terminal or command prompt and run:
     ```bash
     git clone https://github.com/liewcc/GemiPersona.git
     ```


2. **Run the Installer**
* Double-click the **`install.bat`** file.


* A black window (Command Prompt) will appear. It will automatically:
* Create a virtual environment (`.venv`).


* Upgrade the package manager (`pip`).


* Install all necessary libraries (Streamlit, Playwright, etc.).


* Download the Chromium browser engine required for automation.






3. **Wait for Completion**
* When the window says `Installation Complete!`, press any key to close it.





---

## 🚀 How to Run

You do not need to type any code to start the application:

1. Simply double-click the **`run.bat`** file in the main folder.
2. The application will start, and your browser should open automatically to the Streamlit interface.

---

## 📁 Project Structure & Privacy

* **`.venv/`**: This folder contains all the "brains" of the project. **Do not delete or modify it manually**.

* **`install.bat`**: Run this only once during the first setup.

* **`run.bat`**: Use this every time you want to start the app.

---

## ⚠️ Troubleshooting

* **"Python not found"**: This means Python isn't installed or wasn't added to your "PATH" during installation.
---