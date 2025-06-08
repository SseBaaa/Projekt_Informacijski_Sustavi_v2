from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_app(app):
    """Inicijalizira bazu podataka s Flask aplikacijom."""
    db.init_app(app) 
    with app.app_context():
        from models import Category, Product, Order, OrderItem, User
        db.create_all()