from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
import yagmail
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

db = SQLAlchemy(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    price = db.Column(db.Float)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()

    if user and check_password_hash(user.password, data['password']):
        token = create_access_token(identity=user.id)
        return {"token": token}

    return {"msg": "bad login"}, 401

@app.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    products = Product.query.all()
    return jsonify([{"id":p.id,"name":p.name,"price":p.price} for p in products])

@app.route('/order', methods=['POST'])
@jwt_required()
def create_order():
    data = request.json
    items = data['items']
    email = data['email']

    filename = "zamowienie.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Foodkreator - Zamówienie", ln=True)
    pdf.ln(10)

    for item in items:
        pdf.cell(200, 10, txt=f"{item['name']} - {item['qty']} szt.", ln=True)

    pdf.output(filename)

    yag = yagmail.SMTP("twoj_email@gmail.com", "pdny pffd pxvc dllq")
    yag.send(email, "Zamówienie", "W załączniku zamówienie", attachments=filename)

    return {"msg": "wysłano"}

if __name__ == "__main__":
    db.create_all()

    from werkzeug.security import generate_password_hash

    if not User.query.filter_by(username="admin").first():
        user = User(
            username="admin",
            password=generate_password_hash("admin123")
        )
        db.session.add(user)
        db.session.commit()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
