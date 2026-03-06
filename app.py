from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# -----------------------------------
# DATABASE
# -----------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -----------------------------------
# MODELOS
# -----------------------------------

class Aeronave(db.Model):

    __tablename__ = "aeronaves"

    id = db.Column(db.Integer, primary_key=True)

    prefixo = db.Column(db.String(20), unique=True)
    modelo = db.Column(db.String(50))
    foto = db.Column(db.String(500))

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


class Pane(db.Model):

    __tablename__ = "panes"

    id = db.Column(db.Integer, primary_key=True)

    aeronave_id = db.Column(db.Integer)

    descricao = db.Column(db.Text)
    ata = db.Column(db.String(10))

    tipo = db.Column(db.String(20))
    responsavel = db.Column(db.String(100))

    foto_url = db.Column(db.String(500))

     = db.Column(db.String(20))

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    criado_por = db.Column(db.String(100))


class Etapa(db.Model):

    __tablename__ = "etapas"

    id = db.Column(db.Integer, primary_key=True)

    pane_id = db.Column(db.Integer)

    descricao = db.Column(db.Text)

    usuario = db.Column(db.String(100))
    login_usuario = db.Column(db.String(100))

    data = db.Column(db.DateTime)

    foto1 = db.Column(db.String(500))
    foto2 = db.Column(db.String(500))
    foto3 = db.Column(db.String(500))


class Pendencia(db.Model):

    __tablename__ = "pendencias"

    id = db.Column(db.Integer, primary_key=True)

    pane_id = db.Column(db.Integer)

    tipo_item = db.Column(db.String(50))
    tipo_aquisicao = db.Column(db.String(50))

    descricao_material = db.Column(db.Text)

    part_number = db.Column(db.String(100))

    sms = db.Column(db.String(100))
    task_card = db.Column(db.String(100))

    usuario = db.Column(db.String(100))


# -----------------------------------
# AERONAVES
# -----------------------------------

@app.route("/api/aeronaves", methods=["GET"])
def listar_aeronaves():

    aeronaves = Aeronave.query.order_by(Aeronave.prefixo).all()

    return jsonify([
        {
            "id": a.id,
            "prefixo": a.prefixo,
            "modelo": a.modelo,
            "foto": a.foto
        }
        for a in aeronaves
    ])


@app.route("/api/aeronaves", methods=["POST"])
def criar_aeronave():

    data = request.json

    nova = Aeronave(
        prefixo=data["prefixo"],
        modelo=data["modelo"],
        foto=data.get("foto")
    )

    db.session.add(nova)
    db.session.commit()

    return jsonify({"status":"ok"})

# -----------------------------------
# EXCLUIR AERONAVE
# -----------------------------------

@app.route("/api/aeronaves/<int:id>", methods=["DELETE"])
def excluir_aeronave(id):

    aeronave = Aeronave.query.get_or_404(id)

    db.session.delete(aeronave)
    db.session.commit()

    return jsonify({"success": True})

# -----------------------------------
# PANES
# -----------------------------------

@app.route("/api/panes", methods=["GET"])
def listar_panes():

    panes = Pane.query.all()

    return jsonify([
        {
            "id": p.id,
            "aeronave_id": p.aeronave_id,
            "descricao": p.descricao,
            "ata": p.ata,
            "tipo": p.tipo,
            "responsavel": p.responsavel,
            "foto_url": p.foto_url,
            "status": p.status
        }
        for p in panes
    ])


@app.route("/api/panes", methods=["POST"])
def criar_pane():

    data = request.json

    nova = Pane(
        aeronave_id=data["aeronave_id"],
        descricao=data["descricao"],
        ata=data["ata"],
        tipo=data["tipo"],
        responsavel=data["responsavel"],
        foto_url=data.get("foto_url"),
        status=data.get("status","lancada"),
        criado_por=data.get("criado_por")
    )

    db.session.add(nova)
    db.session.commit()

    return jsonify({"status":"ok"})


# -----------------------------------
# ETAPAS
# -----------------------------------

@app.route("/api/etapas", methods=["POST"])
def criar_etapa():

    data = request.json

    nova = Etapa(
        pane_id=data["pane_id"],
        descricao=data["descricao"],
        usuario=data["usuario"],
        login_usuario=data["login_usuario"],
        data=datetime.utcnow(),
        foto1=data.get("foto1"),
        foto2=data.get("foto2"),
        foto3=data.get("foto3")
    )

    db.session.add(nova)
    db.session.commit()

    return jsonify({"status":"ok"})


# -----------------------------------
# PENDENCIAS
# -----------------------------------

@app.route("/api/pendencias", methods=["POST"])
def criar_pendencia():

    data = request.json

    nova = Pendencia(
        pane_id=data["pane_id"],
        tipo_item=data["tipo_item"],
        tipo_aquisicao=data["tipo_aquisicao"],
        descricao_material=data["descricao_material"],
        part_number=data["part_number"],
        sms=data["sms"],
        task_card=data["task_card"],
        usuario=data["usuario"]
    )

    db.session.add(nova)
    db.session.commit()

    return jsonify({"status":"ok"})


# -----------------------------------
# SERVIR FRONT-END
# -----------------------------------

@app.route("/")
def home():
    return send_from_directory(".", "index.html")


# -----------------------------------
# START
# -----------------------------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT",5000))

    app.run(host="0.0.0.0", port=port)

