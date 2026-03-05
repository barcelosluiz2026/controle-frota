from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# conexão com banco Render
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -------------------------------
# MODELOS DO BANCO
# -------------------------------

class Aeronave(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prefixo = db.Column(db.String(20), unique=True, nullable=False)
    modelo = db.Column(db.String(100))
    foto = db.Column(db.String(500))


class Pane(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aeronave = db.Column(db.String(50))
    descricao = db.Column(db.Text)


# -------------------------------
# ROTAS HTML
# -------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -------------------------------
# API AERONAVES
# -------------------------------

@app.route("/api/aeronaves", methods=["GET"])
def listar_aeronaves():

    aeronaves = Aeronave.query.all()

    lista = []

    for a in aeronaves:
        lista.append({
            "id": a.id,
            "prefixo": a.prefixo,
            "modelo": a.modelo,
            "foto": a.foto
        })

    return jsonify(lista)


@app.route("/api/aeronaves", methods=["POST"])
def criar_aeronave():

    data = request.json

    prefixo = data.get("prefixo")
    modelo = data.get("modelo")
    foto = data.get("foto")

    aeronave = Aeronave(
        prefixo=prefixo,
        modelo=modelo,
        foto=foto
    )

    db.session.add(aeronave)
    db.session.commit()

    return jsonify({"status": "ok"})


# -------------------------------
# API PANES
# -------------------------------

@app.route("/api/panes", methods=["GET", "POST"])
def api_panes():

    # LISTAR PANES
    if request.method == "GET":

        panes = Pane.query.all()

        lista = []
        for p in panes:
            lista.append({
                "id": p.id,
                "aeronave": p.aeronave,
                "descricao": p.descricao
            })

        return jsonify(lista)


    # CRIAR NOVA PANE
    if request.method == "POST":

        data = request.get_json()

        nova = Pane(
            aeronave=data.get("aeronave"),
            descricao=data.get("descricao")
        )

        db.session.add(nova)
        db.session.commit()

        return jsonify({"success": True})

# -------------------------------
# INICIALIZAÇÃO
# -------------------------------

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()

# ======================
# RESET BANCO
# ======================

@app.route("/api/reset_db")
def reset_db():
    db.drop_all()
    db.create_all()
    return "Banco recriado com sucesso!"





