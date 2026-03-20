import json
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Text

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")


def build_database_uri() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    if database_url:
        if "sslmode=" not in database_url:
            separator = "&" if "?" in database_url else "?"
            database_url = f"{database_url}{separator}sslmode=require"
        return database_url

    return f"sqlite:///{BASE_DIR / 'app.db'}"


app.config["SQLALCHEMY_DATABASE_URI"] = build_database_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSON_SORT_KEYS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}


db = SQLAlchemy(app)


class Record(db.Model):
    __tablename__ = "records"

    id = db.Column(db.String(120), primary_key=True)
    record_type = db.Column(db.String(50), nullable=True, index=True)
    data = db.Column(Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        payload = json.loads(self.data)
        if not isinstance(payload, dict):
            raise ValueError("Stored record is not a JSON object")
        if "id" not in payload:
            payload["id"] = self.id
        if "type" not in payload and self.record_type:
            payload["type"] = self.record_type
        return payload


with app.app_context():
    db.create_all()


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "*")
    response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
    response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.route("/api/<path:_>", methods=["OPTIONS"])
@app.route("/<path:_>", methods=["OPTIONS"])
def options_handler(_):
    return ("", 204)


@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "controle-panes-api"})


@app.get("/api/records")
def list_records():
    records = Record.query.order_by(Record.created_at.asc(), Record.id.asc()).all()
    return jsonify([record.to_dict() for record in records])


@app.post("/api/records")
def create_record():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON inválido"}), 400

    record_id = str(payload.get("id", "")).strip()
    if not record_id:
        return jsonify({"error": "Campo 'id' é obrigatório"}), 400

    existing = db.session.get(Record, record_id)
    if existing is not None:
        return jsonify({"error": "Já existe um registro com este id"}), 409

    record = Record(
        id=record_id,
        record_type=str(payload.get("type", "")).strip() or None,
        data=json.dumps(payload, ensure_ascii=False),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({"isOk": True, "item": record.to_dict()}), 201


@app.put("/api/records/<record_id>")
def update_record(record_id: str):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON inválido"}), 400

    record = db.session.get(Record, record_id)
    if record is None:
        return jsonify({"error": "Registro não encontrado"}), 404

    payload["id"] = record_id
    record.record_type = str(payload.get("type", "")).strip() or None
    record.data = json.dumps(payload, ensure_ascii=False)
    record.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"isOk": True, "item": record.to_dict()})


@app.delete("/api/records/<record_id>")
def delete_record(record_id: str):
    record = db.session.get(Record, record_id)
    if record is None:
        return jsonify({"error": "Registro não encontrado"}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({"isOk": True, "deletedId": record_id})


@app.delete("/api/records")
def delete_record_from_body():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON inválido"}), 400

    record_id = str(payload.get("id", "")).strip()
    if not record_id:
        return jsonify({"error": "Campo 'id' é obrigatório"}), 400
    return delete_record(record_id)


@app.get("/")
def index():
    candidates = [
        "codigo_render_api.html",
        "index.html",
        "codigo completo.html",
    ]
    for filename in candidates:
        file_path = BASE_DIR / filename
        if file_path.exists():
            return send_from_directory(BASE_DIR, filename)
    return jsonify(
        {
            "ok": True,
            "message": "API online. Coloque seu HTML no mesmo diretório do app.py com o nome 'codigo_render_api.html' ou 'index.html'.",
        }
    )


@app.get("/<path:filename>")
def serve_static(filename: str):
    file_path = BASE_DIR / filename
    if file_path.exists() and file_path.is_file():
        return send_from_directory(BASE_DIR, filename)
    return jsonify({"error": "Arquivo não encontrado"}), 404


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
