# 🚀 How to Run the Email Processor

## Before You Start

### ⚠️ IMPORTANT: Fix OAuth Consent Screen First!

You got the "access_denied" error because you need to add yourself as a test user:

1. **Go to Google Cloud Console** → APIs & Services → **OAuth consent screen**
2. **Click "EDIT APP"** 
3. **Scroll to "Test users"** section
4. **Click "+ ADD USERS"**
5. **Add your email address** (the one you're authenticating with)
6. **Click "SAVE"**

## 🏃‍♂️ Quick Start

### 1. Run Unit Tests First
```bash
# Run all tests
python test_email_processor.py

# Or use the test runner
python run_tests.py

# Run specific test class
python run_tests.py TestCSVProcessor

# Run with coverage (if you have coverage installed)
python run_tests.py --coverage
```

### 2. Test Authentication
```bash
# Test if your credentials work
python email_processor.py --test-auth
```

### 3. Run Once (for testing)
```bash
# Process emails once and exit
python email_processor.py --once
```

### 4. Run Continuously (production)
```bash
# Run every 5 minutes continuously
python email_processor.py
```

## 📁 Required Files

Make sure you have these files in your project folder:

- ✅ `credentials.json` - Download from Google Cloud Console
- ✅ `.env` - Environment configuration (you said you have this)
- ✅ All Python files created by the script

## 🔧 What Each Command Does

### `python test_email_processor.py`
- Tests all components individually
- Verifies CSV processing logic
- Tests Gmail and Google Drive service mocking
- Shows if everything is working correctly

### `python email_processor.py --test-auth`
- Only tests authentication
- Will open browser for OAuth if needed
- Creates token files for future use
- Good for troubleshooting auth issues

### `python email_processor.py --once`
- Checks Gmail once for new emails
- Processes any CSV attachments found
- Uploads to Google Drive
- Exits after one cycle
- Perfect for testing the full workflow

### `python email_processor.py`
- Runs continuously
- Checks every 5 minutes (configurable in .env)
- Logs everything to `email_processor.log`
- Production mode

## 🐛 Troubleshooting

### If you get authentication errors:
1. Make sure you added yourself as a test user in OAuth consent screen
2. Delete token files: `token.json` and `drive_token.json`
3. Run `python email_processor.py --test-auth` again

### If you get "No module" errors:
```bash
pip install -r requirements.txt
```

### If tests fail:
- Check that all Python files are in the same directory
- Make sure you have Python 3.7+ installed

## 📊 Monitoring

- Check `email_processor.log` for detailed logs
- The script will log each step of the process
- Use `--once` mode to test without waiting

## 🎯 Expected Workflow

1. **Script monitors Gmail** for emails from `growatorchard@gmail.com` with subject "Test"
2. **Downloads CSV attachments** and uploads to Google Drive as `New Leads - Daily TMP_timestamp.csv`
3. **Processes CSV data** to transform lead information
4. **Uploads processed CSV** as `Lead_Data_timestamp.csv`
5. **Logs everything** for monitoring

Start with the tests, then test authentication, then try `--once` mode!
