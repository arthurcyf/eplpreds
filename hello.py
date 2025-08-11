from flask import Flask
app = Flask(__name__)

@app.get("/health")
def health():
    return {"ok": True}

if __name__ == "__main__":
    print("Starting Flask on http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=True)