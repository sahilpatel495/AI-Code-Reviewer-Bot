# 🚀 Deploy AI Code Reviewer Bot to Render

## 📋 **Prerequisites**

- Render account (free tier works fine)
- GitHub repository (private or public)
- Gemini API key
- GitHub App credentials

## 🔧 **Step 1: Prepare Your Repository**

### **1.1 Push to GitHub**

```bash
# Add all files
git add .

# Commit changes
git commit -m "Prepare for Render deployment"

# Push to GitHub
git push origin main
```

## 🌐 **Step 2: Deploy to Render**

### **2.1 Connect to Render**

1. **Go to Render Dashboard**

   - Visit: https://dashboard.render.com
   - Sign in with your GitHub account

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `sahilpatel495/AI-Code-Reviewer-Bot`

### **2.2 Configure Render Settings**

**Basic Settings:**

- **Name**: `ai-code-reviewer-bot`
- **Environment**: `Python 3`
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Runtime**: `Python 3.11`

**Build & Deploy:**

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`

### **2.3 Set Environment Variables**

In Render dashboard, go to your service → Environment:

```bash
# Required variables
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_APP_ID=your_github_app_id_here
GITHUB_APP_PRIVATE_KEY=your_private_key_content_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# Optional variables
APP_NAME=AI Code Reviewer Bot
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
MAX_COMMENTS_PER_PR=20
REVIEW_TIMEOUT_SECONDS=300
ENABLE_PYTHON_ANALYZERS=true
ENABLE_JS_ANALYZERS=true
ENABLE_JAVA_ANALYZERS=true
ENABLE_SQL_ANALYZERS=true
WEBHOOK_TIMEOUT_SECONDS=30

# Database (optional - will use SQLite if not provided)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Redis (optional - will use in-memory if not provided)
REDIS_URL=redis://user:pass@host:port/db
```

### **2.4 Deploy**

1. Click "Create Web Service"
2. Wait for deployment to complete
3. Note your Render URL (e.g., `https://ai-code-reviewer-bot.onrender.com`)

## 🐙 **Step 3: Update GitHub App Configuration**

### **3.1 Update Webhook URL**

1. **Go to GitHub App Settings**

   - Visit: https://github.com/settings/apps
   - Select your app

2. **Update Webhook URL**

   - Change from: `http://localhost:8000/webhook/github`
   - Change to: `https://your-app.onrender.com/webhook/github`

3. **Save Changes**

### **3.2 Install on Repository**

1. **Go to App Settings**
2. **Click "Install App"**
3. **Select your repository**
4. **Install**

## 🧪 **Step 4: Test Your Deployment**

### **4.1 Test API Endpoints**

```bash
# Replace YOUR_RENDER_URL with your actual Render URL
curl https://YOUR_RENDER_URL.onrender.com/health
curl https://YOUR_RENDER_URL.onrender.com/
```

### **4.2 Test Webhook**

1. **Create a test PR** in your repository
2. **Check Render logs** for webhook activity
3. **Verify the bot responds** to the PR

## 🔧 **Step 5: Configure for Production**

### **5.1 Add Database (Optional)**

For production, consider using Render Postgres:

1. **Create Postgres Database**

   - Go to Render Dashboard
   - Click "New +" → "PostgreSQL"
   - Choose plan and create

2. **Update Environment Variables**
   - Copy the database URL from Render
   - Add `DATABASE_URL` to your web service

### **5.2 Add Redis (Optional)**

For background tasks, consider using Render Redis:

1. **Create Redis Instance**

   - Go to Render Dashboard
   - Click "New +" → "Redis"
   - Choose plan and create

2. **Update Environment Variables**
   - Copy the Redis URL from Render
   - Add `REDIS_URL` to your web service

## 📋 **Troubleshooting**

### **Common Issues:**

1. **"Build failed"**

   - Check that all dependencies are in `requirements.txt`
   - Ensure Python version is 3.11

2. **"Environment variables not found"**

   - Double-check variable names in Render dashboard
   - Ensure no extra spaces or quotes
   - Redeploy after adding variables

3. **"GitHub webhook not working"**

   - Verify webhook URL is correct
   - Check Render service logs
   - Ensure GitHub App has correct permissions

4. **"Database connection failed"**
   - Use Render Postgres for production
   - Update DATABASE_URL in environment variables

### **Getting Help:**

- Check Render service logs
- Test locally first: `python start_app.py`
- Verify GitHub App permissions
- Check webhook delivery in GitHub

## 🎉 **You're Live!**

Once deployed, your AI Code Reviewer Bot will:

- ✅ Automatically review PRs
- ✅ Post AI-generated comments
- ✅ Run static analysis
- ✅ Scale automatically with Render

## 📚 **Next Steps:**

1. **Monitor Performance**

   - Check Render metrics
   - Monitor service logs
   - Track error rates

2. **Optimize for Production**

   - Add caching
   - Implement rate limiting
   - Set up monitoring alerts

3. **Scale Up**
   - Upgrade Render plan if needed
   - Add more repositories
   - Customize review rules

---

**Your AI Code Reviewer Bot is now live on Render! 🚀**
