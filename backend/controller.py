from service import generate_module
import sys
import time
from repository.service import chat_service
from repository.models import ChatQADubious
from repository.dao_impl import ChatQADubiousDAO, ChatQADAO, ChatSessionDAO
from typing import Dict, Any

class ConversationController:

    def get_all_conversations(self) -> Dict[int, Any]:
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


    def get_conversation_history(self, session_id):
        """获取指定会话的完整对话历史"""
        full_session_data = chat_service.get_session_with_qas(session_id)
        if not full_session_data or 'chat_qas' not in full_session_data:
            return "", None
        
        # 如果chat_qas列表为空，返回空历史
        if not full_session_data['chat_qas']:
            return "", None

        history = ""
        for i in range(len(full_session_data['chat_qas'])-1):  
            # 不包括最后一个未完成的QA
            qa = full_session_data['chat_qas'][i]
            aim = qa.get('aim', '')
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            emotion = qa.get('emotion', 'neutral')
            progress = qa.get('progress', '')
            history += f"aim: {aim}\nquestion: {question}\nanswer: {answer}\nemotion: {emotion}\nprogress: {progress}\n\n"
        qa = full_session_data['chat_qas'][-1]
        history += f"aim: {qa.get('aim', '')}\nquestion: {qa.get('question', '')}\nanswer: "
        
        return history, full_session_data['chat_qas'][-1]['id']


    def continue_conversation(self, session_id, user_input):
        history, qa_id = self.get_conversation_history(session_id)
        
        # 如果qa_id为None，说明会话不存在或没有问答记录
        if qa_id is None:
            yield {
                'type': 'error',
                'content': f'会话 {session_id} 不存在或没有问答记录',
                'data': {}
            }
            return
        
        context = history + f"{user_input}\n"
        response_data = {}
        for chunk in generate_module.generate_response_stream(context, user_input):
            if chunk['type'] == 'final':
                response_data = chunk['data']
            yield chunk

        # 更新最后一个问答记录
        last_qa_record = chat_service.qa_dao.get_by_id(qa_id)
        if last_qa_record:
            last_qa_record.answer = user_input
            last_qa_record.emotion = response_data.get('emotion', '')
            last_qa_record.progress = response_data.get('process', '')
            # 更新问答记录
            update_success = chat_service.qa_dao.update(last_qa_record)
            if update_success:
                print(f"已更新问答记录 ID: {last_qa_record.id}")

                dubious_list = response_data.get('dubious', [])
                
                # print(dubious_list)
                
                if dubious_list:
                    dubious_records = [
                        ChatQADubious(qa_id=last_qa_record.id, snippet=snippet)
                        for snippet in dubious_list
                    ]
                    chat_service.dubious_dao.create_batch(dubious_records)
                    print(f"已保存 {len(dubious_records)} 条可疑语句")
            else:
                print("更新问答记录失败")
        
        # 检查会话是否完成
        is_finished = response_data.get('is_finished', 0)
        if is_finished == 1 or is_finished == True:
            # 标记会话为完成
            session = chat_service.session_dao.get_by_id(session_id)
            if session:
                session.is_finished = True
                session.draft = response_data.get('draft', '')
                chat_service.session_dao.update(session)
                print(f"会话 ID: {session_id} 已标记为完成")
            return

        # 创建下一个问答记录
        next_qa_record = chat_service.add_qa_to_session(
            session_id=session_id,
            question=response_data.get('question', ''),
            answer=None,  # 等待用户回答
            aim=response_data.get('aim', ''),
            emotion=None,
            progress=None
        )
        if next_qa_record:
            print(f"已创建新问答记录 ID: {next_qa_record.id}")
        else:
            print("创建新问答记录失败")


    def start_new_conversation(self, initial_input):
        """开始新对话"""
        session = chat_service.create_new_session()
        print(f"已创建新会话，ID: {session.id}")
        # 创建第一个问答记录
        first_qa = chat_service.add_qa_to_session(
            session_id=session.id,
            question='请填写受访者基础信息',
            answer=None,
            aim='获取基础信息',
            emotion=None,
            progress=None
        )
        print(f"已创建首个问答记录，ID: {first_qa.id}")
        
        for chunk in self.continue_conversation(session.id, initial_input):
            yield chunk