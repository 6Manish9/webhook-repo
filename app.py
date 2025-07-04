from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")  # Use MongoDB Atlas if needed
db = client["webhook_db"]
collection = db["events"]

@app.route('/webhook', methods=['POST'])
def github_webhook():
    payload = request.json
    headers = request.headers

    event_type = headers.get("X-GitHub-Event")

    try:
        if event_type == "push":
            data = {
                "action": "push",
                "author": payload["pusher"]["name"],
                "to_branch": payload["ref"].split('/')[-1],
                "timestamp": datetime.utcnow().isoformat()
            }
        elif event_type == "pull_request":
            pr_action = payload["action"]
            if pr_action in ["opened", "closed"] and payload["pull_request"].get("merged", False):
                data = {
                    "action": "merge",
                    "author": payload["sender"]["login"],
                    "from_branch": payload["pull_request"]["head"]["ref"],
                    "to_branch": payload["pull_request"]["base"]["ref"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                data = {
                    "action": "pull_request",
                    "author": payload["sender"]["login"],
                    "from_branch": payload["pull_request"]["head"]["ref"],
                    "to_branch": payload["pull_request"]["base"]["ref"],
                    "timestamp": datetime.utcnow().isoformat()
                }
        else:
            return "Unsupported event", 400

        collection.insert_one(data)
        return "Success", 200
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(port=5000)
