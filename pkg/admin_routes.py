import os, random, uuid, string
from uuid import uuid4
from flask import render_template,request,redirect,flash,url_for,session,g,flash,jsonify,send_file,current_app
from flask_mailman import EmailMessage
from functools import wraps
from sqlalchemy import or_
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from pkg import app
from pkg.models import db,ProductImage, Product, Admin, ContactUs, Category,Gallery,Distributor
from pkg.product_forms import ProductForm
from pkg.register_forms import RegisterForm


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash("Please log in first!", "warning")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

def allowed_file(filename):
    """Check if the file extension is allowed."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS





def generate_ref(year=None, month=None, serial_number=None):
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    serial_number = serial_number or random.randint(1, 9999)

    year_str = str(year).zfill(4)
    month_str = str(month).zfill(2)
    serial_str = str(serial_number).zfill(4)
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    return f"{year_str}{month_str}{serial_str}{letters}"



@app.route('/add/product/', methods=['GET', 'POST'])
@admin_required
def add_product():
    unread_messages = ContactUs.query.filter_by(status="unread").count()
    form = ProductForm()

    form.category.choices = [(0, 'Select Category')] + [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        if form.category.data == 0:
            return jsonify({"success": False, "message": "Please select a valid category."}), 400

        try:
            year = datetime.now().year
            month = datetime.now().month
            serial_number = Product.query.count() + 1
            product_ref = generate_ref(year, month, serial_number)

            images = request.files.getlist("images")
            if not images or images[0].filename == '':
                return jsonify({"success": False, "message": "Please upload at least one image."}), 400

            new_product = Product(
                product_name=form.name.data,
                product_description=form.description.data,
                category_id=form.category.data, 
                product_ref=product_ref
            )
            db.session.add(new_product)
            db.session.flush()

            for image in images:
                if not allowed_file(image.filename):
                    return jsonify({"success": False, "message": f"File extension not allowed: {image.filename}"}), 400
                ext = image.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid4()}.{ext}"
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
                image.save(file_path)

                image_record = ProductImage(image_name=unique_filename, product_id=new_product.product_id)
                db.session.add(image_record)

            db.session.commit()
            return jsonify({"success": True, "message": "Product added successfully!"})

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

    return render_template("admin/add_product.html", form=form, current_admin=g.admin,
    unread_messages=unread_messages)




@app.route('/manage/products/')
@admin_required
def manage_products():
    unread_messages = ContactUs.query.filter_by(status="unread").count()
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()

    query = Product.query
    if search_query:
        query = query.filter(
            or_(
                Product.product_name.ilike(f"%{search_query}%"),
                Product.product_ref.ilike(f"%{search_query}%")
            )
        )

    products = query.paginate(page=page, per_page=10)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'html': render_template('admin/products_table.html', products=products)})

    return render_template(
        'admin/manage_products.html',
        products=products,
        unread_messages=unread_messages,
        search_query=search_query,
        current_admin=g.admin
    )




@app.route('/admin/products/edit/<int:product_id>/', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    unread_messages = ContactUs.query.filter_by(status="unread").count()
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all() 

    if request.method == 'POST':
        product.product_name = request.form['name']
        product.product_description = request.form['description']
        product.category_id = request.form['category']  

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('manage_products'))

    return render_template(
        'admin/edit_product.html',
        product=product,
        categories=categories,
        unread_messages=unread_messages,
        current_admin=g.admin
    )



@app.route('/admin/product/<int:product_id>')
@admin_required
def admin_product_details(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('admin/products_details.html', product=product)



@app.route('/admin/products/delete/<int:product_id>/', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Product deleted successfully!'})





@app.route('/admin/dashboard/')
@admin_required
def admin_dashboard():
    total_products = Product.query.count()
    total_distributors= Distributor.query.count()
    total_gallery = Gallery.query.count()
    unread_messages = ContactUs.query.filter_by(status="unread").count()
    products = Product.query.order_by(Product.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html', products=products, total_products=total_products,unread_messages=unread_messages,
    current_admin=g.admin, total_distributors=total_distributors,total_gallery=total_gallery)



@app.route("/register/", methods=["GET", "POST"])
def register_admin():
    unread_messages = ContactUs.query.filter_by(status="unread").count()
    form = RegisterForm()
    if form.validate_on_submit():
        pic = form.admin_profile_pic.data
        if pic:
            filename = secure_filename(pic.filename)
            pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = "default.jpg"

        # Hash the password
        hashed_pw = generate_password_hash(form.admin_password.data)

        # Create and save admin
        new_admin = Admin(
            admin_name=form.admin_name.data,
            admin_email=form.admin_email.data,
            admin_password=hashed_pw,
            admin_profile_pic=filename,
            admin_lastlogin=datetime.utcnow()
        )
        db.session.add(new_admin)
        db.session.commit()
        flash("Admin registered successfully!", "success")
        return redirect(url_for('admin_login'))  

    return render_template("admin/register.html", form=form,
    unread_messages=unread_messages,
    current_admin=g.admin)



@app.route("/admin/login/", methods=["GET", "POST"])
def admin_login():
    unread_messages = ContactUs.query.filter_by(status="unread").count()
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        admin = Admin.query.filter_by(admin_email=email).first()

        if admin and check_password_hash(admin.admin_password, password):
            session["admin_id"] = admin.admin_id
            session["admin_name"] = admin.admin_name  
            flash("Login successful!", "success")
            return redirect(url_for("admin_dashboard"))  

        flash("Invalid email or password!", "danger")

    return render_template("admin/login.html" ,
    unread_messages=unread_messages)


@app.route("/admin/logout/")
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_name", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("admin_login"))




def generate_reset_token(email, expires_sec=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='admin-password-reset')

def verify_reset_token(token, max_age=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='admin-password-reset', max_age=max_age)
    except Exception:
        return None
    return email




@app.route('/admin/forgot_password/', methods=['GET', 'POST'])
def forgot_password():
    unread_messages = ContactUs.query.filter_by(status="unread").count()
    
    if request.method == 'POST':
        email = request.form.get('email')
        admin = Admin.query.filter_by(admin_email=email).first()
        
        if admin:
            token = generate_reset_token(admin.admin_email)
            reset_url = url_for('reset_password', token=token, _external=True)

            
            email_msg = EmailMessage(
                subject="Password Reset Request",
                from_email="support@ecosunsolarpower.com",
                to=[admin.admin_email],
                body=f'''Hello {admin.admin_name},

To reset your password, click the link below:
{reset_url}

If you did not request this, please ignore this email.
'''
            )
            try:
                email_msg.send()  
                flash('A password reset link has been sent to your email.', 'info')
            except Exception as e:
                flash('Failed to send reset email. Please try again later.', 'danger')
            
            return redirect(url_for('admin_login'))
        else:
            flash('Email not found.', 'danger')

    return render_template('admin/forgot_password.html', unread_messages=unread_messages)




@app.route('/admin/reset_password/<token>/', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('The password reset link is invalid or has expired.', 'warning')
        return redirect(url_for('forgot_password'))

    admin = Admin.query.filter_by(admin_email=email).first()
    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if new_password != confirm_password:
            flash("Passwords do not match.", 'danger')
        else:
            admin.admin_password = generate_password_hash(new_password)
            db.session.commit()
            flash("Your password has been updated.", 'success')
            return redirect(url_for('admin_login'))

    return render_template('admin/reset_password.html', token=token )





@app.route('/admin/messages/')
@admin_required
def manage_messages():
    """Display all contact messages in the admin panel with pagination."""
    page = request.args.get('page', 1, type=int)  
    per_page = 10 

    messages_paginated = ContactUs.query.order_by(ContactUs.contact_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    unread_messages = ContactUs.query.filter_by(status="unread").count()
    message = ContactUs.query.filter_by().count()

    ContactUs.query.filter_by(status="unread").update({"status": "read"})
    db.session.commit()

    session['unread_messages'] = 0

    return render_template('admin/manage_messages.html', 
                           messages=messages_paginated, 
                           unread_messages=unread_messages, 
                           message=message,
                           current_admin=g.admin)



@app.route('/admin/messages/delete/<int:message_id>/')
@admin_required
def delete_message(message_id):
    """Delete a contact message using a GET request."""
    message = ContactUs.query.get_or_404(message_id)
    
    db.session.delete(message)
    db.session.commit()

    flash('Message deleted successfully', 'success')
    return redirect(url_for('manage_messages'))





@app.route('/admin/messages/reply/', methods=['POST'])
@admin_required
def reply_message():
    """Send a reply via email."""
    email = request.form.get('email')
    subject = request.form.get('subject')
    content = request.form.get('content')

    if not email or not content:
        flash('Email and message content are required', 'danger')
        return redirect(url_for('manage_messages'))

    try:
        msg = EmailMessage(
            subject=f"RE: {subject}",
            body=content,
            to=[email]
        )
        msg.send()
        flash('Reply sent successfully', 'success')
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'danger')

    return redirect(url_for('manage_messages'))





@app.route('/admin/send-mail/', methods=['GET', 'POST'])
@admin_required
def send_mail():
    """Allow admin to send emails to users."""
    if request.method == 'POST':
        recipient = request.form.get('recipient')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not recipient or not subject or not message:
            flash('All fields are required', 'danger')
            return redirect(url_for('send_mail'))

        try:
            email = EmailMessage(subject, message, to=[recipient])
            email.send()
            flash('Email sent successfully!', 'success')
        except Exception as e:
            flash(f'Error sending email: {str(e)}', 'danger')

        return redirect(url_for('send_mail'))

    return render_template('admin/send_mail.html', current_admin=g.admin)


@app.route("/admin/settings/", methods=["GET", "POST"])
@admin_required
def admin_settings():
    unread_messages = ContactUs.query.filter_by(status="unread").count()
    if not g.admin:
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        g.admin.admin_name = request.form["admin_name"]
        g.admin.admin_email = request.form["admin_email"]
        new_password = request.form.get("new_password")

        if new_password:
            g.admin.admin_password = generate_password_hash(new_password)

        if "profile_pic" in request.files:
            file = request.files["profile_pic"]
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join("static/images", filename)
                file.save(filepath)
                g.admin.admin_profile_pic = filename
                session["admin_profile_pic"] = filename

        db.session.commit()
        session["admin_name"] = g.admin.admin_name
        flash("Settings updated successfully.", "success")
        return redirect(url_for("admin_settings"))

    return render_template("admin/settings.html",current_admin=g.admin, 
                           unread_messages=unread_messages)



@app.route('/admin/upload_gallery/', methods=['GET', 'POST'])
@admin_required
def upload_gallery():
    unread_messages = ContactUs.query.filter_by(status="unread").count()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        files = request.files.getlist('media_files')

        if not title or not files or files[0].filename == '':
            flash("Please provide a title and at least one file.", "danger")
            return redirect(url_for('upload_gallery'))

        try:
            for file in files:
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower()

                if ext not in ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi']:
                    flash(f"Unsupported file type: {filename}", "danger")
                    return redirect(url_for('upload_gallery'))

                media_type = 'video' if ext in ['mp4', 'mov', 'avi'] else 'image'

                unique_filename = f"{uuid4().hex}.{ext}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(save_path)

                gallery_entry = Gallery(
                    title=title,
                    description=description,
                    media_type=media_type,
                    filename=unique_filename
                )
                db.session.add(gallery_entry)

            db.session.commit()
            flash('Media uploaded successfully!', 'success')
            return redirect(url_for('manage_galleries'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('upload_gallery'))

    return render_template("admin/upload_gallery.html", current_admin=g.admin, unread_messages=unread_messages)



@app.route('/admin/galleries')
@admin_required
def manage_galleries():
    total_gallery= Gallery.query.count()
    unread_messages = ContactUs.query.filter_by(status="unread").count()
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)

    query = Gallery.query
    if search_query:
        query = query.filter(Gallery.title.ilike(f"%{search_query}%"))

    galleries = query.order_by(Gallery.upload_date.desc()).paginate(page=page, per_page=10)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_template('admin/galleries_table.html', galleries=galleries, gallery_items=galleries.items)
        return jsonify({'html': html})
    
    return render_template('admin/manage_galleries.html', galleries=galleries, gallery_items=galleries.items, search_query=search_query, unread_messages=unread_messages, current_admin=g.admin, total_gallery=total_gallery)



@app.route('/admin/gallery/edit/<int:id>/', methods=['GET', 'POST'])
@admin_required
def edit_gallery(id):
    gallery = Gallery.query.get_or_404(id)
    unread_messages = ContactUs.query.filter_by(status="unread").count()

    if request.method == 'POST':
        gallery.title = request.form['title']
        gallery.description = request.form['description']
        gallery.media_type = request.form['media_type']  

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('manage_galleries'))

    return render_template(
        'admin/edit_gallery.html',
        gallery=gallery,current_admin=g.admin, unread_messages=unread_messages
    )


@app.route('/admin/gallery/delete/<int:id>/', methods=['POST'])
@admin_required
def delete_gallery(id):
    gallery = Gallery.query.get_or_404(id)
    db.session.delete(gallery)
    db.session.commit()
    flash('Media deleted successfully!', 'success')
    return redirect(url_for('manage_galleries'))


@app.route('/manage_distributors/')
@admin_required
def manage_distributors():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    
    query = Distributor.query.order_by(Distributor.date_registered.desc())
    
    if search_query:
        query = query.filter(
            or_(
                Distributor.full_name.ilike(f"%{search_query}%"),
                Distributor.distributor_id.ilike(f"%{search_query}%"),
                Distributor.company_name.ilike(f"%{search_query}%")
            )
        )
    
    distributors = query.paginate(page=page, per_page=10)

    unread_messages = ContactUs.query.filter_by(status="unread").count()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_template('admin/distributors_table.html', distributors=distributors)
        return jsonify({'html': html})
    
    
    return render_template(
        'admin/manage_distributors.html',
        distributors=distributors,
        current_admin=g.admin,
        unread_messages=unread_messages,
        search_query=search_query
    )



@app.route('/admin/distributor/<int:id>')
@admin_required
def distributor_details(id):
    distributor = Distributor.query.get_or_404(id)
    unread_messages = ContactUs.query.filter_by(status="unread").count()
    return render_template('admin/distributor_details.html', distributor=distributor, unread_messages=unread_messages)



