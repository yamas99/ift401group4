from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from functools import wraps
from flask_bcrypt import Bcrypt
import os, random


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/project_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

# Database, login manager, Bcrypt init
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    fullName = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    cash_balance = db.Column(db.Float, nullable=False, default=10000.0)  # Default starting balance

    def __repr__(self):
        return '<User %r>' % self.username

# Stock model
class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_symbol = db.Column(db.String(10), unique=True, nullable=False)
    price_per_share = db.Column(db.Float, nullable=False)

# Account model
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    stock_symbol = db.Column(db.String(10), nullable=False, default="NUL")
    shares = db.Column(db.Integer, nullable=False, default=0)

# Transaction model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    stock_symbol = db.Column(db.String(10), nullable=False, default="NUL")
    shares = db.Column(db.Integer, nullable=False)
    price_per_share = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(4), nullable=False)  # "BUY" or "SELL"
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()

# Admin role required decorator - Checks to see if the user is an admin
# Note! This decorator MUST be placed after the login_required decorator
def admin_role_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.admin:
            abort(403)
        return func(*args, **kwargs)
    return decorated_view

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/stocks')
@login_required
def stocks():
    stocks = Stock.query.all()
    # Randomize stock prices
    for stock in stocks:
        # Stock volatility; higher number means higher price shifts
        volatility = 0.5
        fluctuation = round(random.uniform(-volatility,volatility), 2)

        # No negative stock prices
        if stock.price_per_share + fluctuation < 0:
            stock.price_per_share = 0
        else:
            stock.price_per_share += fluctuation
        
        db.session.commit()
    return render_template('stocks.html', stocks=stocks)

@app.route('/cashaccount')
@login_required
def cashaccount():
    accounts = Account.query.all()
    return render_template('cashaccount.html', accounts=accounts)

@app.route('/transactions')
@login_required
def transactions():
    transactions = Transaction.query.all()
    return render_template('transactions.html', transactions=transactions)

@app.route('/buy', methods=['GET', 'POST'])
@login_required
def buy():
    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol'].upper()
        shares = int(request.form['shares'])

        stock = Stock.query.filter_by(stock_symbol=stock_symbol).first()
        if not stock:
            flash("Stock not found!", "danger")
            return redirect(url_for('buy'))
        
        total_cost = shares * stock.price_per_share
        if current_user.cash_balance < total_cost:
            flash("Insufficient funds!", "danger")
            return redirect(url_for('buy'))
        
        current_user.cash_balance -= total_cost
        account = Account.query.filter_by(user_id=current_user.id, stock_id=stock.id).first()
        if account:
            account.shares += shares
        else:
            new_account = Account(user_id=current_user.id, stock_id=stock.id, stock_symbol = stock.stock_symbol, shares=shares)
            db.session.add(new_account)
        
        new_transaction = Transaction(user_id=current_user.id, stock_id=stock.id, stock_symbol=stock_symbol, shares=shares, price_per_share=stock.price_per_share, transaction_type="BUY")
        db.session.add(new_transaction)
        db.session.commit()
        flash(f"Bought {shares} share(s) of {stock_symbol}!", "success")
    
    return render_template('buy.html', cash_balance=current_user.cash_balance)

@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    owned_stocks = Account.query.filter(Account.user_id == current_user.id, Account.shares > 0).join(Stock).add_columns(Stock.stock_symbol, Account.shares).all()
    
    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol'].upper()
        shares_to_sell = int(request.form['shares'])

        stock = Stock.query.filter_by(stock_symbol=stock_symbol).first()
        if not stock:
            flash("Stock not found!", "danger")
            return redirect(url_for('sell'))
        
        account = Account.query.filter_by(user_id=current_user.id, stock_id=stock.id).first()
        if not account or account.shares < shares_to_sell:
            flash("Insufficient shares!", "danger")
            return redirect(url_for('sell'))
        


        account.shares -= shares_to_sell
        current_user.cash_balance += shares_to_sell * stock.price_per_share

        new_transaction = Transaction(user_id=current_user.id, stock_id=stock.id, stock_symbol=stock_symbol, shares=-shares_to_sell, price_per_share=stock.price_per_share, transaction_type="SELL")
        db.session.add(new_transaction)
        db.session.commit()
        flash(f"Sold {shares_to_sell} share(s) of {stock_symbol}!", "success")
    
    return render_template('sell.html', cash_balance=current_user.cash_balance, owned_stocks=owned_stocks)


#Admin routes - Admin role required

@app.route('/marketoptions')
@login_required
@admin_role_required
def marketoptions():
    return render_template('admin/marketoptions.html')

@app.route('/stock')
@login_required
@admin_role_required
def stock():
    return render_template('admin/stock.html')

@app.route('/users')
@login_required
@admin_role_required
def users():
    return render_template('admin/users.html')

@app.route('/admin')
@login_required
@admin_role_required
def admin():
    return render_template('admin/admin.html')


# Login, logout, register routes

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username")).first()
        if user and bcrypt.check_password_hash(user.password, request.form.get("password")):
            login_user(user, remember=request.form.get("remember"))
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have successfully logged out", "success")
    return redirect(url_for("login"))

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hashedPassword = bcrypt.generate_password_hash(request.form.get("password")).decode('utf-8')
        user = User(
            username=request.form.get("username"),
            password=hashedPassword,
            email=request.form.get("email"),
            fullName=request.form.get("fullName"),
            role="user"
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")


if __name__ == '__main__':
    app.run(debug=True)