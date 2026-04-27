from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'kfueit_job_fair_secret_key_2024_fixed'

# ─── DATABASE CONFIGURATION (SQLite for portability) ──────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['RESUME_FOLDER'] = os.path.join(BASE_DIR, 'uploads', 'resumes')
app.config['LOGO_FOLDER'] = os.path.join(BASE_DIR, 'uploads', 'logos')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_RESUME = {'pdf', 'doc', 'docx'}
ALLOWED_IMAGE = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

# ─── MODELS ───────────────────────────────────────────────────────────────────

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    cgpa = db.Column(db.Float)
    skills = db.Column(db.Text)
    resume = db.Column(db.String(200))
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('Application', backref='student', lazy=True, cascade='all, delete-orphan')
    saved_jobs = db.relationship('SavedJob', backref='student', lazy=True, cascade='all, delete-orphan')

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False)
    hr_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    website = db.Column(db.String(200))
    logo = db.Column(db.String(200))
    description = db.Column(db.Text)
    password = db.Column(db.String(200), nullable=False)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    jobs = db.relationship('Job', backref='company', lazy=True, cascade='all, delete-orphan')

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    salary = db.Column(db.String(100))
    location = db.Column(db.String(100))
    job_type = db.Column(db.String(50), default='Full-time')
    deadline = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('Application', backref='job', lazy=True, cascade='all, delete-orphan')
    saved_by = db.relationship('SavedJob', backref='job', lazy=True, cascade='all, delete-orphan')

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

class SavedJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def allowed_resume(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_RESUME

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE

# ─── DATABASE INITIALIZATION ──────────────────────────────────────────────────

def init_db():
    """Initialize database with tables and seed data."""
    with app.app_context():
        db.create_all()

        # FIX: Always ensure admin exists with correct hashed password
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                password=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
        else:
            # FIX: Reset password hash in case it was corrupted
            admin.password = generate_password_hash('admin123')
            db.session.commit()

        # Seed locations
        location_names = ['Rahim Yar Khan', 'Lahore', 'Islamabad', 'Multan', 'Karachi',
                          'Peshawar', 'Quetta', 'Faisalabad', 'Rawalpindi', 'Remote']
        for loc_name in location_names:
            if not Location.query.filter_by(name=loc_name).first():
                db.session.add(Location(name=loc_name))
        db.session.commit()

        # Seed companies & jobs only if none exist
        if not Company.query.first():
            sample_companies = [
                Company(company_name='TechVision Pakistan', hr_name='Ali Hassan',
                        email='hr@techvision.pk', phone='0300-1234567',
                        website='https://techvision.pk',
                        description='Leading software company in Pakistan specializing in enterprise solutions.',
                        password=generate_password_hash('company123'), approved=True),
                Company(company_name='Netsol Technologies', hr_name='Sara Ahmed',
                        email='hr@netsol.pk', phone='0311-9876543',
                        website='https://netsol.com',
                        description='Global provider of leasing and finance solutions.',
                        password=generate_password_hash('company123'), approved=True),
                Company(company_name='Systems Limited', hr_name='Usman Malik',
                        email='hr@systemsltd.com', phone='0321-5554443',
                        website='https://systemsltd.com',
                        description="Pakistan's largest IT company providing global IT solutions.",
                        password=generate_password_hash('company123'), approved=True),
                Company(company_name='Arbisoft', hr_name='Fatima Zafar',
                        email='hr@arbisoft.com', phone='0333-7654321',
                        website='https://arbisoft.com',
                        description='Top-tier software development company with global clients.',
                        password=generate_password_hash('company123'), approved=True),
                Company(company_name='10Pearls', hr_name='Hamid Raza',
                        email='hr@10pearls.com', phone='0345-1112223',
                        website='https://10pearls.com',
                        description='Digital transformation partner for global enterprises.',
                        password=generate_password_hash('company123'), approved=True),
            ]
            for c in sample_companies:
                db.session.add(c)
            db.session.flush()

            companies = Company.query.all()
            sample_jobs = [
                Job(company_id=companies[0].id, title='Software Engineer',
                    description='Develop and maintain enterprise web applications using Python/Django or Node.js.',
                    requirements='2+ years experience, BSc CS/SE, Python or Node.js',
                    salary='PKR 80,000 - 120,000', location='Lahore',
                    job_type='Full-time', deadline='2025-06-30'),
                Job(company_id=companies[0].id, title='Frontend Developer',
                    description='Build responsive UIs using React.js and modern CSS frameworks.',
                    requirements='React.js, HTML/CSS, 1+ year experience',
                    salary='PKR 60,000 - 90,000', location='Rahim Yar Khan',
                    job_type='Full-time', deadline='2025-06-30'),
                Job(company_id=companies[1].id, title='Business Analyst',
                    description='Analyze business requirements and translate into technical specifications.',
                    requirements='MBA or equivalent, strong communication skills',
                    salary='PKR 70,000 - 100,000', location='Karachi',
                    job_type='Full-time', deadline='2025-07-15'),
                Job(company_id=companies[1].id, title='QA Engineer',
                    description='Manual and automated testing of enterprise software applications.',
                    requirements='ISTQB certification preferred, Selenium knowledge',
                    salary='PKR 55,000 - 80,000', location='Islamabad',
                    job_type='Full-time', deadline='2025-07-15'),
                Job(company_id=companies[2].id, title='Data Scientist',
                    description='Work on ML models and data pipelines for predictive analytics.',
                    requirements='Python, TensorFlow/PyTorch, Statistics background',
                    salary='PKR 100,000 - 150,000', location='Islamabad',
                    job_type='Full-time', deadline='2025-07-30'),
                Job(company_id=companies[2].id, title='DevOps Engineer',
                    description='Manage CI/CD pipelines and cloud infrastructure on AWS/Azure.',
                    requirements='Docker, Kubernetes, AWS/Azure, Linux',
                    salary='PKR 90,000 - 130,000', location='Remote',
                    job_type='Remote', deadline='2025-07-30'),
                Job(company_id=companies[3].id, title='Mobile App Developer',
                    description='Build cross-platform mobile apps using Flutter or React Native.',
                    requirements='Flutter or React Native, REST APIs, 1+ year experience',
                    salary='PKR 75,000 - 110,000', location='Multan',
                    job_type='Full-time', deadline='2025-08-01'),
                Job(company_id=companies[3].id, title='UI/UX Designer',
                    description='Design intuitive interfaces for web and mobile applications.',
                    requirements='Figma, Adobe XD, user research experience',
                    salary='PKR 50,000 - 80,000', location='Lahore',
                    job_type='Full-time', deadline='2025-08-01'),
                Job(company_id=companies[4].id, title='Cloud Architect',
                    description='Design scalable cloud solutions on AWS/GCP/Azure platforms.',
                    requirements='AWS/GCP certified, microservices, 3+ years experience',
                    salary='PKR 150,000 - 200,000', location='Rahim Yar Khan',
                    job_type='Full-time', deadline='2025-08-15'),
                Job(company_id=companies[4].id, title='Cybersecurity Analyst',
                    description='Monitor and secure IT infrastructure from cyber threats.',
                    requirements='CEH/CISSP preferred, network security knowledge',
                    salary='PKR 85,000 - 130,000', location='Islamabad',
                    job_type='Full-time', deadline='2025-08-15'),
            ]
            for j in sample_jobs:
                db.session.add(j)

        db.session.commit()
        print("✅ Database initialized successfully.")
        print("✅ Admin credentials: username=admin | password=admin123")

# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    jobs = Job.query.join(Company).filter(Company.approved == True).order_by(Job.created_at.desc()).limit(6).all()
    companies = Company.query.filter_by(approved=True).limit(8).all()
    total_students = Student.query.count()
    total_companies = Company.query.filter_by(approved=True).count()
    total_jobs = Job.query.count()
    locations = Location.query.order_by(Location.name).all()
    return render_template('index.html', jobs=jobs, companies=companies,
                           total_students=total_students, total_companies=total_companies,
                           total_jobs=total_jobs, locations=locations)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ─── JOBS ─────────────────────────────────────────────────────────────────────

@app.route('/jobs')
def jobs():
    search = request.args.get('search', '').strip()
    location = request.args.get('location', '').strip()
    job_type = request.args.get('job_type', '').strip()

    jobs_query = Job.query.join(Company).filter(Company.approved == True)

    if search:
        jobs_query = jobs_query.filter(
            db.or_(
                Job.title.ilike(f'%{search}%'),
                Job.description.ilike(f'%{search}%'),
                Job.requirements.ilike(f'%{search}%'),
                Company.company_name.ilike(f'%{search}%')
            )
        )
    if location:
        jobs_query = jobs_query.filter(Job.location.ilike(f'%{location}%'))
    if job_type:
        jobs_query = jobs_query.filter(Job.job_type.ilike(f'%{job_type}%'))

    all_jobs = jobs_query.order_by(Job.created_at.desc()).all()
    locations = Location.query.order_by(Location.name).all()

    # Get student's applied & saved job IDs for UI feedback
    applied_ids = set()
    saved_ids = set()
    if session.get('user_type') == 'student':
        student_id = session['user_id']
        applied_ids = {a.job_id for a in Application.query.filter_by(student_id=student_id).all()}
        saved_ids = {s.job_id for s in SavedJob.query.filter_by(student_id=student_id).all()}

    return render_template('jobs.html', jobs=all_jobs, search=search, location=location,
                           job_type=job_type, locations=locations,
                           applied_ids=applied_ids, saved_ids=saved_ids)

# ─── API: JOB SEARCH (AJAX) ───────────────────────────────────────────────────

@app.route('/api/jobs/search')
def api_jobs_search():
    search = request.args.get('q', '').strip()
    location = request.args.get('location', '').strip()
    jobs_query = Job.query.join(Company).filter(Company.approved == True)
    if search:
        jobs_query = jobs_query.filter(
            db.or_(Job.title.ilike(f'%{search}%'), Job.description.ilike(f'%{search}%'))
        )
    if location:
        jobs_query = jobs_query.filter(Job.location.ilike(f'%{location}%'))
    results = jobs_query.limit(10).all()
    return jsonify([{
        'id': j.id, 'title': j.title,
        'company': j.company.company_name,
        'location': j.location, 'salary': j.salary
    } for j in results])

@app.route('/api/locations')
def api_locations():
    locs = Location.query.order_by(Location.name).all()
    return jsonify([l.name for l in locs])

# ─── AUTH ─────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not role:
            flash('Please select Student or Company to login.', 'warning')
            return render_template('login.html')

        if role == 'student':
            user = Student.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session.clear()
                session['user_id'] = user.id
                session['user_type'] = 'student'
                session['user_name'] = user.name
                flash(f'Welcome back, {user.name}! 🎉', 'success')
                return redirect(url_for('student_dashboard'))
            flash('Invalid email or password. Please try again.', 'danger')

        elif role == 'company':
            user = Company.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                if not user.approved:
                    flash('Your company account is pending admin approval. Please wait.', 'warning')
                    return redirect(url_for('login'))
                session.clear()
                session['user_id'] = user.id
                session['user_type'] = 'company'
                session['user_name'] = user.company_name
                flash(f'Welcome back, {user.company_name}!', 'success')
                return redirect(url_for('company_dashboard'))
            flash('Invalid email or password. Please try again.', 'danger')
        else:
            flash('Invalid login role.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# ─── STUDENT REGISTRATION ─────────────────────────────────────────────────────

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        cgpa = request.form.get('cgpa', '').strip()
        skills = request.form.get('skills', '').strip()
        password = request.form.get('password', '')

        if Student.query.filter_by(email=email).first():
            flash('This email is already registered. Please login.', 'danger')
            return redirect(url_for('student_register'))

        student = Student(
            name=name, email=email, phone=phone, department=department,
            cgpa=float(cgpa) if cgpa else None,
            skills=skills,
            password=generate_password_hash(password)
        )
        db.session.add(student)
        db.session.commit()
        flash('Registration successful! Please login to continue.', 'success')
        return redirect(url_for('login'))

    return render_template('student_register.html')

# ─── COMPANY REGISTRATION ─────────────────────────────────────────────────────

@app.route('/company/register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        hr_name = request.form.get('hr_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        website = request.form.get('website', '').strip()
        description = request.form.get('description', '').strip()
        password = request.form.get('password', '')
        logo_file = request.files.get('logo')

        if Company.query.filter_by(email=email).first():
            flash('This email is already registered!', 'danger')
            return redirect(url_for('company_register'))

        logo_filename = None
        if logo_file and logo_file.filename and allowed_image(logo_file.filename):
            logo_filename = secure_filename(logo_file.filename)
            os.makedirs(app.config['LOGO_FOLDER'], exist_ok=True)
            logo_file.save(os.path.join(app.config['LOGO_FOLDER'], logo_filename))

        company = Company(
            company_name=company_name, hr_name=hr_name, email=email, phone=phone,
            website=website, description=description, logo=logo_filename,
            password=generate_password_hash(password)
        )
        db.session.add(company)
        db.session.commit()
        flash('Registration submitted! Awaiting admin approval. You will be notified.', 'success')
        return redirect(url_for('login'))

    return render_template('company_register.html')

# ─── STUDENT DASHBOARD ────────────────────────────────────────────────────────

@app.route('/student/dashboard')
def student_dashboard():
    if session.get('user_type') != 'student':
        flash('Please login as a student to access the dashboard.', 'warning')
        return redirect(url_for('login'))

    student = Student.query.get(session['user_id'])
    applications = Application.query.filter_by(student_id=student.id).order_by(Application.applied_at.desc()).all()
    saved = SavedJob.query.filter_by(student_id=student.id).order_by(SavedJob.saved_at.desc()).all()
    recent_jobs = Job.query.join(Company).filter(Company.approved == True).order_by(Job.created_at.desc()).limit(5).all()
    shortlisted = [a for a in applications if a.status == 'Shortlisted']

    return render_template('student_dashboard.html', student=student,
                           applications=applications, recent_jobs=recent_jobs,
                           saved_jobs=saved, shortlisted=shortlisted)

@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))

    student = Student.query.get(session['user_id'])
    if request.method == 'POST':
        student.name = request.form.get('name', student.name).strip()
        student.phone = request.form.get('phone', '').strip()
        student.department = request.form.get('department', '').strip()
        cgpa = request.form.get('cgpa', '').strip()
        student.cgpa = float(cgpa) if cgpa else None
        student.skills = request.form.get('skills', '').strip()

        resume_file = request.files.get('resume')
        if resume_file and resume_file.filename and allowed_resume(resume_file.filename):
            os.makedirs(app.config['RESUME_FOLDER'], exist_ok=True)
            resume_filename = secure_filename(resume_file.filename)
            resume_file.save(os.path.join(app.config['RESUME_FOLDER'], resume_filename))
            student.resume = resume_filename

        db.session.commit()
        session['user_name'] = student.name
        flash('Profile updated successfully! ✅', 'success')
        return redirect(url_for('student_profile'))

    return render_template('student_profile.html', student=student)

# ─── JOB APPLY / SAVE ─────────────────────────────────────────────────────────

@app.route('/student/apply/<int:job_id>')
def apply_job(job_id):
    if session.get('user_type') != 'student':
        flash('Please login as a student to apply for jobs.', 'warning')
        return redirect(url_for('login'))

    job = Job.query.get_or_404(job_id)
    existing = Application.query.filter_by(student_id=session['user_id'], job_id=job_id).first()
    if existing:
        flash('You have already applied for this job.', 'warning')
    else:
        application = Application(student_id=session['user_id'], job_id=job_id)
        db.session.add(application)
        db.session.commit()
        flash(f'Application submitted for "{job.title}" successfully! 🎉', 'success')

    return redirect(request.referrer or url_for('jobs'))

@app.route('/student/save/<int:job_id>')
def save_job(job_id):
    if session.get('user_type') != 'student':
        flash('Please login as a student to save jobs.', 'warning')
        return redirect(url_for('login'))

    job = Job.query.get_or_404(job_id)
    existing = SavedJob.query.filter_by(student_id=session['user_id'], job_id=job_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash(f'"{job.title}" removed from saved jobs.', 'info')
    else:
        saved = SavedJob(student_id=session['user_id'], job_id=job_id)
        db.session.add(saved)
        db.session.commit()
        flash(f'"{job.title}" saved to your list! 🔖', 'success')

    return redirect(request.referrer or url_for('jobs'))

@app.route('/student/unsave/<int:job_id>')
def unsave_job(job_id):
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    saved = SavedJob.query.filter_by(student_id=session['user_id'], job_id=job_id).first()
    if saved:
        db.session.delete(saved)
        db.session.commit()
        flash('Job removed from saved list.', 'info')
    return redirect(request.referrer or url_for('student_dashboard'))

# ─── FILE SERVING ─────────────────────────────────────────────────────────────

@app.route('/uploads/resumes/<filename>')
def download_resume(filename):
    return send_from_directory(app.config['RESUME_FOLDER'], filename)

@app.route('/uploads/logos/<filename>')
def company_logo(filename):
    return send_from_directory(app.config['LOGO_FOLDER'], filename)

# ─── COMPANY ──────────────────────────────────────────────────────────────────

@app.route('/company/dashboard')
def company_dashboard():
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    company = Company.query.get(session['user_id'])
    jobs_list = Job.query.filter_by(company_id=company.id).order_by(Job.created_at.desc()).all()
    total_applicants = Application.query.join(Job).filter(Job.company_id == company.id).count()
    return render_template('company_dashboard.html', company=company,
                           jobs=jobs_list, total_applicants=total_applicants)

@app.route('/company/post-job', methods=['GET', 'POST'])
def post_job():
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    locations = Location.query.order_by(Location.name).all()
    if request.method == 'POST':
        job = Job(
            company_id=session['user_id'],
            title=request.form.get('title', '').strip(),
            description=request.form.get('description', '').strip(),
            requirements=request.form.get('requirements', '').strip(),
            salary=request.form.get('salary', '').strip(),
            location=request.form.get('location', '').strip(),
            job_type=request.form.get('job_type', 'Full-time'),
            deadline=request.form.get('deadline', '').strip()
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully! ✅', 'success')
        return redirect(url_for('company_dashboard'))
    return render_template('post_job.html', locations=locations)

@app.route('/company/applicants/<int:job_id>')
def view_applicants(job_id):
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    job = Job.query.get_or_404(job_id)
    if job.company_id != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('company_dashboard'))
    applications = Application.query.filter_by(job_id=job_id).order_by(Application.applied_at.desc()).all()
    return render_template('applicants.html', job=job, applications=applications)

@app.route('/company/shortlist/<int:app_id>/<status>')
def shortlist(app_id, status):
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    application = Application.query.get_or_404(app_id)
    allowed_statuses = ['Pending', 'Shortlisted', 'Rejected', 'Hired']
    if status in allowed_statuses:
        application.status = status
        db.session.commit()
        flash(f'Applicant status updated to "{status}". ✅', 'success')
    return redirect(request.referrer or url_for('company_dashboard'))

@app.route('/company/delete-job/<int:job_id>')
def delete_job(job_id):
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    job = Job.query.get_or_404(job_id)
    if job.company_id != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('company_dashboard'))
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully.', 'success')
    return redirect(url_for('company_dashboard'))

# ─── ADMIN ────────────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('user_type') == 'admin':
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # FIX: Proper admin authentication
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session.clear()
            session['admin_id'] = admin.id
            session['user_type'] = 'admin'
            session['user_name'] = 'Administrator'
            flash('Welcome, Admin! Dashboard loaded. ✅', 'success')
            return redirect(url_for('admin_dashboard'))

        flash('Invalid credentials. Try: admin / admin123', 'danger')

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Admin logged out.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('user_type') != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('admin_login'))

    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_jobs = Job.query.count()
    total_applications = Application.query.count()
    pending_companies = Company.query.filter_by(approved=False).count()
    recent_students = Student.query.order_by(Student.created_at.desc()).limit(5).all()
    recent_companies = Company.query.order_by(Company.created_at.desc()).limit(5).all()

    return render_template('admin_dashboard.html',
                           total_students=total_students,
                           total_companies=total_companies,
                           total_jobs=total_jobs,
                           total_applications=total_applications,
                           pending_companies=pending_companies,
                           recent_students=recent_students,
                           recent_companies=recent_companies)

@app.route('/admin/students')
def admin_students():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    students = Student.query.order_by(Student.created_at.desc()).all()
    return render_template('admin_students.html', students=students)

@app.route('/admin/companies')
def admin_companies():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    companies = Company.query.order_by(Company.created_at.desc()).all()
    return render_template('admin_companies.html', companies=companies)

@app.route('/admin/jobs')
def admin_jobs():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    jobs_list = Job.query.join(Company).order_by(Job.created_at.desc()).all()
    return render_template('admin_jobs.html', jobs=jobs_list)

@app.route('/admin/approve-company/<int:company_id>')
def approve_company(company_id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    company = Company.query.get_or_404(company_id)
    company.approved = True
    db.session.commit()
    flash(f'{company.company_name} approved successfully! ✅', 'success')
    return redirect(url_for('admin_companies'))

@app.route('/admin/reject-company/<int:company_id>')
def reject_company(company_id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    company = Company.query.get_or_404(company_id)
    company.approved = False
    db.session.commit()
    flash(f'{company.company_name} rejected.', 'warning')
    return redirect(url_for('admin_companies'))

@app.route('/admin/delete-student/<int:student_id>')
def delete_student(student_id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted.', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/delete-company/<int:company_id>')
def delete_company(company_id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash('Company deleted.', 'success')
    return redirect(url_for('admin_companies'))

@app.route('/admin/delete-job/<int:job_id>')
def admin_delete_job(job_id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted.', 'success')
    return redirect(url_for('admin_jobs'))

@app.route('/admin/reset-password', methods=['POST'])
def admin_reset_password():
    """Emergency admin password reset endpoint."""
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    admin = Admin.query.filter_by(username='admin').first()
    if admin:
        new_pass = request.form.get('new_password', 'admin123')
        admin.password = generate_password_hash(new_pass)
        db.session.commit()
        flash('Admin password reset successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# ─── RUN ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs(app.config['RESUME_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOGO_FOLDER'], exist_ok=True)
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(debug=debug, host='0.0.0.0', port=port)
