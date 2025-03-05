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