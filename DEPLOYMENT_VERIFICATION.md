# Authentication Flow - Deployment & Verification Guide

## ✅ What Was Fixed

### Backend (backend/api.py)
1. **CORS Configuration** - Now reads from environment, with dev mode auto-allowlist
2. **Signup Endpoint** - Added request validation logging and error handling
3. **Login Endpoint** - Added user lookup and password verification logging
4. **Error Logging** - All auth operations now log to help with debugging

### Frontend (frontend/src/api.js)
1. **New Functions Added**:
   - `signup(name, email, password)` - Handles user registration
   - `login(email, password)` - Handles user authentication
   - `logout(sessionToken)` - Handles user logout
   - `verifySession(sessionToken)` - Verifies valid session

### Frontend (frontend/src/App.jsx)
1. **Updated Imports** - Now imports auth functions from api.js
2. **Centralized API Layer** - All auth calls go through api.js functions
3. **Better Error Handling** - Consistent error messages across auth flows

## 📋 Deployment Status

**Commit**: `1ec7378` pushed to `origin/main`
**Status**: ⏳ Auto-deployment to Render started

### Monitor Deployment
1. Go to [Render Dashboard](https://dashboard.render.com)
2. View live logs for your `claimflow-api` service
3. Look for:
   - ✅ Build started
   - ✅ Dependencies installed
   - ✅ Application started on port 8000
   - ✅ "CORS allowed origins: [...]" in logs

## 🧪 Local Testing (Before Production)

### Prerequisites
```bash
# Backend
python -m pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Test Backend Locally
```bash
# Terminal 1: Start backend
python -m uvicorn backend.api:app --reload

# Terminal 2: Check health endpoint
curl -i http://localhost:8000/health

# Expected response:
# HTTP/1.1 200 OK
# {"status":"ok","env":"development","vector_backend":"chroma_local","warnings":[]}
```

### Test Frontend Locally
```bash
# Terminal 1: Backend still running
python -m uvicorn backend.api:app --reload

# Terminal 2: Start frontend
cd frontend
npm run dev

# Terminal 3: Open browser
# http://localhost:5173
```

### Manual Auth Flow Test
1. **Signup Test**:
   - Click "Sign Up" button on landing page
   - Name: "Test User"
   - Email: "test@example.com" (must be valid email format)
   - Password: "secure123" (6+ characters)
   - Click "Create Account"
   - ✅ Should see "Account created successfully"
   - ✅ Should be logged in and view chat interface
   - ✅ Check browser console - no CORS errors

2. **Login Test**:
   - Click Logout
   - Click "Login" button
   - Email: "test@example.com"
   - Password: "secure123"
   - Click "Sign In"
   - ✅ Should see "Login successful"
   - ✅ Should access chat interface
   - ✅ No CORS errors in console

3. **Session Persistence**:
   - After login, refresh page
   - ✅ Should still be logged in
   - ✅ Check localStorage - should have `sessionToken`

## 🚀 Production Testing (After Render Deployment)

### Wait for Deployment
1. Check Render dashboard for deployment completion
2. When complete, deployment URL will be active
3. Watch logs for:
   ```
   "CORS allowed origins: ['https://claimflow-ai-bot.vercel.app', ...]"
   ```

### Test Health Endpoint
```bash
# Should return 200 OK
curl -i https://claimflow-api.onrender.com/health
```

### Test from Vercel Frontend
1. Go to https://claimflow-ai-bot.vercel.app
2. Click "Sign Up"
3. Fill in:
   - Name: "Production Test"
   - Email: "prodtest@yourdomain.com"
   - Password: "test1234"
4. Click "Create Account"
5. ✅ Should see success
6. ✅ Check browser DevTools (F12) → Console:
   - Should NOT see "CORS" errors
   - Should NOT see "failed to fetch"

### Test Signup Flow
```
Expected behavior:
1. POST https://claimflow-api.onrender.com/auth/signup
   - Status: 200 OK
   - Body: {
       "success": true,
       "message": "Account created successfully",
       "user_email": "...",
       "user_name": "...",
       "session_token": "..."
     }
2. Frontend stores session_token in localStorage
3. Redirects to chat view
```

### Test Login Flow
```
Expected behavior:
1. POST https://claimflow-api.onrender.com/auth/login
   - Status: 200 OK
   - Body: same as signup response
2. Frontend redirects to chat view
3. Can send messages in authenticated mode
```

## 🔍 Debugging: Browser Console Errors

### CORS Error
```
Access to XMLHttpRequest at 'https://claimflow-api.onrender.com/auth/signup'
from origin 'https://claimflow-ai-bot.vercel.app' has been blocked by CORS policy
```
**Solution**: Check Render `ALLOWED_ORIGINS` environment variable includes your Vercel domain

### Network Error: Failed to Fetch
```
TypeError: Failed to fetch
Could not connect to server. Please ensure backend is running at https://claimflow-api.onrender.com
```
**Solution**: Verify Render deployment is running - check deployment logs

### 400 Bad Request
```json
{
  "detail": "... validation error ..."
}
```
**Likely causes**:
- Email format invalid (must have @domain)
- Password too short (need 6+ characters)
- Name too short (need 2+ characters)

**Solution**: Check form inputs and error message in UI

### 401 Unauthorized
```json
{
  "detail": "Invalid email or password"
}
```
**Causes**:
- Wrong email or password on login
- Email not registered yet

**Solution**: Verify credentials or sign up first

### 500 Internal Server Error
```json
{
  "detail": "Login failed: ..."
}
```
**Check Render logs for**:
- Database connection issues
- Password hashing errors
- Unexpected exceptions

## 📊 Backend Logs to Monitor

In Render dashboard, watch for these log entries:

**Startup**:
```
CORS allowed origins: ['https://claimflow-api.onrender.com', ...]
APP_ENV: production
```

**Signup**:
```
Signup attempt for email: test@example.com
User created successfully: test@example.com
```

**Login Success**:
```
Login attempt for email: test@example.com
User logged in successfully: test@example.com
```

**Login Failure**:
```
Login attempt for email: test@example.com
Login failed: User not found - test@example.com
```

## ✅ Verification Checklist

- [ ] Render deployment completed successfully
- [ ] Health endpoint returns 200 OK
- [ ] CORS logs show correct allowed origins
- [ ] Can signup from Vercel frontend
- [ ] Can login from Vercel frontend
- [ ] Session token stored in localStorage
- [ ] Can chat when authenticated
- [ ] No CORS errors in browser console
- [ ] Backend logs show auth attempts

## 🚨 Rollback Plan

If authentication is broken in production:

1. Check environment variables:
   ```
   - DATABASE_URL is set and valid
   - ALLOWED_ORIGINS includes your Vercel domain
   - APP_ENV should be "production"
   ```

2. Check Render logs for error messages

3. If critical, you can revert:
   ```bash
   git revert 1ec7378
   git push origin HEAD:main
   # Render will auto-deploy previous version
   ```

## 📞 Support

If you encounter issues:

1. Check [AUTH_FIX_SUMMARY.md](AUTH_FIX_SUMMARY.md) for detailed changes
2. Review Render deployment logs
3. Check browser DevTools console for exact error
4. Verify environment variables on Render match .env.example
5. Test backend locally if possible to isolate the issue
