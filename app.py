from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/test_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
#@login_required
def profile():
    return render_template('profile.html')

@app.route('/dashboard')
#@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/buy')
#@login_required
def buy():
    return render_template('buy.html')

@app.route('/sell')
#@login_required
def sell():
    return render_template('sell.html')

@app.route('/cashaccount')
#@login_required
def cashaccount():
    return render_template('cashaccount.html')

@app.route('/transactions')
#@login_required
def transactions():
    return render_template('transactions.html')

@app.route('/marketoptions')
#@login_required
def marketoptions():
    return render_template('admin/marketoptions.html')

@app.route('/stock')
#@login_required
def stock():
    return render_template('admin/stock.html')

@app.route('/users')
#@login_required
def users():
    return render_template('admin/users.html')

@app.route('/admin')
#@login_required
def admin():
    return render_template('admin/admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user'] = user.username
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)