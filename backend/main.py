from flask import Flask, jsonify, request
from typing import Dict, Any
from repository.service import chat_service
from controller import ConversationController
import json

# 创建Flask应用实例
app = Flask(__name__)

controller = ConversationController()

@app.route('/dialogues', methods=['GET'])
def get_all_dialogues() -> Dict[int, Any]:
    """
    获取所有会话
    :return: 包含所有会话的字典，键为会话ID，值为会话详情（包含qas和dubious列表）
    """
    return controller.get_all_conversations()


@app.route('/start', methods=['POST'])
def start_conversation():
    """
    开始新对话 - 流式响应版本
    """
    initial_input = request.json.get("input", "")
    if not initial_input:
        return jsonify({"error": "Initial input is required"}), 400
    
    def generate():
        for chunk in controller.start_new_conversation(initial_input):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    from flask import Response
    return Response(generate(), mimetype='text/event-stream')


@app.route('/continue', methods=['POST'])
def continue_conversation():
    """
    继续对话 - 流式响应版本
    """
    session_id = request.json.get("session_id")
    user_input = request.json.get("input", "")
    
    if not session_id or not user_input:
        return jsonify({"error": "Session ID and user input are required"}), 400
    
    def generate():
        for chunk in controller.continue_conversation(session_id, user_input):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    from flask import Response
    return Response(generate(), mimetype='text/event-stream')


# 启动应用
if __name__ == '__main__':
    app.run(debug=True, port=5000)
    