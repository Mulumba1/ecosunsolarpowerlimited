from datetime import datetime
from flask_sqlalchemy import SQLAlchemy



db = SQLAlchemy()


class ContactUs(db.Model):
    __tablename__ = 'contact_us'  
    contact_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    contact_name = db.Column(db.String(100), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    contact_subject = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    contact_message = db.Column(db.Text, nullable=False)
    contact_date = db.Column(db.DateTime(), default=datetime.utcnow)
    status = db.Column(db.String(10), default="unread")




class Product(db.Model):
    __tablename__ = 'products'

    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False, unique=True)
    product_description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_new = db.Column(db.Boolean, default=False)
    product_ref = db.Column(db.String(100), nullable=False, unique=True)

    images = db.relationship('ProductImage', backref='products', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Product {self.product_name}>"


class ProductImage(db.Model):
    __tablename__ = 'product_images'

    image_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    image_name = db.Column(db.String(255), nullable=False)
    uploaded_date = db.Column(db.DateTime, default=datetime.utcnow)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)

    def __repr__(self):
        return f"<Image {self.image_name}>"




class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)




class Gallery(db.Model):
    __tablename__ = 'gallery'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    media_type = db.Column(db.String(10), nullable=False) 
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        return f"<Gallery {self.media_type.title()}: {self.title}>"


class Distributor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    registration_number = db.Column(db.String(50))
    address = db.Column(db.Text, nullable=False)
    distributor_id = db.Column(db.String(20), unique=True, nullable=False)
    additional_info = db.Column(db.Text)
    passport_photo = db.Column(db.String(120))  # Stores filename
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)


class Admin(db.Model):
    admin_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    admin_name = db.Column(db.String(100), nullable=False)
    admin_email = db.Column(db.String(120), unique=True, nullable=False)  
    admin_password = db.Column(db.String(255), nullable=False)  
    admin_profile_pic = db.Column(db.String(255), default="default.jpg")  
    admin_lastlogin = db.Column(db.DateTime(), default=datetime.utcnow)
