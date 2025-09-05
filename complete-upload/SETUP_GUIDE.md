# 🚀 AI Code Reviewer Bot - Complete Setup Guide

## ✅ **Current Status: Ready to Configure!**

Your AI Code Reviewer Bot is **95% ready**! The core system is working perfectly:

- ✅ All Python packages installed
- ✅ Database created and working
- ✅ FastAPI application ready
- ✅ Static analyzers configured
- ⚠️ Just need to configure API keys

## 🔑 **Step 1: Configure API Keys**

### **Option A: Interactive Configuration (Recommended)**

```bash
python configure_keys.py
```

### **Option B: Manual Configuration**

Edit the `.env` file and replace these values:

```bash
# Get your Gemini API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Get your GitHub App credentials from: https://github.com/settings/apps
GITHUB_APP_ID=your_actual_github_app_id_here
GITHUB_APP_PRIVATE_KEY=your_actual_private_key_content_here
GITHUB_WEBHOOK_SECRET=your_actual_webhook_secret_here
```

## 🐙 **Step 2: Create GitHub App**

1. **Go to GitHub Settings**

   - Visit: https://github.com/settings/apps
   - Click "New GitHub App"

2. **Configure the App**

   - **App name**: `AI Code Reviewer Bot`
   - **Homepage URL**: `https://your-domain.com` (or any URL)
   - **Webhook URL**: `http://localhost:8000/webhook/github` (for testing)
   - **Webhook secret**: Generate a random string (save this!)

3. **Set Permissions**

   - **Read**: `contents`, `metadata`, `pull requests`
   - **Write**: `pull request comments`, `commit statuses`, `checks`

4. **Get Credentials**
   - Copy the **App ID**
   - Generate and download the **Private key**
   - Copy the **Webhook secret**

## 🤖 **Step 3: Get Gemini API Key**

1. **Visit Google AI Studio**

   - Go to: https://makersuite.google.com/app/apikey
   - Sign in with your Google account

2. **Create API Key**
   - Click "Create API Key"
   - Copy the generated key

## 🧪 **Step 4: Test Your Setup**

```bash
# Test the configuration
python test_setup.py

# Quick functionality test
python quick_test.py

# Start the application
python start_app.py
```

## 🌐 **Step 5: Test the API**

Once the server is running, test these endpoints:

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# API documentation
# Open in browser: http://localhost:8000/docs
```

## 🔧 **Step 6: Test with a Real PR (Optional)**

1. **Install the GitHub App** on a test repository
2. **Create a test PR** with some code changes
3. **Check the webhook** - the bot should automatically review the PR

## 📋 **Troubleshooting**

### **Common Issues:**

1. **"Invalid GitHub App private key"**

   - Make sure the private key is properly formatted
   - Include the full key content including `-----BEGIN` and `-----END`

2. **"Gemini API key not configured"**

   - Get your API key from Google AI Studio
   - Update the `.env` file

3. **"Database connection failed"**

   - The SQLite database should be created automatically
   - Check if the `db` directory exists

4. **"Port 8000 already in use"**
   - Change the port in `start_app.py`
   - Or stop other services using port 8000

### **Getting Help:**

- Check the logs in the `logs/` directory
- Run `python test_setup.py` for detailed diagnostics
- Check the API documentation at `http://localhost:8000/docs`

## 🎉 **You're Ready!**

Once you've configured the API keys, your AI Code Reviewer Bot will be fully functional and ready to review pull requests automatically!

## 📚 **Next Steps:**

1. **Deploy to Production** (optional)

   - Use Docker: `docker-compose up -d`
   - Deploy to cloud platforms (AWS, Google Cloud, Railway)

2. **Customize Configuration**

   - Edit `.ai-reviewer.yml` in your repositories
   - Adjust review settings and focus areas

3. **Monitor and Improve**
   - Check the `/stats` endpoint for usage metrics
   - Review feedback to improve the bot's performance

---

**Happy coding! 🚀**
