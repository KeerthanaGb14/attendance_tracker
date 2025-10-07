from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import csv
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATA_FILE = 'data/user_data.csv'

# Ensure CSV exists
if not os.path.exists('data'):
    os.makedirs('data')

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['user','subject','type','credits','hours','attended'])
        writer.writeheader()

# Read CSV for a user
def read_csv(user):
    subjects = []
    with open(DATA_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['user'] == user:
                row['credits'] = int(row['credits'])
                row['hours'] = int(row['hours'])
                row['attended'] = int(row['attended'])
                row['allowed_leave'] = int(row['hours'] * 0.25)
                row['remaining_leave'] = row['allowed_leave'] - row['attended']
                row['percentage'] = round((row['attended']/row['hours'])*100,2) if row['hours'] else 0
                subjects.append(row)
    return subjects

# Write CSV for a user
def write_csv(user, subjects):
    all_rows = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['user'] != user:
                    all_rows.append(row)
    all_rows.extend(subjects)
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['user','subject','type','credits','hours','attended'])
        writer.writeheader()
        writer.writerows(all_rows)

# Home page - select user
@app.route('/')
def home():
    users = ['keerthana', 'natasha']  # hardcoded users
    return render_template('home.html', users=users)

# Dashboard page
@app.route('/dashboard/<user>')
def dashboard(user):
    return render_template('dashboard.html', user=user)

# Add subject
@app.route('/add_subject/<user>', methods=['GET','POST'])
def add_subject(user):
    if request.method == 'POST':
        subject = request.form['subject']
        type_ = request.form['type']
        credits = int(request.form['credits'])
        hours = int(request.form['hours'])
        subjects = read_csv(user)
        for s in subjects:
            if s['subject'] == subject and s['type'] == type_:
                flash(f"{subject} {type_} already exists.", "error")
                return redirect(url_for('add_subject', user=user))
        subjects.append({'user':user,'subject':subject,'type':type_,'credits':credits,'hours':hours,'attended':0})
        write_csv(user, subjects)
        flash(f"{subject} added.", "success")
        return redirect(url_for('dashboard', user=user))
    return render_template('add_subject.html', user=user)

# Add attendance
@app.route('/add_attendance/<user>', methods=['GET','POST'])
def add_attendance(user):
    subjects = read_csv(user)
    if request.method == 'POST':
        subject_name = request.form['subject']
        attended = int(request.form['attended'])
        for s in subjects:
            if s['subject'] == subject_name:
                s['attended'] += attended
                break
        write_csv(user, subjects)
        flash(f"Attendance added for {subject_name}", "success")
        return redirect(url_for('dashboard', user=user))
    return render_template('add_attendance.html', user=user, subjects=subjects)

# Edit attendance
@app.route('/edit_attendance/<user>/<subject>', methods=['GET','POST'])
def edit_attendance(user, subject):
    subjects = read_csv(user)
    sub = next((s for s in subjects if s['subject'] == subject), None)
    if request.method == 'POST':
        new_attended = int(request.form['attended'])
        sub['attended'] = new_attended
        write_csv(user, subjects)
        flash(f"Attendance for {subject} updated.", "success")
        return redirect(url_for('summary', user=user))
    return render_template('edit_attendance.html', user=user, subject=sub)

# Delete subject
@app.route('/delete_subject/<user>/<subject>')
def delete_subject(user, subject):
    subjects = read_csv(user)
    subjects = [s for s in subjects if s['subject'] != subject]
    write_csv(user, subjects)
    flash(f"{subject} deleted.", "success")
    return redirect(url_for('summary', user=user))

# Summary page
@app.route('/summary/<user>')
def summary(user):
    subjects = read_csv(user)
    return render_template('summary.html', user=user, subjects=subjects)

# Download CSV
@app.route('/download/<user>')
def download(user):
    return send_file(DATA_FILE, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
