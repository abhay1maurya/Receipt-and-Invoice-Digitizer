# Project Setup (Windows)

This guide uses Miniconda and Python 3.13.11.

## 0) Clone the repo and open the folder
```bash
git clone https://github.com/abhay1maurya/Receipt-and-Invoice-Digitizer
cd Receipt-and-Invoice-Digitizer
```

## 1) Install Conda (Miniconda)
1. Download Miniconda for Windows (64-bit) from:
   https://docs.conda.io/en/latest/miniconda.html
2. Run the installer.
3. During install, you may check "Add Miniconda to my PATH".
   If you skip this, you can use the Anaconda Prompt instead.

## 2) Create and activate the environment (Python 3.13.11)
Open Anaconda Prompt (or CMD/PowerShell if conda is in PATH) from the project root:

```bash
conda create -n receipt-invoice python=3.13.11
conda activate receipt-invoice
```

Verify:
```bash
python --version
```

## 3) Install Python requirements
From the project root:

```bash
pip install -r requirements.txt
```

## 4) Install Poppler (required by pdf2image)
Poppler is a system dependency. Use one of these options:


### Option A: Manual install
1. Download a Windows Poppler build, for example:
   https://github.com/oschwartz10612/poppler-windows/releases
2. Extract it, e.g. to:
   `C:\Program Files\poppler-xx\`
3. The binaries are in the `bin` folder, e.g.:
   `C:\Program Files\poppler-xx\Library\bin`

## 5) Add Poppler to PATH
Add the Poppler `bin` folder to your system PATH:
1. Open Start Menu and search "Environment Variables".
2. Open "Edit the system environment variables".
3. Click "Environment Variables".
4. Under "System variables", select `Path` and click "Edit".
5. Add the Poppler `bin` folder path.
6. Click OK on all dialogs and restart your terminal.

Verify Poppler is available:
```bash
pdfinfo -v
```

## 6) Run the environment later
Activate the environment any time with:
```bash
conda activate receipt-invoice
```

Deactivate when done:
```bash
conda deactivate
```

## 7) Start the app
From the project root:

```bash
streamlit run app.py
```
