# Security Fix Instructions - API Key Exposure

## ⚠️ URGENT: Your OpenRouter API key was exposed in Git history

### What Happened
The file `backend/API-KEY-EXPLAINED.md` contained your real API key and was pushed to GitHub.

### Exposed Key (DO NOT USE - ALREADY REVOKED)
```
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
```

---

## 🔴 IMMEDIATE ACTIONS REQUIRED

### Step 1: Rotate Your API Key (DO THIS NOW!)

1. **Go to OpenRouter Dashboard:**
   https://openrouter.ai/keys

2. **Delete the exposed key:**
   - Find key ending in `...ff03`
   - Click "Delete" or "Revoke"

3. **Create a new API key:**
   - Click "Create Key"
   - Copy the new key (starts with `sk-or-v1-`)

4. **Update your local `.env` file:**
   ```bash
   # Open backend/.env and replace the old key
   OPENROUTER_API_KEY=sk-or-v1-YOUR-NEW-KEY-HERE
   OPENAI_API_KEY=sk-or-v1-YOUR-NEW-KEY-HERE
   ```

### Step 2: Verify `.env` is Not Tracked

```bash
# Check if .env is in .gitignore (should show "backend/.env")
cat .gitignore | findstr ".env"

# Check if .env is tracked by git (should show nothing)
git ls-files | findstr ".env"
```

**IMPORTANT:** Never commit `.env` files!

---

## 🛡️ OPTIONAL: Remove Key from Git History

The old key is still in Git history. While it's revoked, you can clean history:

### Option A: Use BFG Repo-Cleaner (Recommended)

1. **Download BFG:**
   https://rtyley.github.io/bfg-repo-cleaner/

2. **Run BFG:**
   ```bash
   # Create a fresh clone
   cd ..
   git clone --mirror https://github.com/deencat/AI-Web-Test-v1.git

   # Remove the key from all commits
   java -jar bfg.jar --replace-text passwords.txt AI-Web-Test-v1.git

   # Push cleaned history
   cd AI-Web-Test-v1.git
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   git push --force
   ```

### Option B: Use git filter-branch (Manual)

```bash
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/API-KEY-EXPLAINED.md" \
  --prune-empty --tag-name-filter cat -- --all

git push origin --force --all
```

**⚠️ WARNING:** Force-pushing rewrites history. Coordinate with your team!

---

## ✅ Prevention Checklist

- [ ] New API key created and old key deleted
- [ ] `backend/.env` updated with new key
- [ ] `.env` is in `.gitignore` (already done ✅)
- [ ] No `.env` files tracked by git
- [ ] Documentation files don't contain real keys
- [ ] Git history cleaned (optional)

---

## 📋 Files That Should NEVER Be Committed

These are already in `.gitignore`:
- `backend/.env`
- `.env`
- `.env.local`
- Any file with real API keys

---

## 🔍 How to Check for Exposed Keys

```bash
# Search for potential keys in tracked files
git grep -n "sk-or-v1-" 

# Search in all history
git log -p -S "sk-or-v1-" --all
```

---

## 📚 Resources

- **OpenRouter Dashboard:** https://openrouter.ai/keys
- **BFG Repo Cleaner:** https://rtyley.github.io/bfg-repo-cleaner/
- **GitHub Secret Scanning:** https://docs.github.com/en/code-security/secret-scanning
- **Git History Cleaning:** https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository

---

## ✅ Current Status

- [x] API key removed from `backend/API-KEY-EXPLAINED.md`
- [x] Sanitized version pushed to GitHub
- [ ] **YOU MUST:** Rotate API key on OpenRouter
- [ ] **OPTIONAL:** Clean Git history

---

**NEXT STEP:** Go to https://openrouter.ai/keys and rotate your key NOW!
