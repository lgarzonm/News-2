# Helicap News — Implementation Plan
**Version:** 1.0  
**Author:** Laura Garzon  
**Date:** March 2026

---

## Before You Open Claude Code — Checklist

Complete these steps first. They take ~10 minutes total.

- [ ] **NewsAPI key** → Sign up free at [newsapi.org](https://newsapi.org) → go to your account dashboard → copy your API key
- [ ] **Anthropic API key** → Go to [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key → copy it
- [ ] **Python 3.11+** installed on your machine (`python --version` to check)
- [ ] **Node.js 18+** installed (required by Claude Code) — [nodejs.org](https://nodejs.org)
- [ ] **Claude Code installed** → run in terminal: `npm install -g @anthropic/claude-code`
- [ ] **A folder created** on your desktop or preferred location, e.g. `helicap-news/`
- [ ] **Both files saved** into that folder: `technical_brief.md` and this file

---

## Phase 1 — Project Setup (Claude Code)

### Step 1: Open Claude Code in your project folder
```bash
cd ~/Desktop/helicap-news
claude
```
You should see the Claude Code prompt appear in your terminal.

---

### Step 2: Tell Claude Code to scaffold the project

Paste this message exactly:

```
I want to build a Streamlit app called "Helicap News". 
Please read the technical brief below and scaffold the full project structure 
with all files: app.py, news_fetcher.py, llm_processor.py, config.py, 
requirements.txt, and .streamlit/secrets.toml (with placeholder values).

[PASTE THE FULL CONTENT OF technical_brief.md HERE]
```

**What Claude Code will create:**
```
helicap-news/
├── app.py
├── news_fetcher.py
├── llm_processor.py
├── config.py
├── requirements.txt
└── .streamlit/
    └── secrets.toml
```

Wait for Claude Code to finish before moving on.

---

### Step 3: Fill in your secrets

Open `.streamlit/secrets.toml` in any text editor and replace the placeholders:

```toml
NEWSAPI_KEY = "paste_your_newsapi_key_here"
ANTHROPIC_API_KEY = "paste_your_anthropic_key_here"
```

> ⚠️ Never commit this file to GitHub. It is already in `.gitignore` — confirm this with Claude Code if unsure.

---

## Phase 2 — Install & Run Locally

### Step 4: Install dependencies

In your terminal (inside the `helicap-news/` folder):

```bash
pip install -r requirements.txt
```

If you get permission errors, use:
```bash
pip install -r requirements.txt --user
```

---

### Step 5: Run the app locally

```bash
streamlit run app.py
```

Your browser should open automatically at `http://localhost:8501`.

**Expected result:** The Helicap News UI loads with a navy header, category tabs, and a "Refresh News" button. No articles yet — that happens when you click the button.

---

### Step 6: Test the first run

1. Click **"Refresh News"** in the UI
2. Wait ~15–30 seconds (NewsAPI + Claude Haiku calls)
3. Check that:
   - [ ] Articles appear in each category
   - [ ] Each card shows: headline, source, timestamp, summary, sentiment tag, and a working link
   - [ ] The "Download CSV" button appears and works
   - [ ] The timestamp in the header updates to the current time

---

## Phase 3 — Debugging (If Needed)

Use Claude Code to fix issues as they come up. Here are the most likely ones and the exact prompts to use:

| Issue | Prompt to give Claude Code |
|---|---|
| App crashes on load | `"The app is crashing with this error: [paste error]. Please fix it."` |
| No articles showing for a category | `"The [category name] category is returning 0 results. Review the keyword list in config.py and broaden the search query logic in news_fetcher.py."` |
| Articles older than 24h appearing | `"Some articles are outside the 24h window. Tighten the publishedAt filter in news_fetcher.py and make sure the from= parameter is being passed correctly to NewsAPI."` |
| LLM call failing | `"The Claude API call in llm_processor.py is failing with: [paste error]. Please debug and fix."` |
| UI looks off / styling broken | `"The CSS styling is not applying correctly. Review the st.markdown style block in app.py and fix the navy/white/blue palette."` |
| CSV download not working | `"The CSV download button is not generating the file correctly. Fix the download_button logic in app.py."` |

---

## Phase 4 — Polish Pass

Once the app is working correctly, do one final polish pass with Claude Code:

### Step 7: UI refinement prompt

```
The app is working. Please do a polish pass on app.py:
1. Make sure the header "Helicap News" is prominent in navy (#0D1F3C)
2. Confirm the footer reads: "Curated by AI · Designed by Laura Garzon · 2026"
3. Make article cards visually clean with light blue (#EBF2FF) backgrounds
4. Sentiment tags should be color-coded: gold for Positive, red for Negative, grey for Neutral
5. The Refresh button should be blue (#1A56DB) and full-width or prominently placed
6. Add a subtle loading spinner while articles are being fetched
```

### Step 8: Final checks before deployment

- [ ] Click every article link — confirm they open real articles
- [ ] Run the app twice in a row — confirm session caching works (second run is instant)
- [ ] Download the CSV — open it and confirm all columns are populated
- [ ] Check the terminal for any error messages or warnings

---

## Phase 5 — Deploy to Streamlit Community Cloud (Free)

### Step 9: Push to GitHub

If you don't have a GitHub account: [github.com](https://github.com) → sign up (free).

In your terminal:
```bash
git init
git add .
git commit -m "Initial commit — Helicap News v1.0"
```

Create a new **private** repository on GitHub (do not initialize with README), then:
```bash
git remote add origin https://github.com/YOUR_USERNAME/helicap-news.git
git branch -M main
git push -u origin main
```

> ⚠️ Confirm `.streamlit/secrets.toml` is in `.gitignore` before pushing. Run `git status` — it should NOT appear in the list of files being committed.

---

### Step 10: Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
2. Click **"New app"**
3. Select your `helicap-news` repository
4. Set **Main file path** to: `app.py`
5. Click **"Advanced settings"** → **Secrets** → paste your secrets:
   ```toml
   NEWSAPI_KEY = "your_key_here"
   ANTHROPIC_API_KEY = "your_key_here"
   ```
6. Click **"Deploy"**

Streamlit will build and deploy the app. This takes 2–5 minutes. You'll get a public URL like:
```
https://helicap-news-XXXXXX.streamlit.app
```

Share this URL with your team. Done. ✅

---

## Phase 6 — Sharing & Maintenance

### Access control (optional)
Streamlit Community Cloud free tier apps are public by default. To restrict access to your team:
- Upgrade to **Streamlit for Teams** (paid), OR
- Add a simple password gate in `app.py` — ask Claude Code:
  ```
  "Add a simple password protection screen to app.py. 
   The password should be stored in secrets.toml as APP_PASSWORD."
  ```

### Updating the app later
To make changes after deployment:
1. Edit files locally
2. Test with `streamlit run app.py`
3. Push to GitHub: `git add . && git commit -m "update" && git push`
4. Streamlit Cloud auto-redeploys within ~1 minute

### If NewsAPI free tier runs out (100 req/day)
Ask Claude Code:
```
"Switch the news fetcher to use GNews API instead of NewsAPI. 
 The GNews docs are at https://gnews.io/docs. Keep the same interface."
```

---

## Summary Timeline

| Phase | Estimated Time |
|---|---|
| Pre-setup (accounts + folder) | 10 min |
| Claude Code scaffolding | 5–10 min |
| Install + first local run | 5 min |
| Testing + debugging | 15–30 min |
| UI polish pass | 10 min |
| GitHub push + Streamlit deploy | 10 min |
| **Total** | **~1 hour** |

---

## Quick Reference — Key Commands

```bash
# Start Claude Code
claude

# Run app locally
streamlit run app.py

# Install dependencies
pip install -r requirements.txt

# Push updates to GitHub
git add . && git commit -m "your message" && git push
```

---

## Quick Reference — Key URLs

| Resource | URL |
|---|---|
| NewsAPI dashboard | [newsapi.org/account](https://newsapi.org/account) |
| Anthropic console | [console.anthropic.com](https://console.anthropic.com) |
| Streamlit deploy | [share.streamlit.io](https://share.streamlit.io) |
| Your app (after deploy) | `https://helicap-news-XXXXXX.streamlit.app` |

---

*End of Implementation Plan — Helicap News v1.0*
