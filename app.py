from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
import qrcode
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
db = SQLAlchemy(app)

# Modelos
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    meal_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student', backref=db.backref('requests', lazy=True))

# Ruta para la página principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para registrar al usuario
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        new_student = Student(name=name, email=email, password=password)
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Ruta para iniciar sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        student = Student.query.filter_by(email=email, password=password).first()
        if student:
            session['student_id'] = student.id
            session['student_name'] = student.name
            return redirect(url_for('generate_qr'))
    return render_template('login.html')

# Ruta para generar el QR
@app.route('/generate-qr', methods=['GET', 'POST'])
def generate_qr():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        meal_type = request.form['meal_type']  # "Desayuno" o "Almuerzo"
        current_date = datetime.now().strftime('%Y-%m-%d')
        student_id = session['student_id']
        student_name = session['student_name']
        
        # Crear un nuevo registro de solicitud
        new_request = Request(student_id=student_id, meal_type=meal_type)
        db.session.add(new_request)
        db.session.commit()
        
        # Crear el enlace para la confirmación
        confirmation_link = url_for('confirmation', student_id=student_id, _external=True)
        
        # Datos a codificar en el QR
        qr_data = f"{confirmation_link}"
        
        # Generar el código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Crear una imagen del código QR
        img = qr.make_image(fill='black', back_color='white')
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    
    return render_template('generate_qr.html')


# Ruta para la página de confirmación
@app.route('/confirmation/<int:student_id>')
def confirmation(student_id):
    if 'student_id' not in session or session['student_id'] != student_id:
        return redirect(url_for('login'))
    
    # Contar el número de solicitudes de desayuno y almuerzo
    breakfast_count = Request.query.filter_by(student_id=student_id, meal_type='Desayuno').count()
    lunch_count = Request.query.filter_by(student_id=student_id, meal_type='Almuerzo').count()
    
    return render_template('confirmation.html', breakfast_count=breakfast_count, lunch_count=lunch_count)

# Ruta para el formulario de contacto
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Aquí puedes agregar la lógica para manejar el mensaje, como enviarlo por correo electrónico o guardarlo en una base de datos.
        
        return render_template('contact_success.html', name=name)
    
    return render_template('contact.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea la base de datos y las tablas
    app.run(debug=True, port=5000)
