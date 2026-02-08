![System Diagnosis Page](https://github.com/liewcc/GemiPersona/blob/main/img/1.png)

# GemiPersona 🚀

**The World's First Free Gemini Batch Image Generator with Automatic Prompt Embedding**

> 🎯 **Unique Feature**: Automatically embed AI prompts into image metadata while batch-generating images through Google Gemini without API costs

---

## 🌟 What Makes GemiPersona Different?

### ✨ Revolutionary Features You Won't Find Anywhere Else

#### 🏆 Automatic Prompt Metadata Embedding (EXCLUSIVE)
- **World-First Technology**: GemiPersona is the ONLY tool that automatically writes your prompts into the metadata of generated images
- **Non-Destructive Tagging**: Prompts are embedded without modifying the actual image content
- **Future-Proof**: Easily track which prompt created which image
- **Batch Comparison Ready**: Compare generated images with their exact prompts side-by-side

#### 🤖 Hands-Free Batch Automation
- **Fire and Forget**: Queue multiple prompts and let the software work while you do other tasks
- **Continuous Operation**: Automatically cycles through prompts without manual intervention
- **No Manual Clicking**: Say goodbye to repetitive send-button clicking
- **Unattended Execution**: Leave your computer, come back to finished batches

#### 💰 Free Forever (No API Required)
- **Zero Cost**: Works with free Gemini accounts - no API keys needed
- **Unlimited Batches**: No rate limiting from paid tiers
- **Cost-Effective Analysis**: Test hundreds of prompts without spending a dime
- **Perfect for Experimentation**: Ideal for prompt engineers and AI enthusiasts on a budget

#### 📊 Systematic Prompt Testing
- **A/B Testing Made Easy**: Compare multiple prompts and their results
- **Organized Workflow**: Batch processing with systematic naming
- **Effect Analysis**: Easily evaluate how different prompts affect image generation
- **Data-Driven Insights**: Track what works and what doesn't

---

## 💡 Use Cases

### For Content Creators
Generate hundreds of variations of a design concept overnight without touching your keyboard

### For Prompt Engineers
Test and refine prompts at scale to discover the perfect wording for your needs

### For AI Researchers
Conduct systematic studies on how prompt variations affect image quality and style

### For Busy Professionals
Set up batch jobs and focus on other work while GemiPersona handles the heavy lifting

### For Budget-Conscious Users
Leverage free Gemini tier to its fullest potential without API costs

---

## ✨ Core Features

### 🎨 Image Generation & Management
- **Batch Image Generation**: Generate dozens of images in a single batch
- **Metadata Embedding**: Automatically store prompts in image metadata
- **Flexible Output**: Customize save locations and file naming
- **Image Organization**: Auto-numbered files with custom prefixes
- **Format Support**: Full support for standard image formats

### 🔄 Intelligent Automation
- **Queue Management**: Add multiple prompts and let the system process them
- **Playwright Automation**: Reliable browser-based automation
- **Stealth Operation**: Anti-detection technology for stable performance
- **Error Recovery**: Automatic retry on failures
- **State Tracking**: Remember your last session and progress

### 🎯 Prompt Management
- **Prompt History**: Automatic tracking of all prompts used
- **Reusable Templates**: Save and reuse successful prompts
- **Batch Configuration**: Set up complete workflows in JSON
- **Smart Scheduling**: Control execution speed and timing

### 🌐 User-Friendly Interface
- **Web-Based Dashboard**: Clean Streamlit interface accessible from any browser
- **Real-Time Progress**: Monitor automation as it happens
- **Debug Console**: Detailed logging for troubleshooting
- **Responsive Design**: Works on desktop and tablet devices
- **No Technical Skills Required**: Designed for non-programmers

### ⚙️ Advanced Customization
- **CSS Selector Configuration**: Adapt to Gemini UI changes
- **Headless Mode**: Run in background for maximum efficiency
- **Custom Naming Schemes**: Organize outputs your way
- **Flexible Configuration**: Easy JSON-based settings
- **Version Management**: Track engine updates

---
## 🚦 How It Works – Complete Setup & Operation Guide

Before you can start batch prompt generation, you **must follow this workflow exactly**. This ensures everything works perfectly before you attempt large batches.

---

### Phase 1: Initialize the Engine and Login

**What to do:**
1. Open GemiPersona (double-click `run.bat`)
2. Look at the left sidebar and navigate to the **System Diagnosis** page
3. Find the **"Start Engine"** button and click it
4. Wait a few seconds until you see the message: `Engine Started Successfully` ✅

**Why this matters:** The automation engine is the "brain" that controls the browser. It must be running before anything else can work.

Once you've confirmed this setting, click **Launch Browser (Visual)** and GemiPersona will automatically launch a browser window. Now you need to log in to your Google Gemini account just like you normally would. Complete any 2FA verification or security checks. Once you're logged in and seeing the Gemini interface, your session is now active and ready for automation.

try to play around and generate a few pictures before you close the windows (without log out). You can choose to close the browser windows as usual or use **Close Browser (Gracefully)** to turn off the browser.

**Important:** You only need to log in this once per session. Your login session will be remembered and reused for all subsequent automation steps.

---

### Phase 2: Learn How Automation Works (This is crucial!)

You cannot effectively troubleshoot problems later if you don't understand how the automation works RIGHT NOW. So this phase is absolutely non-negotiable.

**What to do:**
1. Stay on the **System Diagnosis** page
2. click **Launch Browser (Visual)** and observe browser windows
3. Scroll down and fill in any text in **Edit Last Prompt" and dill in full path of the file to upload (optional)
4. Look for the **"Upload Files Test"** button and click it
5. **Very important:** Watch the browser window carefully as it runs through the automation

**What you're watching for:**
- See how fast the automation clicks (it's quick!)
- See which UI elements it interacts with
- Notice where on the screen the actions happen
- Watch how long each step takes
- Observe any pauses while it's waiting for Gemini to respond

Don't just let this run in the background! This is your chance to understand the system. You're building a mental map of how GemiPersona controls the browser.

**After the first test is done:**
Now click the **"Upload Test Redo"** button. This runs the same automation sequence again. Watch it a second time. The repetition helps you understand the pattern better. You'll start to predict what comes next. This confidence is important for troubleshooting later when something goes wrong.

**How long should this take?** Each test typically runs for 30-90 seconds depending on how fast Gemini responds. Don't rush through this - take your time.

---

### Phase 3: Switch to Headless Mode (Faster, but invisible)

Now that you understand what the automation does, it's time to make it faster and more efficient.

**What to do:**
1. Close the browser window (or let it close if it finishes automatically)
2. Click **Launch browser (Headless)**
3. The engine keeps running in the background - you'll still see it in your terminal/command window
4. Click **Sign In Status** and observe **Engine Live Logs** indicate the the browser is log in.
5. Repeat **"Upload Files Test"** button and **"Upload Test Redo"**. Observe **Engine Live Logs** and wait for the messages indicated that pictures download had been completed.
   
**What headless mode does:** Your browser no longer appears on screen. The automation still happens, but invisibly. This makes everything 30-50% faster because there's no window rendering overhead.

**Why switch now?** You've already learned what happens in headed mode. Now you can safely use the faster headless mode. If something breaks, you already know what SHOULD be happening, which makes debugging easier.

**Now watch the "Engine Live Logs" section very carefully.** This is where the system tells you what's happening behind the scenes.

**What you're looking for:**
You want to see these messages:
- ✅ `[SUCCESS] Authentication verified`
- ✅ `[INFO] Browser ready for automation`
- ✅ `[INFO] Session active`

**What you DON'T want to see:**
- ❌ `[ERROR] Authentication failed`
- ❌ `[ERROR] Session expired`
- ❌ `[ERROR] Browser not responding`

**If you see success messages:** Congratulations! Your headless automation is working perfectly. The system can interact with Gemini invisibly and reliably. You're ready to proceed.

**If you see error messages:** Do not proceed to batch generation yet. Go back to Phase 1, switch back to headed mode (`"headless": false`), log in again, run the Upload tests again, and then try headless mode again. The issue is usually a lost authentication session.

---

### Phase 4: You're Ready for Batch Generation!

If you've made it through all four phases with no errors, you're officially ready.

**What to do:**
1. Navigate to the **HOME** page (click the link in the left sidebar)
2. You'll see the main batch generation interface
3. Start with something simple: enter a single test prompt in the text field
4. Something like: "a red car on a sunny day" or "a cozy coffee shop"
5. Click the **"Generate Single Image"** button (NOT a full batch yet)
6. Wait and watch as GemiPersona:
   - Enters your prompt into the Gemini chat box
   - Clicks the send button
   - Waits for Gemini to process
   - Detects when the image has been generated
   - Downloads the image
   - **Automatically embeds your original prompt into the image's metadata** ✨
   - Saves the image with an organized filename

**Verify the metadata was actually embedded:**
1. Find your generated image in the output folder
2. Right-click the image file
3. Select **Properties** (on Windows)
4. Go to the **Details** tab
5. Scroll down through all the properties
6. You should see your prompt text embedded in there! 🎯

**If this works,** you now fully understand the complete workflow. You're ready for batch generation with confidence.

**What happens next?**
Once you're comfortable with single-image generation:
1. Enter Prompt
2. Uoload Images
3. Click "Start Loop"
4. Walk away! ☕ Go do something else for few tens minutes
5. Come back to find all your images with their prompts embedded in the metadata
6. Now you can compare different prompts and their results side-by-side

---

## Why This Specific Workflow?

You might be wondering: "Why do I have to do all this? Can't I just jump straight to batch generation?"

The answer is: **No, and here's why:**

- **Phase 1-2 (Headed mode + observation):** You learn exactly how the system works. When something breaks later, you'll recognize the problem immediately.

- **Phase 3-4 (Headless verification):** You confirm that the invisible automation actually works. Many people skip this and then blame the software when headless mode doesn't work - but the issue was usually their own system.

- **Phase 5 (Single image test):** You verify the entire pipeline end-to-end: automation + image generation + metadata embedding. This proves everything is connected correctly.

This workflow takes about 30-45 minutes for first-time users, but it saves you HOURS of frustration later when you understand exactly what went wrong if something breaks.

---
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
