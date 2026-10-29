from flask import Flask, request, jsonify, send_file
import requests
from urllib.parse import quote
import time
import os

app = Flask(__name__)

BASE = os.environ["BASE_URL"]
KEY = os.environ["API_KEY"]
TIMEOUT = 30

# service name -> query parameter name in the upstream API
SERVICES = {
    "num_info":          "num",
    "vehicle_full":      "xr",
    "vehicle_to_number": "xr",
    "pan2dob_name":      "pan2dob_name",
    "aadhaar2pan":       "aadhaar2pan",
    "imei":              "imei",
    "pincode":           "pincode",
    "ifse":              "ifse",
    "tg":                "q",
    "addhaar2num":       "q",
}

HERE = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
def index():
    return send_file(os.path.join(HERE, "index.html"))


@app.route("/api/lookup", methods=["POST"])
def lookup():
    data = request.get_json(silent=True) or {}
    service = (data.get("service") or "").strip()
    query   = (data.get("query") or "").strip()

    if service not in SERVICES:
        return jsonify({"ok": False, "error": f"unknown service: {service}"}), 400
    if not query:
        return jsonify({"ok": False, "error": "query is empty"}), 400

    param = SERVICES[service]
    url = f"{BASE}?={service}&key={KEY}&{param}={quote(query)}"

    t0 = time.time()
    try:
        r = requests.get(url, timeout=TIMEOUT)
        elapsed = round(time.time() - t0, 2)

        try:
            payload = r.json()
        except ValueError:
            return jsonify({
                "ok": False,
                "elapsed": elapsed,
                "error": f"upstream returned non-JSON (HTTP {r.status_code})",
                "raw": r.text[:500],
            }), 502

        return jsonify({
            "ok": True,
            "service": service,
            "query": query,
            "elapsed": elapsed,
            "http_status": r.status_code,
            "data": payload,
        })

    except requests.exceptions.Timeout:
        return jsonify({"ok": False, "error": "upstream API timed out"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"ok": False, "error": f"request failed: {e}"}), 502


if __name__ == "__main__":
    app.run(debug=True, port=5000)
