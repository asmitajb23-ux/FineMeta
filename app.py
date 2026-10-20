import os
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "traffic_police_secret_key"

# Database Configuration (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///traffic.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ----------------- Database Models -----------------
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    vehicle_no = db.Column(db.String(20), nullable=False)
    challan_no = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    evidence = db.Column(db.String(200))
    status = db.Column(db.String(50), default="Pending")
    police_remark = db.Column(db.String(200), default="Under Review")

class Police(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    police_id = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

# ----------------- Routes / Endpoints -----------------

# 1. Home Page & Fine Calculator
@app.route('/')
def home():
    return render_template('index.html')

# 2. Complaint Page (तक्रार दाखल करा)
@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        c_id = f"CMP{random.randint(10000, 99999)}"
        name = request.form['name']
        phone = request.form['phone']
        vehicle_no = request.form['vehicle_no']
        challan_no = request.form['challan_no']
        reason = request.form['reason']
        
        file = request.files.get('evidence')
        filename = ""
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_complaint = Complaint(
            complaint_id=c_id,
            name=name,
            phone=phone,
            vehicle_no=vehicle_no,
            challan_no=challan_no,
            reason=reason,
            evidence=filename
        )
        db.session.add(new_complaint)
        db.session.commit()

        flash(f"तुमची तक्रार सबमिट झाली आहे! तुमचा Complaint ID: {c_id}")
        return redirect(url_for('track'))

    return render_template('complaint.html')

# 3. Track Status (तक्रारीचे स्टेटस पाहा)
@app.route('/track', methods=['GET', 'POST'])
def track():
    result = None
    if request.method == 'POST':
        c_id = request.form['complaint_id']
        result = Complaint.query.filter_by(complaint_id=c_id).first()
    return render_template('track.html', result=result)

# 4. Police Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        p_id = request.form['police_id']
        pwd = request.form['password']
        officer = Police.query.filter_by(police_id=p_id, password=pwd).first()
        if officer:
            session['police_logged_in'] = True
            session['police_id'] = p_id
            return redirect(url_for('police_dashboard'))
        else:
            flash("चुकीचा Police ID किंवा Password!")
    return render_template('login.html')

# 5. Police Dashboard Page
@app.route('/police/dashboard')
def police_dashboard():
    if not session.get('police_logged_in'):
        return redirect(url_for('login'))
    complaints = Complaint.query.all()
    return render_template('police_dashboard.html', complaints=complaints)

# 6. Update Status (पोलीस अधिकाऱ्याकडून निर्णय अपडेट करणे)
@app.route('/police/update/<int:id>', methods=['POST'])
def update_status(id):
    if not session.get('police_logged_in'):
        return redirect(url_for('login'))
    
    comp = Complaint.query.get(id)
    if comp:
        comp.status = request.form['status']
        comp.police_remark = request.form['remark']
        db.session.commit()
        flash("तक्रारीचे स्टेटस यशस्वीरित्या अपडेट झाले!")
    return redirect(url_for('police_dashboard'))

# 7. Logout
@app.route('/logout')
def logout():
    session.pop('police_logged_in', None)
    return redirect(url_for('home'))

# Database Create & Default Police User Set Up
with app.app_context():
    db.create_all()
    if not Police.query.filter_by(police_id="POLICE101").first():
        default_police = Police(police_id="POLICE101", password="admin")
        db.session.add(default_police)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)