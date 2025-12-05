# 🔧 Quick Fix for Test Generation Error

## ❌ Problem:
```
INFO:     127.0.0.1:61880 - "POST /api/v1/tests/generate HTTP/1.1" 500 Internal Server Error
```

## ✅ Solution Applied:

Changed the AI model from `qwen/qwen-2.5-7b-instruct` to `deepseek/deepseek-chat` in `backend/.env`

## 🔄 Next Steps:

**You MUST restart the backend server for this to work:**

### Option 1: Stop and Restart (Recommended)
1. Find the terminal running the backend server
2. Press `Ctrl+C` to stop it
3. Run: `python run.py` to restart

### Option 2: Use the restart script (if available)
```powershell
cd backend
python run.py
```

---

## 📋 Then Test Again:

1. **Open browser**: `http://localhost:5173/tests`

2. **Paste this test requirement**:
   ```
   Test the Three.com.hk 5G Broadband subscription at https://web.three.com.hk/5gbroadband/plan-hsbc-en.html
   
   Select 30 months contract, verify $135/month pricing, click Subscribe Now, handle popup, proceed through checkout, verify payment ($100 SIM card fee), login with pmo.andrewchan+010@gmail.com, select service date, complete subscription.
   
   Expected: Full flow completes successfully.
   ```

3. **Click "Generate Test Cases"**

4. **Should work now!** ✅

---

## 🤔 Why Did This Happen?

The `qwen/qwen-2.5-7b-instruct` model may have:
- Been temporarily unavailable
- Had rate limiting issues
- Returned an invalid response format

`deepseek/deepseek-chat` is more reliable and is also FREE! 🎉

---

## 🚨 If It Still Doesn't Work:

Check the backend terminal output for the actual error message. The 500 error means there's an exception being thrown in the backend.
