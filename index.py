from flask import Flask, request, make_response, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

app = Flask(__name__)

# 初始化 Firebase (使用環境變數或本機金鑰)
# 若在 Vercel 部署，請將金鑰內容設為環境變數 FIREBASE_KEY
if not firebase_admin._apps:
    try:
        # 嘗試從環境變數讀取金鑰
        firebase_key = json.loads(os.environ.get("FIREBASE_KEY", "{}"))
        if firebase_key:
            cred = credentials.Certificate(firebase_key)
        else:
            # 本機測試用，請下載金鑰檔並放在同目錄
            cred = credentials.Certificate("firebase-key.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print("Firebase 初始化錯誤:", e)

db = firestore.client()

@app.route("/", methods=["GET"])
def home():
    return "電影聊天機器人 Webhook 運作中 🎬"

@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    action = req.get("queryResult", {}).get("action")

    if action == "rateChoice":
        rate = req["queryResult"]["parameters"].get("rate")
        return handle_rate_choice(rate)
    
    elif action == "searchByKeyword":
        keyword = req["queryResult"]["parameters"].get("keyword")
        return handle_search_by_keyword(keyword)
    
    else:
        return make_response(jsonify({
            "fulfillmentText": "我還不懂這個功能，請試試查詢分級（例如：普遍級電影）或輸入片名關鍵字（例如：查詢「玩命」相關電影）。"
        }))

def handle_rate_choice(rate):
    """根據電影分級查詢"""
    try:
        collection_ref = db.collection("電影含分級")
        docs = collection_ref.get()
        result = f"🎬 您選擇的電影分級是：{rate}\n\n相關電影：\n"
        found = False

        for doc in docs:
            movie = doc.to_dict()
            if rate in movie.get("rate", ""):
                found = True
                result += f"📽️ 片名：{movie.get('title', '未知')}\n"
                result += f"🔗 介紹：{movie.get('hyperlink', '無')}\n"
                if movie.get("poster"):
                    result += f"🖼️ 海報：{movie.get('poster')}\n"
                result += "\n"

        if not found:
            result = f"找不到「{rate}」的電影，請確認分級是否正確（普遍級、保護級、輔12級、輔15級、限制級）。"

        return make_response(jsonify({"fulfillmentText": result}))
    
    except Exception as e:
        return make_response(jsonify({"fulfillmentText": f"查詢電影分級時發生錯誤：{str(e)}"}))

def handle_search_by_keyword(keyword):
    """根據片名關鍵字查詢"""
    try:
        collection_ref = db.collection("電影含分級")
        docs = collection_ref.get()
        result = f"🔍 以下是含有「{keyword}」的電影：\n\n"
        found = False

        for doc in docs:
            movie = doc.to_dict()
            title = movie.get("title", "")
            if keyword.lower() in title.lower():
                found = True
                result += f"🎬 片名：{title}\n"
                result += f"🔗 介紹：{movie.get('hyperlink', '無')}\n"
                if movie.get("poster"):
                    result += f"🖼️ 海報：{movie.get('poster')}\n"
                result += "\n"

        if not found:
            result = f"❌ 找不到含有「{keyword}」的電影，請試試其他關鍵字。"

        return make_response(jsonify({"fulfillmentText": result}))
    
    except Exception as e:
        return make_response(jsonify({"fulfillmentText": f"查詢關鍵字時發生錯誤：{str(e)}"}))

if __name__ == "__main__":
    app.run(debug=True)
