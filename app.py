from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__, static_folder=".", static_url_path="")

# Configuração do banco de dados (Render usa DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/controle_panes")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
CORS(app)

# -----------------------------
# MODELOS
# -----------------------------
class Aeronave(db.Model):
    __tablename__ = "aeronaves"
    id = db.Column(db.Integer, primary_key=True)
    prefixo = db.Column(db.String(20), unique=True, nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    foto = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    panes = db.relationship("Pane", backref="aeronave", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "prefixo": self.prefixo,
            "modelo": self.modelo,
            "foto": self.foto,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None
        }


class Pane(db.Model):
    __tablename__ = "panes"
    id = db.Column(db.Integer, primary_key=True)
    aeronave_id = db.Column(db.Integer, db.ForeignKey("aeronaves.id"), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    ata = db.Column(db.String(10), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # mecanico / avionico
    responsavel = db.Column(db.String(100), nullable=False)
    foto_url = db.Column(db.String(255))
    status = db.Column(db.String(30), default="lancada")
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    criado_por = db.Column(db.String(100))

    def to_dict(self):
        return {
            "id": self.id,
            "aeronave_id": self.aeronave_id,
            "descricao": self.descricao,
            "ata": self.ata,
            "tipo": self.tipo,
            "responsavel": self.responsavel,
            "foto_url": self.foto_url,
            "status": self.status,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "criado_por": self.criado_por
        }

# -----------------------------
# ROTAS DE API
# -----------------------------

@app.route("/api/aeronaves", methods=["GET"])
def listar_aeronaves():
    aeronaves = Aeronave.query.order_by(Aeronave.prefixo).all()
    return jsonify([a.to_dict() for a in aeronaves])


@app.route("/api/aeronaves", methods=["POST"])
def criar_aeronave():
    data = request.get_json()
    if not data or "prefixo" not in data or "modelo" not in data:
        return jsonify({"status": "erro", "mensagem": "Dados incompletos"}), 400

    if Aeronave.query.filter_by(prefixo=data["prefixo"]).first():
        return jsonify({"status": "erro", "mensagem": "Prefixo já existe"}), 400

    nova = Aeronave(
        prefixo=data["prefixo"],
        modelo=data["modelo"],
        foto=data.get("foto")
    )
    db.session.add(nova)
    db.session.commit()
    return jsonify({"status": "ok", "aeronave": nova.to_dict()})


@app.route("/api/aeronaves/<int:aeronave_id>", methods=["DELETE"])
def deletar_aeronave(aeronave_id):
    aeronave = Aeronave.query.get(aeronave_id)
    if not aeronave:
        return jsonify({"status": "erro", "mensagem": "Aeronave não encontrada"}), 404

    db.session.delete(aeronave)
    db.session.commit()
    return jsonify({"status": "ok"})

# -----------------------------
# PANES
# -----------------------------
@app.route("/api/panes", methods=["GET"])
def listar_panes():
    panes = Pane.query.all()
    return jsonify([p.to_dict() for p in panes])


@app.route("/api/panes", methods=["POST"])
def criar_pane():
    data = request.get_json()
    if not data or "aeronave_id" not in data or "descricao" not in data:
        return jsonify({"status": "erro", "mensagem": "Dados incompletos"}), 400

    nova = Pane(
        aeronave_id=data["aeronave_id"],
        descricao=data["descricao"],
        ata=data.get("ata", "00"),
        tipo=data.get("tipo", "mecanico"),
        responsavel=data.get("responsavel", "Desconhecido"),
        foto_url=data.get("foto_url"),
        status=data.get("status", "lancada"),
        criado_por=data.get("criado_por")
    )
    db.session.add(nova)
    db.session.commit()
    return jsonify({"status": "ok", "pane": nova.to_dict()})

@app.route("/api/panes/<int:pane_id>", methods=["DELETE"])
def deletar_pane(pane_id):
    pane = Pane.query.get(pane_id)
    if not pane:
        return jsonify({"status": "erro", "mensagem": "Pane não encontrada"}), 404

    db.session.delete(pane)
    db.session.commit()
    return jsonify({"status": "ok"})


@app.route("/api/panes/<int:pane_id>", methods=["PUT"])
def atualizar_pane(pane_id):
    pane = Pane.query.get(pane_id)
    if not pane:
        return jsonify({"status": "erro", "mensagem": "Pane não encontrada"}), 404

    data = request.get_json()
    for campo in ["descricao", "ata", "tipo", "responsavel", "foto_url", "status"]:
        if campo in data:
            setattr(pane, campo, data[campo])

    db.session.commit()
    return jsonify({"status": "ok", "pane": pane.to_dict()})

# -----------------------------
# PENDENCIAS
# -----------------------------
@app.route("/api/pendencias", methods=["POST"])
def criar_pendencia():

    data = request.get_json()

    nova = Pendencia(
        pane_id=data["pane_id"],
        tipo_item=data["tipo_item"],
        tipo_aquisicao=data["tipo_aquisicao"],
        usuario=data["usuario"],
        login_usuario=data["login_usuario"],
        descricao_material=data.get("descricao_material"),
        part_number=data.get("part_number"),
        sms=data.get("sms"),
        task_card=data.get("task_card"),
        criado_em=datetime.utcnow()
    )

    db.session.add(nova)
    db.session.commit()

    return jsonify({"status": "ok"})

# -----------------------------
# SERVE FRONT-END
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -----------------------------
# INICIALIZAÇÃO
# -----------------------------

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



