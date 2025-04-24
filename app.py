from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from functools import wraps
from flask_bcrypt import Bcrypt
from datetime import datetime
import os, random


app = Flask(__name__)
# Local database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/project_db'

# AWS database
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:password@my-rds-instance.cjow08gck1jq.us-west-1.rds.amazonaws.com:3306/project_db'
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
    role = db.Column(db.String(10), nullable=False, default = 0)
    cash_balance = db.Column(db.Float, nullable=False, default = 0)

    def __repr__(self):
        return '<User %r>' % self.username

# Stock model
class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_symbol = db.Column(db.String(10), unique=True, nullable=False)
    stock_name = db.Column(db.String(200), nullable=False)
    price_per_share = db.Column(db.Float, nullable=False)
    total_volume = db.Column(db.Integer, nullable=False, default = 100)
    purchased_volume = db.Column(db.Integer, nullable = False, default = 0)

# Account model
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    shares = db.Column(db.Integer, nullable=False, default=0)

# Transaction model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    price_per_share = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(4), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Market schedule model
class MarketSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(10), nullable=False, default='Monday')
    open_time = db.Column(db.Time, nullable=False, default='09:30:00')
    close_time = db.Column(db.Time, nullable=False, default='16:00:00')

# Market holiday model
class MarketHoliday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    name = db.Column(db.String(20), nullable=False) # Name of holiday

# Inserts sample data if database tables are empty
def init_data():

    # Market Schedule table
    if db.session.query(MarketSchedule).count() == 0:
        schedules = [
            MarketSchedule(day_of_week='Monday', open_time='09:30:00', close_time='16:00:00'),
            MarketSchedule(day_of_week='Tuesday', open_time='09:30:00', close_time='16:00:00'),
            MarketSchedule(day_of_week='Wednesday', open_time='09:30:00', close_time='16:00:00'),
            MarketSchedule(day_of_week='Thursday', open_time='09:30:00', close_time='16:00:00'),
            MarketSchedule(day_of_week='Friday', open_time='09:30:00', close_time='16:00:00')
        ]
        db.session.bulk_save_objects(schedules)
        db.session.commit()
    
    # Stock table
    if db.session.query(Stock).count() == 0:
        stocks = [
            Stock(stock_symbol='AAPL', stock_name='Apple Inc.', price_per_share=150.00),
            Stock(stock_symbol='MSFT', stock_name='Microsoft Corporation', price_per_share=280.00),
            Stock(stock_symbol='AMZN', stock_name='Amazon.com, Inc.', price_per_share=3300.00),
            Stock(stock_symbol='GOOGL', stock_name='Alphabet Inc. Class A', price_per_share=2700.00),
            Stock(stock_symbol='FB', stock_name='Meta Platforms, Inc.', price_per_share=340.00)
        ]
        db.session.add_all(stocks)
        db.session.commit()

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables, and populates some tables with necessary sample data for testing
with app.app_context():
    db.create_all()
    init_data()

# Admin role required decorator - Checks to see if the user is an admin
# Note! This decorator MUST be placed after the login_required decorator
def admin_role_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.role == "admin":
            abort(403)
        return func(*args, **kwargs)
    return decorated_view

# Function to compare current time with market open/close times
def is_market_open():
    now = datetime.now()
    current_day = now.strftime("%A")  # e.g. 'Monday'
    current_date = now.date()  # To check if day is holiday
    current_time = now.time()

    # Check if today is a holiday
    holiday = MarketHoliday.query.filter_by(date=current_date).first()
    if holiday:
        return False
    
    # Check trading schedule if not a holiday
    schedule = MarketSchedule.query.filter_by(day_of_week=current_day).first()

    if schedule and schedule.open_time <= current_time <= schedule.close_time:
        return True
    return False

# Context processor to make market status available to all templates
@app.context_processor
def inject_market_status():
    return {'market_status': is_market_open()}


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
    accounts = db.session.query(Account, Stock).join(Stock).filter(Account.user_id == current_user.id).all()

    # Calculate total stock value
    stock_value = sum(account.shares * stock.price_per_share for account, stock in accounts)
    current_balance = current_user.cash_balance
    total_value = current_balance + stock_value

    return render_template('dashboard.html', accounts=accounts,
                           current_balance=current_balance,
                           stock_value=stock_value,
                           total_value=total_value)


@app.route('/stocks')
@login_required
def stocks():
    stocks = Stock.query.all()

    # Checking if market is open
    if not is_market_open():
        flash("Trading is not currently available, market is closed.", "warning")
        return render_template('stocks.html', stocks=stocks)   
    
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
    return render_template('cashaccount.html', cash_balance=current_user.cash_balance)

@app.route('/deposit', methods=['POST'])
@login_required
def deposit():
    amount = float(request.form.get("amount"))
    if amount <= 0:
        flash("Invalid deposit amount!", "danger")
        return redirect(url_for('cashaccount'))

    current_user.cash_balance += amount
    db.session.commit()
    flash(f"Successfully deposited ${amount}!", "success")
    return redirect(url_for('cashaccount'))

@app.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    amount = float(request.form.get("amount"))
    if amount <= 0 or amount > current_user.cash_balance:
        flash("Invalid withdrawal amount!", "danger")
        return redirect(url_for('cashaccount'))

    current_user.cash_balance -= amount
    db.session.commit()
    flash(f"Successfully withdrew ${amount}!", "success")
    return redirect(url_for('cashaccount'))

@app.route('/transactions')
@login_required
def transactions():
    transactions = db.session.query(Transaction, Stock).join(Stock).order_by(Transaction.timestamp.desc()).all()
    return render_template('transactions.html', transactions=transactions)

@app.route('/buy', methods=['GET', 'POST'])
@login_required
def buy():
    # Checking if market is open
    if not is_market_open():
        return render_template('buy.html', cash_balance=current_user.cash_balance) 
    
    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol'].upper()
        shares = int(request.form['shares'])

        stock = Stock.query.filter_by(stock_symbol=stock_symbol).first()

        if not stock:
            flash("Stock not found!", "danger")
            return redirect(url_for('buy'))

        available_volume = stock.total_volume - stock.purchased_volume
        if available_volume < shares:
            flash("Stock has insufficient shares!")
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
            new_account = Account(user_id=current_user.id, stock_id=stock.id, shares=shares)
            db.session.add(new_account)
        
        new_transaction = Transaction(user_id=current_user.id, stock_id=stock.id, shares=shares, price_per_share=stock.price_per_share, transaction_type="BUY")
        db.session.add(new_transaction)

        stock.purchased_volume += shares
        db.session.commit()
        flash(f"Bought {shares} share(s) of {stock_symbol}!", "success")
    
    return render_template('buy.html', cash_balance=current_user.cash_balance)

@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    owned_stocks = Account.query.filter(Account.user_id == current_user.id, Account.shares > 0).join(Stock).add_columns(Stock.stock_symbol, Account.shares).all()
    
    # Checking if market is open
    if not is_market_open():    
        return render_template('sell.html', cash_balance=current_user.cash_balance, owned_stocks=owned_stocks)
    
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
        stock.purchased_volume -= shares_to_sell
        current_user.cash_balance += shares_to_sell * stock.price_per_share

        new_transaction = Transaction(user_id=current_user.id, stock_id=stock.id, shares=-shares_to_sell, price_per_share=stock.price_per_share, transaction_type="SELL")
        db.session.add(new_transaction)
        db.session.commit()
        flash(f"Sold {shares_to_sell} share(s) of {stock_symbol}!", "success")
    
    return render_template('sell.html', cash_balance=current_user.cash_balance, owned_stocks=owned_stocks)


##### Market option routes - Admin Required

@app.route('/marketoptions')
@login_required
@admin_role_required
def marketoptions():
    schedule = MarketSchedule.query.order_by(MarketSchedule.id.asc()).all()
    holidays = MarketHoliday.query.order_by(MarketHoliday.date.asc()).all()
    return render_template('admin/marketoptions.html', schedule=schedule, holidays=holidays)

@app.route('/update_schedule', methods=['POST'])
@login_required
@admin_role_required
def update_schedule():
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        open_time = request.form.get(f'open_{day}')
        close_time = request.form.get(f'close_{day}')
        schedule = MarketSchedule.query.filter_by(day_of_week=day).first()
        if schedule:
            schedule.open_time = open_time
            schedule.close_time = close_time
    db.session.commit()
    flash("Market schedule updated!", "success")
    return redirect(url_for('marketoptions'))

@app.route('/add_holiday', methods=['POST'])
@login_required
@admin_role_required
def add_holiday():
    date = request.form.get('holiday_date')
    name = request.form.get('holiday_name') or "Unnamed Holiday"
    if date:
        new_holiday = MarketHoliday(date=date, name=name)
        db.session.add(new_holiday)
        db.session.commit()
        flash("Holiday added!", "success")
    return redirect(url_for('marketoptions'))

@app.route('/delete_holiday/<int:holiday_id>', methods=['POST'])
@login_required
@admin_role_required
def delete_holiday(holiday_id):
    holiday = MarketHoliday.query.get(holiday_id)
    if holiday:
        db.session.delete(holiday)
        db.session.commit()
        flash("Holiday deleted!", "success")
    return redirect(url_for('marketoptions'))

##### Stock modification routes - Admin Required

@app.route('/stock', methods = ['GET', 'POST'])
@login_required
@admin_role_required
def stock():
    return render_template('admin/stock.html')

@app.route('/stock_create', methods = ['POST'])
@login_required
@admin_role_required
def stock_create():
    stock = Stock(
        stock_symbol = request.form.get("stock_symbol"),
        stock_name = request.form.get("stock_name"),
        price_per_share = request.form.get("price_per_share"),
        total_volume = request.form.get("total_volume")
    )
    db.session.add(stock)
    db.session.commit()
    return render_template('admin/stock.html')


@app.route('/stock_delete', methods = ['POST'])
@login_required
@admin_role_required
def stock_delete():
    stock_symbol = request.form.get("stock_symbol")
    Stock.query.filter_by(stock_symbol = stock_symbol).delete()
    db.session.commit()
    return render_template('admin/stock.html')


@app.route('/stock_update', methods=['POST']) 
@login_required
@admin_role_required
def stock_update():
    stock_symbol = request.form.get("stock_symbol")
    stock_name = request.form.get("stock_name")
    price_per_share = request.form.get("price_per_share")
    total_volume = request.form.get("total_volume")

    stock = Stock.query.filter_by(stock_symbol=stock_symbol).first()
    if not stock:
        flash("Stock not found!", "danger")
        return redirect(url_for('stock'))

    if stock_name:
        stock.stock_name = stock_name
    if price_per_share:
        stock.price_per_share = float(price_per_share)
    if total_volume:
        stock.total_volume = int(total_volume)

    db.session.commit()
    flash(f"Stock {stock_symbol} updated successfully!", "success")
    return redirect(url_for('stock'))


###### User modification routes - Admin Required
 
@app.route('/users')
@login_required
@admin_role_required
def users():
    users = User.query.order_by(User.id.asc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/add_user', methods=['POST'])
@login_required
@admin_role_required
def add_user():
    fullName = request.form['name']
    username = request.form['username']
    email = request.form['email']
    password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
    role = request.form['role']
    if request.form['cash']:
        cash_balance = request.form['cash']
    else:
        cash_balance = 10000.0  # Default starting balance

    # Prevents duplicate usernames
    if User.query.filter(User.username == username).first():
        flash('Username already exists!', 'danger')
        return redirect(url_for('users'))
    
    new_user = User(fullName=fullName, username=username, email=email, password=password, role=role, cash_balance=cash_balance)
    db.session.add(new_user)
    db.session.commit()
    
    flash('User added successfully!', 'success')
    return redirect(url_for('users'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_role_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    
    return redirect(url_for('users'))

@app.route('/edit_user/<int:user_id>', methods=['POST'])
@login_required
@admin_role_required
def edit_user(user_id):
    user = User.query.get(user_id)
    user.fullName = request.form['name']

    # Prevents duplicate usernames
    if User.query.filter(User.username == request.form['username']).first():
        flash('Username already exists!', 'danger')
        return redirect(url_for('users'))
    
    user.username = request.form['username']
    user.email = request.form['email']
    if request.form['password']:  # Keep old password if not provided
        user.password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
    user.role = request.form['role']

    db.session.commit()
    flash('User details updated successfully!', 'success')
    return redirect(url_for('users'))

# Admin landing page - Admin Required

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
        if not all([request.form.get("fullName"), request.form.get("username"), request.form.get("email"), request.form.get("password"), request.form.get("verifyPassword")  ]):
            flash("All fields are required!", "danger")
            return redirect(url_for("register"))
        if request.form.get("password") != request.form.get("verifyPassword"):
            flash("Passwords do not match!", "danger")
            return redirect(url_for("register"))
        hashedPassword = bcrypt.generate_password_hash(request.form.get("password")).decode('utf-8')
        user = User(
            fullName=request.form.get("fullName"),
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=hashedPassword,
            role="user"
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")


if __name__ == '__main__':
    app.run(debug=True)