# Gmail App Password Setup for Password Reset Emails

## Current Issue
The Gmail SMTP authentication is failing because:
1. The `EMAIL_HOST_PASSWORD` environment variable is not set
2. Gmail requires an App Password (not your regular password) for SMTP access

## Solution: Set up Gmail App Password

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", enable **2-Step Verification**
3. Follow the setup process

### Step 2: Generate App Password
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click **App passwords**
3. Select **Mail** as the app
4. Select **Other** as the device and enter "Django App"
5. Click **Generate**
6. Copy the 16-character password (it looks like: `abcd efgh ijkl mnop`)

### Step 3: Set Environment Variable

#### Option 1: Create .env file (Recommended)
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file and add your app password:
   ```
   EMAIL_HOST_PASSWORD=abcdefghijklmnop
   ```
   (Remove spaces from the app password)

#### Option 2: Set in system environment
**Windows:**
```cmd
set EMAIL_HOST_PASSWORD=abcdefghijklmnop
```

**Linux/Mac:**
```bash
export EMAIL_HOST_PASSWORD=abcdefghijklmnop
```

### Step 4: Enable SMTP in Django
In `settings.py`, uncomment the SMTP backend:
```python
# Switch from console to SMTP
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
```

### Step 5: Test Email
Run the test command:
```bash
python manage.py test_email
```

## Current Status (Console Backend)
✅ Password reset system works with console output  
✅ Styled emails are ready  
✅ All templates are in English  
⏳ Waiting for Gmail App Password to enable email sending  

## Alternative Email Providers
If Gmail doesn't work, consider:
- **SendGrid** (free tier available)
- **Mailgun** (free tier available)
- **Amazon SES** (pay as you go)

## Security Notes
- Never commit your App Password to Git
- Use environment variables or .env files
- The .env file is already in .gitignore
- App Passwords are more secure than regular passwords