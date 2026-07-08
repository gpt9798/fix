# TODO
- [x] Investigate build error: missing Flask endpoints `customer_find` / `professional_join` referenced from `templates/home.html`.
- [x] Confirm `app.py` route endpoints available (`home`, `login`, `signup`, `dashboard`, etc.).
- [x] Update `templates/home.html` navbar URLs to reference existing endpoints:
  - `customer_find` -> `login`
  - `professional_join` -> `signup`
- [ ] Run the Flask app and verify the homepage renders without `BuildError`.

