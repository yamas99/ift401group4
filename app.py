from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/project_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# User model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    fullName = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

# Stock Transaction model (NEW)
class StockTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_symbol = db.Column(db.String(10), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    price_per_share = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(4), nullable=False)  # "BUY" or "SELL"
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Stock {self.stock_symbol} {self.transaction_type}>"


# User loader, initialize database
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
with app.app_context():
    db.create_all()

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


@app.route('/buy', methods=['GET', 'POST'])
#@login_required
def buy():
    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol'].upper()
        shares = int(request.form['shares'])
        price_per_share = float(request.form['price_per_share'])

        if shares <= 0 or price_per_share <= 0:
            flash("Invalid stock purchase data!", "danger")
            return redirect(url_for('buy'))

        new_transaction = StockTransaction(
            user_id=current_user.id,
            stock_symbol=stock_symbol,
            shares=shares,
            price_per_share=price_per_share,
            transaction_type="BUY"
        )

        db.session.add(new_transaction)
        db.session.commit()
        flash(f"Successfully bought {shares} shares of {stock_symbol}!", "success")
        return redirect(url_for('dashboard'))

    return render_template('buy.html')

@app.route('/sell')
#@login_required
def sell():
    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol'].upper()
        shares_to_sell = int(request.form['shares'])

        owned_shares = db.session.query(
            db.func.sum(StockTransaction.shares)
        ).filter_by(user_id=current_user.id, stock_symbol=stock_symbol).scalar() or 0

        if shares_to_sell > owned_shares:
            flash("Not enough shares to sell!", "danger")
            return redirect(url_for('sell'))

        new_transaction = StockTransaction(
            user_id=current_user.id,
            stock_symbol=stock_symbol,
            shares=-shares_to_sell, 
            price_per_share=0,  
            transaction_type="SELL"
        )

        db.session.add(new_transaction)
        db.session.commit()
        flash(f"Successfully sold {shares_to_sell} shares of {stock_symbol}!", "success")
        return redirect(url_for('dashboard'))

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
@login_required
def admin():
    return render_template('admin/admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user = Users.query.filter_by(username=request.form.get("username")).first()
        if user and user.password == request.form.get("password"):
            login_user(user)
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))



@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = Users(
            username=request.form.get("username"),
            password=request.form.get("password"),
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