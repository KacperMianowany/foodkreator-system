from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
import yagmail
import os

app = Flask(__name__)

# ===== CORS =====
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# ===== MODELE =====
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    price = db.Column(db.Float)

# ===== INIT DB (NA RENDER) =====
with app.app_context():
    db.create_all()

    # produkty tylko jeśli brak
    if Product.query.count() == 0:

        produkty = [

        # ===== 400g =====
        {"name":"Pierogi ruskie 400g", "price":8.99},
        {"name":"Pierogi z mięsem 400g", "price":12.50},
        {"name":"Pierogi z kapustą 400g", "price":9.75},
        {"name":"Kopytka 400g", "price":7.45},
        {"name":"Leniwe 400g", "price":8.75},
        {"name":"Pierogi z serem 400g", "price":10.50},
        {"name":"Pierogi szpinak + ser 400g", "price":10.90},
        {"name":"Pierogi z soczewicą 400g", "price":8.40},
        {"name":"Pierogi kaczka + jabłko 400g", "price":16.99},
        {"name":"Pierogi ruskie tofu VEGE 320g", "price":9.90},
        {"name":"Pierogi masala VEGE 320g", "price":7.99},
        {"name":"Pierogi wiejskie 400g", "price":9.25},

        # ===== 1kg =====
        {"name":"Pierogi ruskie 1kg", "price":16.95},
        {"name":"Pierogi z mięsem 1kg", "price":24.95},
        {"name":"Pierogi z kapustą 1kg", "price":18.75},
        {"name":"Kopytka 1kg", "price":14.95},
        {"name":"Pierogi z serem 1kg", "price":19.95},
        {"name":"Pierogi szpinak + ser 1kg", "price":19.95},
        {"name":"Pierogi z soczewicą 1kg", "price":15.95},
        {"name":"Pierogi wiejskie 1kg", "price":17.95},
        {"name":"Uszka z grzybami 1kg", "price":42.50},

        # ===== DANIA =====
        {"name":"Penne kurczak + suszone pomidory 360g", "price":9.50},
        {"name":"Gulasz wieprzowy + kasza bulgur 360g", "price":8.20},
        {"name":"Łazanki 360g", "price":8.20},
        {"name":"Tortilla burrito", "price":11.49},
        {"name":"Tortilla z kurczakiem", "price":11.49},
        {"name":"Naleśniki z serem 400g", "price":10.50},
        {"name":"Naleśniki z jabłkami 400g", "price":9.80},

        # ===== SEZONOWE =====
        {"name":"Pierogi truskawka 400g", "price":8.99},
        {"name":"Pierogi wiśnia 400g", "price":9.50},
        {"name":"Pierogi jagoda 400g", "price":12.90},
        {"name":"Uszka z grzybami 400g", "price":17.50},

        ]

        for p in produkty:
            db.session.add(Product(name=p["name"], price=p["price"]))

        db.session.commit()

    # admin
    if not User.query.filter_by(username="admin").first():
        user = User(
            username="admin",
            password=generate_password_hash("admin123")
        )
        db.session.add(user)
        db.session.commit()

# ===== LOGIN =====
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()

    if user and check_password_hash(user.password, data['password']):
        token = create_access_token(identity=user.id)
        return {"token": token}

    return {"msg": "bad login"}, 401

# ===== OPTIONS =====
@app.route('/login', methods=['OPTIONS'])
def login_options():
    response = jsonify({})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response

# ===== PRODUKTY =====
@app.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    products = Product.query.all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "price": p.price
    } for p in products])

# ===== ZAMÓWIENIE =====
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

    yag = yagmail.SMTP(
        os.environ.get("EMAIL"),
        os.environ.get("EMAIL_PASS")
    )

    yag.send(email, "Zamówienie", "W załączniku zamówienie", attachments=filename)

    return {"msg": "wysłano"}

# ===== GLOBALNY CORS =====
@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

# ===== START =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
