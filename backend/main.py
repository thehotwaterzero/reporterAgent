from flask import Flask, jsonify, request
from typing import Dict, Any
from repository.service import chat_service
from controller import ConversationController
import json

# 创建Flask应用实例
app = Flask(__name__)

controller = ConversationController()

@app.route('/dialogues', methods=['GET'])
def get_all_dialogue() -> Dict[int, Any]:
    """
    获取所有会话
    :return: 包含所有会话的字典，键为会话ID，值为会话详情（包含qas和dubious列表）
    """
    sessions = chat_service.get_all_sessions()
    result = {}
    
    for session_id, session in sessions.items():
        # 直接使用session对象，但需要手动序列化关联数据
        qas_data = []
        
        # 获取该会话的所有QA记录
        qa_list = chat_service.qa_dao.get_by_session_id(session_id)
        
        for qa in qa_list:
            # 获取该QA的所有dubious记录
            dubious_list = chat_service.dubious_dao.get_by_qa_id(qa.id)
            dubious_data = [
                {
                    "id": dubious.id,
                    "snippet": dubious.snippet
                }
                for dubious in dubious_list
            ]
            
            qa_item = {
                "id": qa.id,
                "question": qa.question,
                "answer": qa.answer,
                "aim": qa.aim,
                "emotion": qa.emotion,
                "progress": qa.progress,
                "created_at": qa.created_at.isoformat() if qa.created_at else None,
                "updated_at": qa.updated_at.isoformat() if qa.updated_at else None,
                "dubious": dubious_data
            }
            qas_data.append(qa_item)
        
        result[session_id] = {
            "id": session.id,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "is_finished": session.is_finished,
            "draft": session.draft,
            "qas": qas_data
        }
    
    return result

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
    