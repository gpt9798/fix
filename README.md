# KarigarOnline.com (Flask)

This is a starter Flask project that serves a beautiful homepage for:
- Customers: **Find a Professional** (Plumbers / Electricians)
- Professionals: **Join as a Professional**

## Folder structure

```text
KarigarOnline.com/
  app.py
  templates/
    base.html
    home.html
  static/
    css/
      styles.css
```

## Run locally

1. Open this project folder in VS Code.
2. (Optional but recommended) Create/activate a virtual environment.
3. Install Flask:

```bash
pip install flask
```

4. Start the server:

```bash
python app.py
```

5. Open in browser:
- http://127.0.0.1:5000/

## Notes
- The CTAs on the homepage now point to **Login** (Find a Professional) and **Signup** (Join as a Professional).
- Google OAuth and password signup/login are supported.

### Google OAuth setup
Set these environment variables (required for Google login):

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

Optional:
- `GOOGLE_REDIRECT_URI` (defaults to `http://127.0.0.1:5000/auth/google/callback`)


