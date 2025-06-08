import os
from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from flask_cors import CORS
from database import db, init_app as init_db_command
from models import Product, Category, Order, OrderItem, User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy import func
from datetime import datetime, timedelta
from flask import abort
from wtforms import FloatField, SelectField
from wtforms.validators import NumberRange
from functools import wraps
from flask import request, redirect

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    try:
        os.makedirs(instance_path)
        print(f"Kreiran direktorij: {instance_path}")
    except OSError as e:
        print(f"Greška pri kreiranju direktorija {instance_path}: {e}")

db_path = os.path.join(instance_path, 'kafic.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
print(f"Putanja do baze podataka: {app.config['SQLALCHEMY_DATABASE_URI']}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'promijeni-ovu-tajnu-sifru-u-produkciji'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Molimo prijavite se za pristup ovoj stranici."
login_manager.login_message_category = "error"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('Korisničko ime', validators=[DataRequired()])
    password = PasswordField('Lozinka', validators=[DataRequired()])
    submit = SubmitField('Prijavi se')

class ProductForm(FlaskForm):
    name = StringField('Naziv proizvoda', validators=[DataRequired()])
    price = FloatField('Cijena', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Kategorija', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Spremi')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Nemate ovlasti za pristup ovoj stranici.", "error")
            return redirect(url_for('blagajna'))
        return f(*args, **kwargs)
    return decorated_function


CORS(app)
init_db_command(app)


def initialize_default_data():
    with app.app_context(): 
        if not Category.query.first():
            print("Inicijalizacija početnih podataka...")
            
            categories_data = ['Kave', 'Sokovi', 'Piva', 'Vina', 'Žestice', 'Hrana', 'Ostalo']
            cat_objects_dict = {} 

            for name in categories_data:
                category_obj = Category(name=name)
                db.session.add(category_obj)
                cat_objects_dict[name] = category_obj
            
            try:
                db.session.commit()
                print("Kategorije uspješno spremljene.")
            except Exception as e:
                db.session.rollback()
                print(f"Greška pri spremanju kategorija: {e}")
                return 
            print("Inicijalizacija kategorija dovršena.")
        else:
            print("Kategorije već postoje, preskačem inicijalizaciju.")


def initialize_users():
    with app.app_context():
        if not User.query.first():
            print("Inicijalizacija korisnika...")
            user1 = User(username='konobar', role='konobar')
            user1.set_password('konobar123') 

            user2 = User(username='admin', role='admin')
            user2.set_password('admin123') 

            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            print("Korisnici 'konobar' i 'admin' su kreirani.")
        else:
            print("Korisnici već postoje, preskačem inicijalizaciju.")

@app.route('/')
@login_required
def tables():
    """Prikazuje vizualnu mapu stolova."""
    return render_template('tables.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blagajna'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Nevažeće korisničko ime ili lozinka.', 'error')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('blagajna'))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Servira stranicu za analizu i grafove."""
    return render_template('dashboard.html')


@app.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories])

@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    category_name_filter = request.args.get('category')
    query = Product.query
    if category_name_filter and category_name_filter.lower() != 'all':
        category_obj = Category.query.filter(Category.name.ilike(category_name_filter)).first()
        if category_obj:
            query = query.filter_by(category_id=category_obj.id)
        else:
            return jsonify([])
    products = query.order_by(Product.name).all()
    return jsonify([product.to_dict() for product in products])

@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    data = request.get_json()
    if not data or 'table_number' not in data:
        return jsonify({"error": "Nedostaje broj stola."}), 400

    if data.get('status', 'open') == 'open':
        existing_order = Order.query.filter_by(table_number=data['table_number'], status='open').first()
        if existing_order:
            return jsonify({"error": f"Stol {data['table_number']} već ima otvorenu narudžbu."}), 400

    new_order = Order(
        table_number=data.get('table_number'),
        status=data.get('status', 'open'),
        total_amount=data.get('total_amount', 0)
    )
    db.session.add(new_order)

    if 'items' in data and data['items']:
        db.session.flush() 
        for item_data in data['items']:
            product = Product.query.get(item_data.get('id'))
            if product:
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=item_data['quantity'],
                    price_at_purchase=product.price
                )
                db.session.add(order_item)

    db.session.commit()
    return jsonify(new_order.to_dict()), 201

@app.route('/api/tables/status')
@login_required
def get_tables_status():
    """Vraća rječnik s otvorenim narudžbama: {'ImeStola': order_id}."""
    open_orders = Order.query.filter(Order.status.in_(['open', 'pending'])).all()
    status_dict = {order.table_number: {'id': order.id, 'status': order.status} for order in open_orders}
    response = jsonify(status_dict)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/orders', methods=['GET'])
@login_required
def get_all_orders():
    status_filters = request.args.getlist('status')
    query = Order.query
    if status_filters:
        query = query.filter(Order.status.in_(status_filters))
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    query = query.filter(Order.timestamp >= today_start)

    orders = query.order_by(Order.timestamp.desc()).all()
    return jsonify([order.to_dict() for order in orders])

@app.route('/api/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order_by_id(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['pending', 'completed', 'cancelled']:
        return jsonify({"error": "Nepoznat status narudžbe."}), 400
    order.status = new_status
    db.session.commit()
    return jsonify(order.to_dict())

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
@login_required
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status not in ['open', 'pending']:
        return jsonify({"error": "Narudžba je zaključena."}), 400

    data = request.get_json()

    if 'status' in data:
        new_status = data['status']
        if new_status not in ['completed', 'cancelled']:
            return jsonify({"error": "Nepoznat status."}), 400
        order.status = new_status
        order.total_amount = data.get('total_amount', order.total_amount)

    if 'items' in data:
        OrderItem.query.filter_by(order_id=order_id).delete()
        for item_data in data['items']:
            product = Product.query.get(item_data.get('id'))
            if product:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=item_data['quantity'],
                    price_at_purchase=product.price
                )
                db.session.add(order_item)

    db.session.commit()
    return jsonify(order.to_dict())

@app.route('/api/dashboard/data')
@login_required
def get_dashboard_data():
    completed_orders_query = Order.query.filter_by(status='completed')
    total_earnings = db.session.query(func.sum(Order.total_amount)).filter(Order.status == 'completed').scalar() or 0
    total_orders = completed_orders_query.count()

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    earnings_by_day_query = db.session.query(
        func.date(Order.timestamp).label('date'),
        func.sum(Order.total_amount).label('total')
    ).filter(Order.timestamp >= thirty_days_ago, Order.status == 'completed').group_by('date').order_by('date').all()

    earnings_by_cat_query = db.session.query(
        Category.name,
        func.sum(OrderItem.quantity * OrderItem.price_at_purchase).label('total')
    ).join(Product, OrderItem.product_id == Product.id)\
     .join(Category, Product.category_id == Category.id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(Order.status == 'completed')\
     .group_by(Category.name).order_by(func.sum(OrderItem.quantity * OrderItem.price_at_purchase).desc()).all()

    top_products_query = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_quantity')
    ).join(Product, OrderItem.product_id == Product.id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(Order.status == 'completed')\
     .group_by(Product.name)\
     .order_by(func.sum(OrderItem.quantity).desc())\
     .limit(10).all()

    response_data = {
        'summary': {
            'total_earnings': round(total_earnings, 2),
            'total_orders': total_orders
        },
        'daily_earnings': [{'date': str(record.date), 'total': round(record.total, 2)} for record in earnings_by_day_query],
        'category_earnings': [{'category': record.name, 'total': round(record.total, 2)} for record in earnings_by_cat_query],
        'top_products': [{'name': record.name, 'quantity': record.total_quantity} for record in top_products_query]
    }

    response = jsonify(response_data)

    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response


@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    """Prikazuje sve proizvode s opcijama za uređivanje/brisanje."""
    products = Product.query.order_by(Product.id).all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    """Ruta za dodavanje novog proizvoda."""
    form = ProductForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.order_by('name').all()]
    
    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data,
            price=form.price.data,
            category_id=form.category.data
        )
        db.session.add(new_product)
        db.session.commit()
        flash(f"Proizvod '{new_product.name}' je uspješno dodan.", "success")
        return redirect(url_for('admin_products'))
        
    return render_template('_product_form.html', form=form, title="Dodaj novi proizvod")

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    """Ruta za uređivanje postojećeg proizvoda."""
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product) 
    form.category.choices = [(c.id, c.name) for c in Category.query.order_by('name').all()]

    if request.method == 'GET':
        form.category.data = product.category_id

    if form.validate_on_submit():
        product.name = form.name.data
        product.price = form.price.data
        product.category_id = form.category.data
        db.session.commit()
        flash(f"Proizvod '{product.name}' je uspješno ažuriran.", "success")
        return redirect(url_for('admin_products'))
        
    return render_template('_product_form.html', form=form, title="Uredi proizvod", product=product)

@app.route('/blagajna')
@login_required
def blagajna():
    """Servira glavnu HTML stranicu blagajne."""
    order_id = request.args.get('order_id')
    if not order_id:
        flash("Molimo odaberite stol za početak.", "error")
        return redirect(url_for('tables'))
    
    order = Order.query.get_or_404(order_id)
    if order.status not in ['open', 'pending']:
        flash(f"Narudžba #{order.id} je već zaključena i ne može se mijenjati.", "error")
        return redirect(url_for('tables'))

    return render_template('blagajna.html', order=order)

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    """Ruta za brisanje proizvoda."""
    product = Product.query.get_or_404(product_id)
    product_name = product.name
    if OrderItem.query.filter_by(product_id=product.id).first():
        flash(f"Proizvod '{product_name}' se ne može obrisati jer je dio postojećih narudžbi.", "error")
        return redirect(url_for('admin_products'))

    db.session.delete(product)
    db.session.commit()
    flash(f"Proizvod '{product_name}' je obrisan.", "success")
    return redirect(url_for('admin_products'))


if __name__ == '__main__':
    with app.app_context():
        initialize_default_data() 
        initialize_users() 
    app.run(debug=True, port=5000)