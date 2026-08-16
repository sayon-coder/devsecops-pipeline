from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "devsecops-demo"})

@app.route('/')
def home():
    return jsonify({"message": "DevSecOps Pipeline Running", "version": "1.0.0"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
