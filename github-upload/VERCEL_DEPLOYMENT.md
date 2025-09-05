# 🚀 Deploy AI Code Reviewer Bot to Vercel

## 📋 **Prerequisites**

- Vercel account (free tier works fine)
- GitHub repository (private or public)
- Gemini API key
- GitHub App credentials

## 🔧 **Step 1: Prepare Your Repository**

### **1.1 Push to GitHub**

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit changes
git commit -m "Initial commit: AI Code Reviewer Bot"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git push -u origin main
```

### **1.2 Update Environment Variables**

Create a `.env.example` file (this will be in your repo):

```bash
# Copy the template
cp local.env .env.example

# Edit .env.example to remove sensitive data
# Keep the structure but remove actual values
```

## 🌐 **Step 2: Deploy to Vercel**

### **2.1 Connect to Vercel**

1. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/dashboard
   - Sign in with your GitHub account

2. **Import Project**
   - Click "New Project"
   - Select your GitHub repository
   - Click "Import"

### **2.2 Configure Vercel Settings**

1. **Framework Preset**: Python
2. **Root Directory**: `./` (default)
3. **Build Command**: Leave empty (Vercel will auto-detect)
4. **Output Directory**: Leave empty
5. **Install Command**: `pip install -r requirements-vercel.txt`

### **2.3 Set Environment Variables**

In Vercel dashboard, go to your project → Settings → Environment Variables:

```bash
# Required variables
GITHUB_APP_ID=your_github_app_id
GITHUB_APP_PRIVATE_KEY=your_private_key_content
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GEMINI_API_KEY=your_gemini_api_key

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
```

### **2.4 Deploy**

1. Click "Deploy"
2. Wait for deployment to complete
3. Note your Vercel URL (e.g., `https://your-app.vercel.app`)

## 🐙 **Step 3: Update GitHub App Configuration**

### **3.1 Update Webhook URL**

1. **Go to GitHub App Settings**
   - Visit: https://github.com/settings/apps
   - Select your app

2. **Update Webhook URL**
   - Change from: `http://localhost:8000/webhook/github`
   - Change to: `https://your-app.vercel.app/webhook/github`

3. **Save Changes**

### **3.2 Install on Repository**

1. **Go to App Settings**
2. **Click "Install App"**
3. **Select your repository**
4. **Install**

## 🧪 **Step 4: Test Your Deployment**

### **4.1 Test API Endpoints**

```bash
# Replace YOUR_VERCEL_URL with your actual Vercel URL
curl https://YOUR_VERCEL_URL.vercel.app/health
curl https://YOUR_VERCEL_URL.vercel.app/
```

### **4.2 Test Webhook**

1. **Create a test PR** in your repository
2. **Check Vercel logs** for webhook activity
3. **Verify the bot responds** to the PR

## 🔧 **Step 5: Configure for Production**

### **5.1 Update Database (Optional)**

For production, consider using a managed database:

```bash
# Add to Vercel environment variables
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### **5.2 Set Up Monitoring**

1. **Check Vercel Analytics**
2. **Monitor Function Logs**
3. **Set up error alerts**

## 📋 **Troubleshooting**

### **Common Issues:**

1. **"Function timeout"**
   - Vercel has a 10-second timeout for hobby plans
   - Consider upgrading to Pro plan for longer timeouts
   - Optimize your code for faster execution

2. **"Environment variables not found"**
   - Double-check variable names in Vercel dashboard
   - Ensure no extra spaces or quotes
   - Redeploy after adding variables

3. **"GitHub webhook not working"**
   - Verify webhook URL is correct
   - Check Vercel function logs
   - Ensure GitHub App has correct permissions

4. **"Database connection failed"**
   - Use a managed database service
   - Update DATABASE_URL in Vercel
   - Consider using Vercel Postgres

### **Getting Help:**

- Check Vercel function logs
- Test locally first: `python start_app.py`
- Verify GitHub App permissions
- Check webhook delivery in GitHub

## 🎉 **You're Live!**

Once deployed, your AI Code Reviewer Bot will:
- ✅ Automatically review PRs
- ✅ Post AI-generated comments
- ✅ Run static analysis
- ✅ Scale automatically with Vercel

## 📚 **Next Steps:**

1. **Monitor Performance**
   - Check Vercel analytics
   - Monitor function execution times
   - Track error rates

2. **Optimize for Production**
   - Add caching
   - Implement rate limiting
   - Set up monitoring alerts

3. **Scale Up**
   - Upgrade Vercel plan if needed
   - Add more repositories
   - Customize review rules

---

**Your AI Code Reviewer Bot is now live on Vercel! 🚀**
