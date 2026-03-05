from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# pegar URL do banco criada no Render
DATABASE_URL = os.getenv("DATABASE_URL")

# correção necessária para PostgreSQL no Render
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ----------------------------
# Modelo da tabela
# ----------------------------

class Pane(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aeronave = db.Column(db.String(50))
    descricao = db.Column(db.Text)


# ----------------------------
# Criar tabelas automaticamente
# ----------------------------

with app.app_context():
    db.create_all()


# ----------------------------
# Rotas
# ----------------------------

@app.route("/")
def home():
    return render_template("index.html")


# listar panes
@app.route("/api/panes", methods=["GET"])
def listar_panes():
    panes = Pane.query.all()

    lista = []
    for p in panes:
        lista.append({
            "id": p.id,
            "aeronave": p.aeronave,
            "descricao": p.descricao
        })

    return jsonify(lista)


# criar pane
@app.route("/api/panes", methods=["POST"])
def criar_pane():
    data = request.json

    pane = Pane(
        aeronave=data["aeronave"],
        descricao=data["descricao"]
    )

    db.session.add(pane)
    db.session.commit()

    return jsonify({"status": "ok"})


# ----------------------------
# iniciar servidor
# ----------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)