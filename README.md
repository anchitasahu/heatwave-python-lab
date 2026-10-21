# Climate Lab

Interactive climate dashboard backed by the supplied CSV datasets and six Python experiments.

## Project layout

```text
.
├── app.py                 # Flask entrypoint for Vercel
├── requirements.txt       # Python runtime dependencies
├── vercel.json            # Vercel function data-file configuration
├── climatelabweb/
│   ├── app.py             # Local API and dashboard server
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── datasets/              # Source CSV files used by the dashboard
└── exps/                  # Standalone Python experiments
```

## Run locally

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python climatelabweb/app.py
```

Open <http://127.0.0.1:8000>.

## Deploy to Vercel

Deploy from this repository's root directory so Vercel can find `app.py`, `requirements.txt`, `vercel.json`, `climatelabweb/`, and `datasets/`.

With the Vercel CLI:

```bash
npm install --global vercel
vercel link
vercel
vercel --prod
```

When linking, select or create the intended Vercel project. If importing through the Vercel dashboard, set the Root Directory to `.` and let it detect the Flask app. Do not set `climatelabweb/` as the project root; the backend and datasets live beside it.

## Push to a new GitHub repository

Create an empty repository on GitHub, then from this project root point `origin` at its URL:

```bash
git remote set-url origin https://github.com/USER/NEW-REPOSITORY.git
git add -A
git status
git commit -m "Prepare climate lab for deployment"
git push -u origin main
```

Review `git status` before committing so local-only files are not included.
