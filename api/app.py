import os
import logging
from flask import Flask, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")
POOL_SIZE = int(os.getenv("POOL_SIZE", "5"))


@app.route("/health")
def health():
    return jsonify({"status": "ok", "pool_size": POOL_SIZE})


@app.route("/")
def index():
    return jsonify({"service": "api", "database": bool(DATABASE_URL)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
