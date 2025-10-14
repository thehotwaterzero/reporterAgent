#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
对话服务模块
提供统一的对话管理功能，包括新对话、继续对话等核心逻辑
"""

import time
from typing import Optional, Dict, Any
from . import generate_module
from repository.service import chat_service
from repository.models import ChatQADubious


def print_with_typing_effect(text, delay=0.03):
    """打字机效果输出"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


def print_status_with_dots(text, duration=1.0):
    """带动态点的状态显示"""
    print(text, end='', flush=True)
    for _ in range(int(duration * 10)):
        print('.', end='', flush=True)
        time.sleep(0.1)
    print()


def handle_ai_interaction(conversation_history: str, user_input: str) -> Optional[Dict[str, Any]]:
    """处理AI交互流程，返回响应数据"""
    print("\n" + "🔄 " + "=" * 48)
    print("🤖 AI正在处理您的回答...")
    print("=" * 50)
    
    response_data = None
    for stream_chunk in generate_module.generate_response_stream(conversation_history, user_input, debug=False):
        if stream_chunk['type'] == 'status':
            print_status_with_dots(f"   {stream_chunk['content']}", 0.5)
        elif stream_chunk['type'] == 'content':
            print(stream_chunk['content'], end='', flush=True)
        elif stream_chunk['type'] == 'final':
            response_data = stream_chunk['data']
            print_with_typing_effect(f"   {stream_chunk['content']}")
            break
        elif stream_chunk['type'] == 'error':
            print(f"\n❌ 错误: {stream_chunk['content']}")
            return None
    
    if not response_data:
        print("❌ 未能获取有效响应")
        return None
    
    return response_data


def save_qa_record(session_id: int, next_qa_id: Optional[int], current_question: str, 
                  current_aim: str, user_input: str, response_data: Dict[str, Any]) -> bool:
    """保存问答记录到数据库，返回是否成功"""
    try:
        if next_qa_id:
            # 更新预创建的问答记录
            from repository.dao_impl import ChatQADAO
            qa_dao = ChatQADAO()
            qa_record = qa_dao.get_by_id(next_qa_id)
            if qa_record:
                qa_record.answer = user_input
                qa_record.emotion = response_data.get('emotion', 'neutral')
                qa_record.progress = response_data.get('process', '')
                
                # 更新记录
                update_success = qa_dao.update(qa_record)
                if update_success:
                    print(f"💾 已更新问答记录 ID: {qa_record.id}")
                    
                    # 如果有可疑语句，添加它们
                    if response_data.get('dubious_snippets'):
                        from repository.dao_impl import ChatQADubiousDAO
                        dubious_dao = ChatQADubiousDAO()
                        dubious_records = [
                            ChatQADubious(qa_id=qa_record.id, snippet=snippet)
                            for snippet in response_data.get('dubious_snippets', [])
                        ]
                        dubious_dao.create_batch(dubious_records)
                        print(f"💾 已保存 {len(dubious_records)} 条可疑语句")
                    return True
                else:
                    print("❌ 更新问答记录失败")
                    return False
            else:
                print("❌ 未找到预创建的问答记录，创建新记录")
                qa_record = chat_service.complete_qa_interaction(
                    session_id=session_id,
                    question=current_question,
                    answer=user_input,
                    aim=current_aim,
                    emotion=response_data.get('emotion', 'neutral'),
                    progress=response_data.get('process', ''),
                    dubious_snippets=response_data.get('dubious_snippets', [])
                )
                print(f"💾 已保存新问答记录 ID: {qa_record.id}")
                return True
        else:
            # 如果没有预创建记录，使用原来的方式创建
            qa_record = chat_service.complete_qa_interaction(
                session_id=session_id,
                question=current_question,
                answer=user_input,
                aim=current_aim,
                emotion=response_data.get('emotion', 'neutral'),
                progress=response_data.get('process', ''),
                dubious_snippets=response_data.get('dubious_snippets', [])
            )
            print(f"💾 已保存问答记录 ID: {qa_record.id}")
            return True
    except Exception as e:
        print(f"❌ 保存问答记录失败: {e}")
        return False


def pre_create_next_qa(session_id: int, current_aim: str, current_question: str) -> Optional[int]:
    """预创建下一个问答记录，返回记录ID或None"""
    if current_aim and current_question:
        try:
            next_qa_record = chat_service.add_qa_to_session(
                session_id=session_id,
                question=current_question,
                answer=None,  # 等待用户回答
                aim=current_aim,
                emotion=None,
                progress=None
            )
            print(f"💾 已预创建下一轮问答记录 ID: {next_qa_record.id}")
            return next_qa_record.id
        except Exception as e:
            print(f"❌ 预创建问答记录失败: {e}")
            return None
    return None


def display_response_status(response_data: Dict[str, Any]) -> None:
    """显示响应状态信息"""
    print("\n" + "-" * 40)
    print_with_typing_effect(f"😊 情绪状态: {response_data.get('emotion', 'neutral')}")
    print_with_typing_effect(f"📊 进度: {response_data.get('process', '')}")
    print("-" * 40)
    print_with_typing_effect(f"🎯 目标: {response_data.get('aim', '')}")
    print_with_typing_effect(f"❓ 问题: {response_data.get('question', '')}")
    print("-" * 40)


def handle_conversation_completion(session_id: int, response_data: Dict[str, Any]) -> bool:
    """处理对话完成流程，返回是否成功"""
    try:
        final_draft = response_data.get('draft', '')
        chat_service.finish_session(session_id, final_draft)
        print(f"💾 对话完成，已保存最终稿件到会话 {session_id}")
        
        print("\n" + "=" * 50)
        print("✅ 对话已完成！")
        print("=" * 50)
        print("📄 生成稿件:")
        print("-" * 50)
        print_with_typing_effect(response_data.get('draft', ''), 0.02)
        return True
    except Exception as e:
        print(f"❌ 保存最终稿件失败: {e}")
        return False


def start_new_conversation() -> None:
    """开始新对话的完整流程"""
    print("=" * 50)
    print("🚀 新对话已开始，输入'退出'结束对话")
    print("=" * 50)
    print()

    # 创建新的数据库会话
    try:
        session_obj = chat_service.create_new_session()
        session_id = session_obj.id
        print(f"💾 已创建会话 ID: {session_id}")
        print("-" * 50)
    except Exception as e:
        print(f"❌ 创建会话失败: {e}")
        return

    conversation_history = ""
    current_question = ""
    current_aim = ""
    next_qa_id = None  # 用于跟踪预创建的问答记录ID

    while True:
        user_input = ""
        
        if not conversation_history:
            print("📋 基础信息收集")
            print("-" * 30)
            current_aim = "获取基础信息"
            current_question = "请填写受访者基础信息"
            
            # 立即为第一个问题创建问答记录
            try:
                first_qa_record = chat_service.add_qa_to_session(
                    session_id=session_id,
                    question=current_question,
                    answer=None,  # 等待用户回答
                    aim=current_aim,
                    emotion=None,
                    progress=None
                )
                next_qa_id = first_qa_record.id
                print(f"💾 已创建初始问答记录 ID: {next_qa_id}")
            except Exception as e:
                print(f"❌ 创建初始问答记录失败: {e}")
                next_qa_id = None
            
            system_message = f"🎯 目标: {current_aim}\n❓ 问题: {current_question}\n"
            print(system_message)
            
            user_input = input("💭 回答: ")

            if user_input.lower() == '退出':
                print("\n👋 对话结束，感谢您的参与！")
                break

            conversation_history += system_message + "\n"

        else:
            user_input = input("💭 回答: ")

            if user_input.lower() == '退出':
                print("\n👋 对话结束，感谢您的参与！")
                break

        conversation_history += f"answer : {user_input}\n"

        # 使用抽象的AI交互函数
        response_data = handle_ai_interaction(conversation_history, user_input)
        if not response_data:
            return

        # 使用抽象的保存函数
        save_success = save_qa_record(session_id, next_qa_id, current_question, current_aim, user_input, response_data)
        if not save_success:
            print("⚠️ 保存失败，但继续对话...")

        if response_data['is_finished']:
            # 使用抽象的完成处理函数
            handle_conversation_completion(session_id, response_data)
            break

        # 使用抽象的状态显示函数
        display_response_status(response_data)

        # 更新当前问题和目标，用于下一轮保存
        current_aim = response_data.get('aim', '')
        current_question = response_data.get('question', '')

        # 使用抽象的预创建函数
        next_qa_id = pre_create_next_qa(session_id, current_aim, current_question)

        system_message = f"emotion : {response_data.get('emotion', 'neutral')}\nprocess : {response_data.get('process', '')}\n\naim : {current_aim}\nquestion : {current_question}\n"

        conversation_history += system_message


def get_conversation_history(session_id: int) -> str:
    """获取指定会话的完整对话历史"""
    full_session_data = chat_service.get_session_with_qas(session_id)
    if not full_session_data or 'chat_qas' not in full_session_data:
        print("❌ 未找到该会话或无问答记录")
        return ""

    history = ""
    for qa in full_session_data['chat_qas']:
        aim = qa.get('aim', '')
        question = qa.get('question', '')
        answer = qa.get('answer', '')
        emotion = qa.get('emotion', 'neutral')
        progress = qa.get('progress', '')
        history += f"🎯 目标: {aim}\n❓ 问题: {question}\n💭 回答: {answer}\n😊 情绪: {emotion}\n📊 进度: {progress}\n\n"
    
    return history


def continue_conversation(dialogues: Dict[int, Any]) -> None:
    """继续现有对话的完整流程"""
    keys = list(dialogues.keys())
    if not keys:
        print("❌ 当前没有可继续的对话，请先开始新对话。")
        return

    while True:
        # 选择要继续的对话
        print("请选择要继续的对话：")
        print(keys)
        choice = input("请输入选项：")

        if choice.isdigit() and int(choice) in keys:
            session_id = int(choice)
            if dialogues[session_id].is_finished:
                print("❌ 该对话已完成，无法继续。")
                return
            
            print(f"您选择了继续会话 {session_id}")
            history = get_conversation_history(session_id)
            print("当前对话历史:")
            print(history)
            
            # 从数据库重构对话历史字符串
            full_session_data = chat_service.get_session_with_qas(session_id)
            if not full_session_data or 'chat_qas' not in full_session_data:
                print("❌ 未能加载对话历史")
                return
            
            conversation_history = ""
            last_qa = None
            
            # 重构对话历史
            for qa in full_session_data['chat_qas']:
                if qa.get('aim') and qa.get('question'):
                    conversation_history += f"🎯 目标: {qa.get('aim')}\n❓ 问题: {qa.get('question')}\n"
                if qa.get('answer'):
                    conversation_history += f"answer : {qa.get('answer')}\n"
                if qa.get('emotion') and qa.get('progress'):
                    conversation_history += f"emotion : {qa.get('emotion')}\nprocess : {qa.get('progress')}\n\n"
                    if qa.get('aim') and qa.get('question'):
                        conversation_history += f"aim : {qa.get('aim')}\nquestion : {qa.get('question')}\n"
                last_qa = qa
            
            # 继续对话循环
            print("\n" + "=" * 50)
            print(f"🔄 继续会话 {session_id}，输入'退出'结束对话")
            print("=" * 50)
            
            # 用于跟踪预创建的问答记录ID
            next_qa_id = None
            
            # 检查是否有未完成的问答记录（没有答案的记录）
            if full_session_data['chat_qas']:
                last_qa = full_session_data['chat_qas'][-1]
                if last_qa.get('answer') is None and last_qa.get('aim') and last_qa.get('question'):
                    # 如果最后一个记录没有答案，说明是预创建的记录
                    next_qa_id = last_qa['id']
                    current_aim = last_qa.get('aim')
                    current_question = last_qa.get('question')
                    print(f"💾 发现未完成的问答记录 ID: {next_qa_id}")
            
            # 如果有最后一个问题，先显示它
            if current_aim and current_question:
                print("\n" + "-" * 40)
                print(f"🎯 目标: {current_aim}")
                print(f"❓ 问题: {current_question}")
                print("-" * 40)
            else:
                current_aim = ""
                current_question = ""
            
            while True:
                user_input = input("💭 回答: ")

                if user_input.lower() == '退出':
                    print("\n👋 对话结束，感谢您的参与！")
                    break

                conversation_history += f"answer : {user_input}\n"

                # 使用抽象的AI交互函数
                response_data = handle_ai_interaction(conversation_history, user_input)
                if not response_data:
                    return

                # 使用抽象的保存函数
                save_success = save_qa_record(session_id, next_qa_id, current_question, current_aim, user_input, response_data)
                if not save_success:
                    print("⚠️ 保存失败，但继续对话...")

                if response_data['is_finished']:
                    # 使用抽象的完成处理函数
                    handle_conversation_completion(session_id, response_data)
                    break

                # 使用抽象的状态显示函数
                display_response_status(response_data)

                # 更新当前问题和目标，用于下一轮保存
                current_aim = response_data.get('aim', '')
                current_question = response_data.get('question', '')

                # 使用抽象的预创建函数
                next_qa_id = pre_create_next_qa(session_id, current_aim, current_question)

                system_message = f"emotion : {response_data.get('emotion', 'neutral')}\nprocess : {response_data.get('process', '')}\n\naim : {current_aim}\nquestion : {current_question}\n"

                conversation_history += system_message
            
            break

        elif choice.lower() == '退出':
            print("\n👋 对话结束，感谢您的参与！")
            break
        else:
            print("❌ 无效选项\n")