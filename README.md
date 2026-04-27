# KFUEIT Job Fair Web Application - Fixed Version

## ✅ All Issues Fixed

### 1. Admin Login Fix
- **Root Cause**: Password hash was not being regenerated on startup.
- **Fix**: `init_db()` now always resets admin password hash on startup.
- **Credentials**: `username: admin` | `password: admin123`

### 2. User Login Button Fix
- **Root Cause**: Form validation blocked submission when role radio button not selected.
- **Fix**: Replaced radio buttons with visible clickable role cards. Hidden `<input>` stores selected role. JS validates before submit with user-friendly error.

### 3. KFUEIT Logo Added
- SVG-based KFUEIT logo (no external image required) added to:
  - ✅ Navbar (all pages)
  - ✅ Login page
  - ✅ Admin Login page
  - ✅ Admin Sidebar
  - ✅ Footer

### 4. Job Search Fixed
- Search now queries: title, description, requirements, company name
- Location dropdown populated from `locations` table
- Job type filter added (Full-time, Remote, Internship, Part-time)
- Applied/saved status shown per job for logged-in students

### 5. Locations Fixed
- `Location` model added to database
- 10 cities seeded: Rahim Yar Khan, Lahore, Islamabad, Multan, Karachi, Peshawar, Quetta, Faisalabad, Rawalpindi, Remote
- All dropdowns pull from DB dynamically

### 6. Apply Job Feature Fixed
- Apply button works with confirmation dialog
- Status shown (Applied / Save / Pending)
- Saved Jobs feature fully implemented (toggle save/unsave)

### 7. Database
- SQLite (portable, no PostgreSQL server needed)
- Tables: Student, Company, Job, Application, SavedJob, Admin, Location
- 10 sample jobs, 5 companies, 10 locations seeded automatically

### 8. Student Dashboard - 3 Tabs
- **Applications** tab: All applied jobs with status badges
- **Shortlisted** tab: Jobs where status = Shortlisted
- **Saved Jobs** tab: Bookmarked jobs with Apply/Remove buttons

## 🚀 How to Run

```bash
cd KFUEIT-Job-Fair-Fixed
pip install -r requirements.txt
python app.py
```

Then open: http://localhost:5000

## 👤 Test Accounts

| Role | Username/Email | Password |
|------|---------------|----------|
| Admin | admin | admin123 |
| Company | hr@techvision.pk | company123 |
| Company | hr@netsol.pk | company123 |
| Student | Register new account | — |

## 📁 Project Structure
```
KFUEIT-Job-Fair-Fixed/
├── app.py              # Main Flask app (all bugs fixed)
├── requirements.txt
├── database.db         # Auto-created on first run
├── static/
│   ├── css/
│   │   ├── style.css   # Original styles
│   │   └── kfueit.css  # New professional UI styles
│   └── js/
│       └── main.js     # Fixed JavaScript
├── templates/
│   ├── base.html       # With KFUEIT logo in navbar
│   ├── index.html      # Homepage with hero search
│   ├── login.html      # Fixed role selection
│   ├── admin_login.html# Fixed admin auth + logo
│   ├── admin_dashboard.html  # With KFUEIT logo
│   ├── admin_jobs.html
│   ├── student_dashboard.html # 3 tabs: Applications/Shortlisted/Saved
│   ├── jobs.html       # Full search + apply + save
│   └── ...
└── uploads/
    ├── resumes/
    └── logos/
```
