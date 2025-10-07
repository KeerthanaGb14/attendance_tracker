from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import csv
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'replace-with-a-random-secret'

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

# Fixed users
USERS = ['keerthana', 'natasha']

# ---------------- CSV Helpers ----------------
def subjects_file(user):
    return DATA_DIR / f"{user}_subjects.csv"

def attendance_file(user):
    return DATA_DIR / f"{user}_attendance.csv"

def ensure_files(user):
    if not subjects_file(user).exists():
        with open(subjects_file(user),'w',newline='',encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['subject','credits','course_type','total_hours','leave_taken'])
    if not attendance_file(user).exists():
        with open(attendance_file(user),'w',newline='',encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date','subject','leave_hours','note'])

def read_subjects(user):
    ensure_files(user)
    subjects = []
    with open(subjects_file(user),newline='',encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            total_hours = float(r['total_hours'])
            leave_taken = float(r['leave_taken'])
            max_leave = total_hours*0.25
            subjects.append({
                'subject': r['subject'],
                'credits': float(r['credits']),
                'course_type': r['course_type'],
                'total_hours': total_hours,
                'leave_taken': leave_taken,
                'remaining': max_leave - leave_taken,
                'max_leave': max_leave
            })
    return subjects

def write_subjects(user, subjects):
    with open(subjects_file(user),'w',newline='',encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['subject','credits','course_type','total_hours','leave_taken'])
        for s in subjects:
            writer.writerow([s['subject'], s['credits'], s['course_type'], s['total_hours'], s['leave_taken']])

def read_attendance(user):
    ensure_files(user)
    records = []
    with open(attendance_file(user),newline='',encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            records.append(r)
    return records

def write_attendance(user, records):
    with open(attendance_file(user),'w',newline='',encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['date','subject','leave_hours','note'])
        for r in records:
            writer.writerow([r['date'], r['subject'], r['leave_hours'], r['note']])

def recalc_subject_leave(user):
    subjects = read_subjects(user)
    for s in subjects:
        s['leave_taken'] = 0
    records = read_attendance(user)
    for r in records:
        for s in subjects:
            if s['subject']==r['subject']:
                s['leave_taken'] += float(r['leave_hours'])
    write_subjects(user, subjects)

# ---------------- Routes ----------------
@app.route('/')
def home():
    # Just list fixed users
    return render_template('home.html', users=USERS)

@app.route('/dashboard/<user>')
def dashboard(user):
    user = user.lower()
    ensure_files(user)
    return render_template('dashboard.html', user=user)

@app.route('/add_subject/<user>', methods=['GET','POST'])
def add_subject(user):
    user = user.lower()
    ensure_files(user)
    if request.method=='POST':
        name = request.form['subject'].strip()
        credits = float(request.form['credits'])
        ctype = request.form['course_type']
        subjects = read_subjects(user)
        duplicate = any(s['subject']==name and s['course_type']==ctype for s in subjects)
        if duplicate:
            flash(f"{name} ({ctype}) already exists.", 'error')
        else:
            total_hours = credits*15*2 if ctype=='lab' else credits*15
            subjects.append({'subject':name,'credits':credits,'course_type':ctype,'total_hours':total_hours,'leave_taken':0})
            write_subjects(user, subjects)
            flash(f"{name} added.", 'success')
        return redirect(url_for('add_subject',user=user))
    return render_template('add_subject.html', user=user)

@app.route('/add_attendance/<user>', methods=['GET','POST'])
def add_attendance(user):
    user = user.lower()
    ensure_files(user)
    subjects = read_subjects(user)
    if request.method=='POST':
        subject = request.form['subject']
        leave_hours = float(request.form['leave_hours'])
        note = request.form['note']
        date = request.form['date'] or datetime.now().strftime('%Y-%m-%d')
        records = read_attendance(user)
        records.append({'date':date,'subject':subject,'leave_hours':leave_hours,'note':note})
        write_attendance(user,records)
        recalc_subject_leave(user)
        flash("Attendance added.",'success')
        return redirect(url_for('add_attendance',user=user))
    return render_template('add_attendance.html', user=user, subjects=subjects)

@app.route('/summary/<user>')
def summary(user):
    user = user.lower()
    subjects = read_subjects(user)
    records = read_attendance(user)
    return render_template('summary.html', user=user, subjects=subjects, records=records)

@app.route('/delete_subject/<user>/<subject>/<ctype>')
def delete_subject(user,subject,ctype):
    user = user.lower()
    subjects = read_subjects(user)
    subjects = [s for s in subjects if not (s['subject']==subject and s['course_type']==ctype)]
    write_subjects(user,subjects)
    flash(f"{subject} deleted.",'success')
    return redirect(url_for('summary',user=user))

@app.route('/delete_attendance/<user>/<int:index>')
def delete_attendance(user,index):
    user = user.lower()
    records = read_attendance(user)
    if 0<=index<len(records):
        records.pop(index)
        write_attendance(user,records)
        recalc_subject_leave(user)
        flash("Attendance deleted.",'success')
    return redirect(url_for('summary',user=user))

@app.route('/edit_attendance/<user>/<int:index>',methods=['GET','POST'])
def edit_attendance(user,index):
    user = user.lower()
    records = read_attendance(user)
    if request.method=='POST':
        try:
            new_hours = float(request.form['leave_hours'])
        except:
            new_hours = 0
        records[index]['leave_hours'] = new_hours
        records[index]['note'] = request.form['note']
        write_attendance(user,records)
        recalc_subject_leave(user)
        flash("Attendance updated.",'success')
        return redirect(url_for('summary',user=user))
    record = records[index]
    return render_template('edit_attendance.html', user=user, record=record, index=index)

@app.route('/download/<user>')
def download_csv(user):
    return send_file(subjects_file(user), as_attachment=True, download_name=f"{user}_subjects.csv")

# ---------------- Run ----------------
if __name__=='__main__':
    app.run(debug=True)
