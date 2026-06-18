import os
from flask import Flask, render_template, request, redirect, url_for, flash
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "harmony_vintage_secret_key" 

# --- DATABASE CONNECTION ---
# Paste your actual URL and Key here again!
SUPABASE_URL = "https://pbygqrhorevuehbgdcnu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBieWdxcmhvcmV2dWVoYmdkY251Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE3NzA1MzcsImV4cCI6MjA5NzM0NjUzN30.aSkkj5xj9bqtZ2IcK2VSKMLzKZijb6qfVWmO_m89Yac"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    response = supabase.table('harmony_expenses').select('*').order('created_at', desc=True).execute()
    expenses = response.data

    totals = {"Sujal": 0, "Mehul": 0, "Kyson": 0, "Other": 0}
    
    for exp in expenses:
        if exp['paid_by'] in totals:
            totals[exp['paid_by']] += float(exp['amount'])
            
    core_members = {k: v for k, v in totals.items() if k != "Other"}
    next_buyer = min(core_members, key=core_members.get) if core_members else "No Data"

    # Calculate Total Room Expense and target average (excluding "Other")
    total_spent = sum(core_members.values())
    target_average = total_spent / 3 if total_spent > 0 else 0

    return render_template('index.html', expenses=expenses, totals=totals, next_buyer=next_buyer, target_average=target_average)

@app.route('/add', methods=['POST'])
def add_expense():
    item_name = request.form.get('item_name')
    amount = float(request.form.get('amount'))
    paid_by = request.form.get('paid_by')

    if paid_by == "Kyson" and amount >= 50:
        flash("Transaction Denied: Kyson is strictly limited to ₹50 per transaction.")
        return redirect(url_for('index'))

    supabase.table('harmony_expenses').insert({
        "item_name": item_name, "amount": amount, "paid_by": paid_by
    }).execute()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_expense(id):
    supabase.table('harmony_expenses').delete().eq('id', id).execute()
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset_ledger():
    # Deletes all rows where ID is greater than 0 (which is all of them)
    supabase.table('harmony_expenses').delete().gt('id', 0).execute()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)