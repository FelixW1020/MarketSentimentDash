from flask import Flask, jsonify, render_template

import config
import pipeline
import store

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    try:
        tickers = config.TICKERS if config.TICKERS else None
        data = pipeline.run(tickers)
        # Return tickers in rank order
        ordered = sorted(data.values(), key=lambda v: v.get("rank") or 9999)
        return jsonify({"ok": True, "data": data, "tickers": [v["ticker"] for v in ordered]})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/history")
def api_history():
    try:
        store.init_db()
        history = store.get_mention_history()
        return jsonify({"ok": True, "history": history})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
