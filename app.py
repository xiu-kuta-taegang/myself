from flask import Flask, render_template, request, jsonify
import requests
import json
import os

app = Flask(__name__)
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # 初始数据结构
    return {
        "user_a": {"name": "我", "calories": 0, "study_minutes": 0, "foods": []},
        "user_b": {"name": "对方", "calories": 0, "study_minutes": 0, "foods": []}
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search")
def search():
    name = request.args.get("q", "").strip()
    if not name:
        return jsonify([])
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5,
        "fields": "product_name,nutriments"
    }
    headers = {"User-Agent": "CoupleCalorieApp/1.0 (test@example.com)"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        results = []
        for p in data.get("products", []):
            kcal = p.get("nutriments", {}).get("energy-kcal_100g")
            if kcal is not None:
                results.append({
                    "name": p.get("product_name", "未知"),
                    "kcal_per_100g": round(float(kcal), 1)
                })
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/add_food", methods=["POST"])
def add_food():
    body = request.json
    user = body["user"]
    food_name = body["food_name"]
    grams = float(body["grams"])
    kcal_per_100g = float(body["kcal_per_100g"])
    total = round(kcal_per_100g * grams / 100, 1)

    data = load_data()
    data[user]["calories"] = round(data[user]["calories"] + total, 1)
    data[user]["foods"].append({
        "name": food_name, "grams": grams, "kcal": total
    })
    save_data(data)
    return jsonify({"total": total, "day_calories": data[user]["calories"]})

@app.route("/api/study", methods=["POST"])
def study():
    body = request.json
    user = body["user"]
    minutes = int(body["minutes"])
    data = load_data()
    data[user]["study_minutes"] += minutes
    save_data(data)
    return jsonify({"study_minutes": data[user]["study_minutes"]})

@app.route("/api/data")
def get_data():
    return jsonify(load_data())

@app.route("/api/reset", methods=["POST"])
def reset():
    save_data({
        "user_a": {"name": "我", "calories": 0, "study_minutes": 0, "foods": []},
        "user_b": {"name": "对方", "calories": 0, "study_minutes": 0, "foods": []}
    })
    return jsonify({"ok": True})
@app.route("/api/update_name", methods=["POST"])
def update_name():
    body = request.json
    user = body["user"]
    new_name = body["name"].strip()
    if not new_name:
        return jsonify({"error": "名字不能为空"}), 400
        
    data = load_data()
    data[user]["name"] = new_name
    save_data(data)
    return jsonify({"ok": True})
if __name__ == "__main__":
    # 部署到公网时，需要监听 0.0.0.0 并获取平台提供的端口
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
