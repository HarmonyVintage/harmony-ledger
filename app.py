import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from supabase import create_client, Client
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "harmony_vintage_super_secret" # Required for sessions to work

# --- DATABASE CONNECTION ---
SUPABASE_URL = "https://pbygqrhorevuehbgdcnu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBieWdxcmhvcmV2dWVoYmdkY251Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE3NzA1MzcsImV4cCI6MjA5NzM0NjUzN30.aSkkj5xj9bqtZ2IcK2VSKMLzKZijb6qfVWmO_m89Yac"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- AUTHENTICATION ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')
        room_name = request.form.get('room_name').strip()
        password = request.form.get('password')

        if action == "create":
            # Check if room already exists
            existing = supabase.table('rooms').select('*').eq('room_name', room_name).execute()
            if existing.data:
                flash("Room name already taken. Choose another.")
                return redirect(url_for('login'))
            
            # Create new room
            hashed_pw = generate_password_hash(password)
            new_room = supabase.table('rooms').insert({"room_name": room_name, "password": hashed_pw}).execute()
            session['room_id'] = new_room.data[0]['id']
            session['room_name'] = room_name
            return redirect(url_for('index'))

        elif action == "join":
            # Check credentials
            room = supabase.table('rooms').select('*').eq('room_name', room_name).execute()
            if room.data and check_password_hash(room.data[0]['password'], password):
                session['room_id'] = room.data[0]['id']
                session['room_name'] = room.data[0]['room_name']
                return redirect(url_for('index'))
            else:
                flash("Incorrect Room Name or Password.")
                return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- MAIN APP ROUTES ---
@app.route('/')
def index():
    # Kick user to login if they don't have a session wristband
    if 'room_id' not in session:
        return redirect(url_for('login'))

    # Fetch ONLY expenses for this specific room
    response = supabase.table('expenses').select('*').eq('room_id', session['room_id']).order('created_at', desc=True).execute()
    expenses = response.data

    totals = {}
    for exp in expenses:
        totals[exp['paid_by']] = totals.get(exp['paid_by'], 0) + float(exp['amount'])
            
    next_buyer = min(totals, key=totals.get) if totals else "No Data"
    total_spent = sum(totals.values())
    member_count = len(totals) if len(totals) > 0 else 1
    target_average = total_spent / member_count

    return render_template('index.html', expenses=expenses, totals=totals, next_buyer=next_buyer, target_average=target_average, room_name=session['room_name'])

@app.route('/add', methods=['POST'])
def add_expense():
    if 'room_id' not in session: return redirect(url_for('login'))
    
    item_name = request.form.get('item_name')
    amount = float(request.form.get('amount'))
    paid_by = request.form.get('paid_by').strip().title() # standardizes names

    supabase.table('expenses').insert({
        "room_id": session['room_id'], "item_name": item_name, "amount": amount, "paid_by": paid_by
    }).execute()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_expense(id):
    if 'room_id' not in session: return redirect(url_for('login'))
    # Ensure they only delete from THEIR room
    supabase.table('expenses').delete().eq('id', id).eq('room_id', session['room_id']).execute()
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset_ledger():
    if 'room_id' not in session: return redirect(url_for('login'))
    # Deletes only this room's expenses
    supabase.table('expenses').delete().eq('room_id', session['room_id']).execute()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)