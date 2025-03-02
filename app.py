from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from models import User, Transaction
from database import db
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///financial_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# User Registration (User Story #1)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400

        user = User(email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# User Login (User Story #2)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password, user.password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return jsonify({'error': 'Invalid credentials, please try again'}), 401
    return render_template('login.html')

# Dashboard (User Stories #4)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', user=user, transactions=transactions)

# Add Income/Expenses (User Story #3)
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.get(session['user_id'])
    amount = request.form['amount']
    category = request.form['category']
    description = request.form['description']
    is_recurring = request.form.get('recurring', False)

    transaction = Transaction(
        user_id=user.id,
        amount=amount,
        category=category,
        description=description,
        is_recurring=is_recurring
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'message': 'Transaction added successfully'})

# Edit/Remove Transaction (User Story #9)
@app.route('/transaction/<int:transaction_id>', methods=['PUT', 'DELETE'])
def manage_transaction(transaction_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.user_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'PUT':
        data = request.get_json()
        transaction.amount = data.get('amount', transaction.amount)
        transaction.category = data.get('category', transaction.category)
        transaction.description = data.get('description', transaction.description)
        db.session.commit()
        return jsonify({'message': 'Transaction updated successfully'})
    
    if request.method == 'DELETE':
        db.session.delete(transaction)
        db.session.commit()
        return jsonify({'message': 'Transaction removed successfully'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)