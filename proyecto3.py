from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-password'
app.config['MAIL_USE_TLS'] = True

db = SQLAlchemy(app)
ma = Marshmallow(app)
mail = Mail(app)

# Modelo de Empleado
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    role = db.Column(db.String(100))
    hourly_rate = db.Column(db.Float)
    hours_worked = db.Column(db.Float)

# Esquema de Empleado
class EmployeeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Employee
        include_relationships = True
        load_instance = True


employee_schema = EmployeeSchema()
employees_schema = EmployeeSchema(many=True)

# Rutas de la API

# Endpoint para crear un nuevo empleado
@app.route('/employee', methods=['POST'])
def add_employee():
    name = request.json['name']
    email = request.json['email']
    role = request.json['role']
    hourly_rate = request.json['hourly_rate']
    hours_worked = request.json['hours_worked']
    new_employee = Employee(name=name, email=email, role=role, hourly_rate=hourly_rate, hours_worked=hours_worked)
    db.session.add(new_employee)
    db.session.commit()
    return employee_schema.jsonify(new_employee)

# Endpoint para obtener todos los empleados
@app.route('/employee', methods=['GET'])
def get_employees():
    all_employees = Employee.query.all()
    result = employees_schema.dump(all_employees)
    return jsonify(result)

# Función para enviar correos electrónicos
def send_email(subject, recipient, body, attachment=None):
    msg = Message(subject, sender='your-email@example.com', recipients=[recipient])
    msg.body = body
    if attachment:
        with app.open_resource(attachment) as fp:
            msg.attach(attachment, "application/pdf", fp.read())
    mail.send(msg)

# Función para pagar la nómina diaria y enviar notificaciones por correo electrónico
def pay_salaries():
    # Obtener la lista de empleados
    employees = Employee.query.all()
    
    # Iterar sobre la lista de empleados y realizar el pago de nómina
    for employee in employees:
        salary = calculate_salary(employee)
        pdf_path = generate_paystub(employee, salary)
        send_paystub_email(employee.email, pdf_path)

def calculate_salary(employee):
    return employee.hourly_rate * employee.hours_worked

def generate_paystub(employee, salary):
    pdf_path = f"paystubs/{employee.id}_paystub.pdf"
    # Código para generar el PDF y guardarlo en la ruta especificada
    return pdf_path

def send_paystub_email(recipient_email, pdf_path):
    subject = 'Desprendible de pago'
    body = 'Adjunto encontrará su desprendible de pago.'
    send_email(subject, recipient_email, body, pdf_path)


# Crear un programador de tareas
scheduler = BackgroundScheduler()
scheduler.start()

# Programar el pago de nómina diario a las 6 pm
scheduler.add_job(pay_salaries, 'cron', hour=18)

if __name__ == '__main__':
    app.run(debug=True)