import os, random, string, uuid
from uuid import uuid4
from datetime import datetime,date
from flask import render_template,request
from sqlalchemy.orm import joinedload
from flask import render_template,request,redirect,flash,url_for,make_response,session,flash,jsonify,send_file, current_app
from werkzeug.utils import secure_filename
from io import BytesIO
from fpdf import FPDF
from flask_mailman import EmailMessage
from flask_wtf.csrf import generate_csrf
from pkg import app
from pkg.models import db,ContactUs,Product,Category,Gallery,Distributor
from pkg.models import db
from pkg.contact_forms import ContactForm



ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

def allowed_file(filename):
    """Check if the file extension is allowed."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    form = ContactForm()
    products = Product.query.order_by(Product.created_at.desc()).limit(6).all()
    return render_template("user/index.html", products=products, form=form)



@app.route('/about/')
def about():
    return render_template("user/about.html")

@app.route('/contact/')
def contact_us():
    form = ContactForm()
    return render_template('user/contact.html', form =form)

@app.route('/service/')
def service():
    return render_template("user/service.html")


# @app.route('/products/')
# def products():
#     page = request.args.get('page', 1, type=int)
#     pagination = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=9)
#     categories = Category.query.all()
#     return render_template('user/products.html', products=pagination.items, pagination=pagination, categories=categories)





@app.route('/products/')
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    category_id = request.args.get('category', '', type=str)

    query = Product.query

    if search:
        query = query.filter(Product.product_name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)

    pagination = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=9)
    categories = Category.query.all()
    return render_template('user/products.html', products=pagination.items, pagination=pagination, categories=categories, search=search, category_id=category_id)


@app.route('/products/ajax')
def products_ajax():
    search = request.args.get('search', '', type=str)
    category_id = request.args.get('category', '', type=str)

    query = Product.query

    if search:
        query = query.filter(Product.product_name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.created_at.desc()).all()
    return render_template('user/_product_grid.html', products=products)




@app.route('/product/<int:product_id>')
def product_details(product_id):
    product = Product.query.options(joinedload(Product.category)).get_or_404(product_id)

    similar_products = Product.query.filter(
        (Product.category_id == product.category_id) &
        (Product.product_id != product_id)
    ).limit(6).all()

    return render_template('user/products_details.html', product=product, similar_products=similar_products)




@app.route('/send_message/', methods=['POST', 'GET'])
def send_message():
    form = ContactForm()
    
    if request.method == 'POST':        
        if form.validate_on_submit():            
            name = form.name.data
            email = form.email.data
            phone = form.phone.data
            subject = form.subject.data
            message = form.message.data

            new_contact = ContactUs(
                contact_name=name, 
                contact_email=email, 
                contact_phone=phone, 
                contact_subject=subject, 
                contact_message=message
            )
            db.session.add(new_contact)
            db.session.commit()

            flash(f'Thank you {name} for contacting us. One of our representatives will contact you shortly at {email}', 'success')
            return redirect('/')
    return render_template('user/contact.html', form=form)





@app.route('/gallery/')
def show_gallery():
    gallery_items = Gallery.query.order_by(Gallery.upload_date.desc()).all()
    return render_template('user/gallery.html', gallery_items=gallery_items)




def generate_distributor_id():
    date_part = datetime.utcnow().strftime("%y%m%d")  
    random_letters = ''.join(random.choices(string.ascii_uppercase, k=2))  
    serial = str(random.randint(1000, 9999))  
    return f"DIST-{date_part}{serial}{random_letters}"



@app.route('/register_distributor/', methods=['GET', 'POST'])
def register_distributor():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        company_name = request.form.get('company_name')
        registration_number = request.form.get('registration_number')
        address = request.form.get('address')
        additional_info = request.form.get('additional_info')
        photo = request.files.get('passport_photo')

        if not full_name or not phone or not email or not company_name or not address or not photo:
            flash('All fields including the photo are required.', 'danger')
            return redirect(url_for('register_distributor'))

        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            ext = filename.rsplit('.', 1)[1]
            unique_filename = f"{uuid4().hex}.{ext}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            photo.save(save_path)
        else:
            flash('Invalid passport photo format. Only jpg, jpeg, png allowed.', 'danger')
            return redirect(url_for('register_distributor'))

        distributor = Distributor(
        distributor_id=generate_distributor_id(),
        full_name=full_name,
        phone=phone,
        email=email,
        company_name=company_name,
        registration_number=registration_number,
        address=address,
        additional_info=additional_info,
        passport_photo=unique_filename
    )


        try:
            db.session.add(distributor)
            db.session.commit()
            base_dir = current_app.config['BASE_DIR']
            send_distributor_confirmation_email(distributor, app.config)
            flash('Distributor registered successfully!', 'success')
            return redirect(url_for('distributor_confirmation', distributor_id=distributor.distributor_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", 'danger')
            return redirect(url_for('register_distributor'))

    return render_template('user/register_distributor.html')



@app.route('/distributor/confirmation/<string:distributor_id>')
def distributor_confirmation(distributor_id):
    distributor = Distributor.query.filter_by(distributor_id=distributor_id).first_or_404()
    return render_template('user/confirmation.html', distributor=distributor)




class CustomPDF(FPDF):
    def __init__(self, app_config):
        super().__init__()
        self.app_config = app_config

    def header(self):
        # Set background white
        self.set_fill_color(255, 255, 255)
        self.rect(0, 0, 210, 40, 'F')  # White background for header

        # Logo
        logo_path = os.path.join(self.app_config['BASE_DIR'], 'static/images/letterhead_logo.jpg')
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 25)  # x, y, width

        # Company name and website (aligned beside logo)
        self.set_xy(40, 10)
        self.set_text_color(0, 128, 0)  # Green color
        self.set_font('Arial', 'B', 16)
        self.cell(100, 8, 'ECOSUN SOLAR POWER LIMITED', ln=True)

        self.set_x(40)
        self.set_font('Arial', '', 10)
        self.cell(100, 5, 'www.ecosunsolarpower.com', ln=True)

        # Horizontal line after header
        self.set_line_width(0.5)
        self.set_draw_color(0, 128, 0)  # Green
        # self.line(10, 38, 200, 38)
        current_y = self.get_y()  # Get current Y position after website
        self.line(10, current_y + 7, 200, current_y + 7)  # Little gap of 2 units below website

        self.ln(5)

    def footer(self):
        # Horizontal line above footer
        self.set_y(-30)
        self.set_line_width(0.5)
        self.set_draw_color(0, 128, 0)  # Green
        self.line(8, self.get_y(), 200, self.get_y())

        # Set footer text
        self.set_y(-25)
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 128, 0)

        # Abuja Office (left)
        self.set_x(10)
        self.multi_cell(90, 5,
            "Abuja Office:\nSuite A27 Yemi Plaza Gudu FCT Abuja, Nigeria\nPhone: +2348034833305\nEmail: abujaoffice@ecosunsolarpower.com"
        )

        # Lagos Office (right)
        self.set_y(-25)
        self.set_x(110)
        self.multi_cell(90, 5,
            "Lagos Office:\nUche Ubochi Close, Beside Total Energy Oil\nAlaba Int'l Market, Lagos, Nigeria\nPhone: +2348038664269\nEmail:lagosoffice@ecosunsolarpower.com"
        )

         


            



    def distributor_details(self, distributor_data, distributor_image):
        self.ln(10)

        # Add user image if available
        if distributor_image and os.path.exists(distributor_image):
            self.image(distributor_image, x=130, y=self.get_y() + 3, w=40)
        else:
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, "No image available", ln=True)

        self.ln(40)  # Adjusted spacing after image

        # Salutation
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f"Dear {distributor_data['Full Name'].split()[0]},", ln=True)

       
        self.set_font('Arial', 'B', 16)
        title = 'CONFIRMATION OF REGISTRATION'
        self.cell(0, 10, title, ln=True, align='C')

        

        # Welcome paragraph
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 8,
            "Welcome to Ecosun Solar Power Limited! We appreciate your interest in partnering with us as a distributor. "
            "Our team is reviewing your application and will reach out to you within two (2) working days. "
            "Please find below the summary of your registration details:")

        self.ln(6)

        # Table of registration details
        self.set_font('Arial', '', 11)
        col_widths = [60, 120]  # Adjusted widths
        line_height = self.font_size * 1.6

        for key, value in distributor_data.items():
            self.cell(col_widths[0], line_height, key.replace('_', ' ').title(), border=1)
            self.cell(col_widths[1], line_height, str(value), border=1)
            self.ln(line_height)

        self.ln(10)

        # Closing
        self.set_font('Arial', '', 12)
        self.cell(0, 10, 'Accept my highest regards.', ln=True)
        self.cell(0, 10, 'Yours sincerely.', ln=True)
        

        signature_path = os.path.normpath(os.path.join(self.app_config['BASE_DIR'], 'static/images/signature.png'))
        if os.path.exists(signature_path):
            self.image(signature_path, x=10, y=self.get_y(), w=40)
            self.ln(30)            
        else:
            self.cell(0, 10, "E-Signature", ln=True)

        self.set_font('Arial', '', 12)
        self.cell(0, 10, 'Sunday Mboyi', ln=True)
        self.cell(0, 10, 'Managing Director', ln=True)





def send_distributor_confirmation_email(distributor, app_config):
    try:
        pdf = CustomPDF(app_config)
        pdf.add_page()

        distributor_data = {
            "Full Name": distributor.full_name,
            "Ref No": distributor.distributor_id,
            "Phone Number": distributor.phone,
            "Email": distributor.email,
            "Company/Business Name": distributor.company_name,
            "Company/Business Address": distributor.address,
            "Company Reg Number": distributor.registration_number,
            "Date of Reg": distributor.date_registered.strftime('%Y-%m-%d'),
        }

        image_path = os.path.join(app_config['UPLOAD_FOLDER'], distributor.passport_photo)
        if not os.path.exists(image_path):
            image_path = None

        pdf.distributor_details(distributor_data, distributor_image=image_path)
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        safe_filename = f"registration_summary_{secure_filename(distributor.full_name)}.pdf"

        subject = "Ecosun Distributor Registration Confirmation"
        message_body = f"""
        Dear {distributor.full_name},

        Thank you for registering with Ecosun Solar Power Ltd. Please find attached your registration summary for your reference.

        Best regards,
        Ecosun Solar Team
        """

        email = EmailMessage(
                subject=subject, 
                body=message_body, 
                from_email="support@ecosunsolarpower.com",
                to=[distributor.email])
        
        email.attach(filename=safe_filename, content=pdf_bytes, mimetype="application/pdf")
        email.send()

        return True
    except Exception as e:
        app.logger.error(f"Failed to send registration email: {e}")
        return False


