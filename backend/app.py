from flask import Flask, jsonify
from flask_cors import CORS  # 导入 CORS

app = Flask(__name__)
CORS(app)  # 启用跨域请求支持
@app.route('/')
def home():
    return "Welcome to Flask!"  # 返回简单的文本或 HTML

@app.route('/api/data')
def get_data():
    return jsonify({'message': 'Hello from Flask!11111'})

if __name__ == '__main__':
    app.run(debug=True)

