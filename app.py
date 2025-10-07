from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import csv, os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATA_FILE = 'data.csv'

# Ensure CSV exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user','subject','type','credits','hours','attended'])

# Helper to read/write CSV
def read_data():
    with open(DATA_FILE, 'r', newline='') as f:
        return list(csv.DictReader(f))

def write_data(rows):
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['user','subject','type','credits','hours','attended'])
        writer.writeheader()
        writer.writerows(rows)

# Home page - select user
@app.route('/')
def home():
    rows = read_data()
    users = sorted(set([r['user'] for r in rows]))
    return render_template('home.html', users=users)

# Dashboard
@app.route('/dashboard/<user>')
def dashboard(user):
    return render_template('dashboard.html', user=user)

# Add Subject
@app.route('/add_subject/<user>', methods=['GET','POST'])
def add_subject(user):
    if request.method == 'POST':
        subject = request.form['subject']
        type_course = request.form['type']
        credits = int(request.form['credits'])
        hours = int(request.form['hours'])
        rows = read_data()
        # check duplicate
        for r in rows:
            if r['user']==user and r['subject']==subject and r['type']==type_course:
                flash(f"{subject} ({type_course}) already exists!", 'error')
                return redirect(url_for('add_subject', user=user))
        rows.append({'user':user,'subject':subject,'type':type_course,'credits':credits,'hours':hours,'attended':0})
        write_data(rows)
        flash(f"{subject} added!", 'success')
        return redirect(url_for('dashboard', user=user))
    return render_template('add_subject.html', user=user)

# Add Attendance
@app.route('/add_attendance/<user>', methods=['GET','POST'])
def add_attendance(user):
    rows = read_data()
    subjects = [r for r in rows if r['user']==user]
    if request.method=='POST':
        subject = request.form['subject']
        attended = int(request.form['attended'])
        for r in rows:
            if r['user']==user and r['subject']==subject:
                r['attended'] += attended
        write_data(rows)
        flash(f"{attended} hours added for {subject}", 'success')
        return redirect(url_for('dashboard', user=user))
    return render_template('add_attendance.html', user=user, subjects=subjects)

# Summary
@app.route('/summary/<user>')
def summary(user):
    rows = read_data()
    subjects = [r for r in rows if r['user']==user]
    for s in subjects:
        s['allowed_leave'] = int(s['hours']*0.25)
        s['remaining_leave'] = s['allowed_leave'] - int(s['attended'])
        s['percentage'] = round(s['attended']/s['hours']*100,2) if s['hours']>0 else 0
    return render_template('summary.html', user=user, subjects=subjects)

# Delete subject
@app.route('/delete_subject/<user>/<subject>')
def delete_subject(user, subject):
    rows = read_data()
    rows = [r for r in rows if not (r['user']==user and r['subject']==subject)]
    write_data(rows)
    flash(f"{subject} deleted", 'success')
    return redirect(url_for('summary', user=user))

# Download CSV
@app.route('/download/<user>')
def download(user):
    return send_file(DATA_FILE, as_attachment=True)

if __name__=='__main__':
    app.run(debug=True)
