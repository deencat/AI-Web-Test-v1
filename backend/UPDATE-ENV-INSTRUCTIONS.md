# How to Update Your .env File for Model Selection

## 📝 **Quick Instructions**

1. **Open your `.env` file:**
   ```powershell
   cd backend
   notepad .env
   ```

2. **Add this line** (if not already present):
   ```env
   OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
   ```

3. **Save and close** the file

4. **Restart the server** (if running):
   ```powershell
   # Press Ctrl+C to stop the server
   .\run_server.ps1
   ```

---

## 🎯 **What This Does**

- Sets the **default model** to Meta Llama 3.1 8B (FREE)
- You can change this to any model from `MODEL-SELECTION-GUIDE.md`
- The model is used for all test generation unless overridden in code

---

## 🔄 **To Change Models**

Just update the line in `.env`:

```env
# Use free model (default)
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free

# Or use Claude for better quality (costs money)
# OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Or use a different free model
# OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
```

**Note:** Uncomment (remove `#`) the model you want to use, and comment out (add `#`) the others.

---

## ✅ **Verify It's Working**

Run the test script:
```powershell
.\venv\Scripts\python.exe test_openrouter.py
```

You should see:
```
Model configured: meta-llama/llama-3.1-8b-instruct:free
[Test 1] Testing basic connection... ✅ SUCCESS
```

---

## 📚 **More Information**

See `MODEL-SELECTION-GUIDE.md` for:
- Full list of available models
- Cost comparisons
- Performance benchmarks
- Recommendations by use case

