from . import emotion_module
from . import check_module  
from . import talk_module
from . import summary_module
from typing import Generator, Dict, Any

def generate_response_stream(context: str, user_input: str, debug: bool = False) -> Generator[Dict[str, Any], None, None]:
    """
    流式生成响应内容
    :param context: 上下文信息
    :param user_input: 用户输入
    :param debug: 是否启用调试模式
    :return: 生成器，返回包含 type, content, data 字段的字典
    """

    # 初始化返回字典
    result = {
        "emotion": None,
        "dubious": [],
        "process": None,
        "aim": None,
        "question": None,
        "is_finished": False,
        "draft": None
    }

    if not context or not context.strip():
        yield {'type': 'error', 'content': '❌ 上下文不能为空', 'data': result}
        return

    if not user_input or not user_input.strip():
        yield {'type': 'error', 'content': '❌ 用户输入不能为空', 'data': result}
        return

    # 调用emotion模块进行情绪识别
    try:
        emotion = emotion_module.emotion(user_input)
        result["emotion"] = emotion
        yield {'type': 'emotion', 'content': f'{emotion}', 'data': result}
    except Exception as e:
        yield {'type': 'error', 'content': f'❌ 情绪识别失败: {e}', 'data': result}
        return

    # 调用check模块进行史实校验
    try:
        dubious = check_module.check(user_input)
        result["dubious"] = dubious
        yield {'type': 'dubious', 'content': f'发现可疑内容: {len(dubious)}项', 'data': result}
    except Exception as e:
        yield {'type': 'error', 'content': f'❌ 史实校验失败: {e}', 'data': result}
        return

    # 调用talk模块进行AI分析（流式）
    talk_result = None
    for stream_chunk in talk_module.talk_stream(context, debug):
        if stream_chunk['type'] == 'final':
            talk_result = {'success': True, 'data': stream_chunk['data']}
            break
        elif stream_chunk['type'] == 'error':
            yield {'type': 'error', 'content': stream_chunk['content'], 'data': result}
            return
        else:
            # 转发状态更新
            yield stream_chunk
    
    if not talk_result or not talk_result.get('success', False):
        yield {'type': 'error', 'content': '❌ AI分析失败', 'data': result}
        return
        
    talk_data = talk_result.get("data", {})
    result["process"] = talk_data.get("process", "")
    yield {'type': 'process', 'content': f'{result["process"]}', 'data': result}
    
    result['is_finished'] = talk_data.get('is_finished', False)
    yield {'type': 'is_finished', 'content': f'{talk_data.get("is_finished", False)}', 'data': result}

    # 如果对话已完成，生成总结草稿
    if talk_data.get('is_finished', False):
        try:
            draft = summary_module.summary(context)
            result['draft'] = draft
            yield {'type': 'draft', 'content': f'{draft}', 'data': result}
        except Exception as e:
            yield {'type': 'error', 'content': f'❌ 生成总结草稿失败: {e}', 'data': result}
            return
    else:
        result['aim'] = talk_data.get('aim', '')
        yield {'type': 'aim', 'content': f'{result["aim"]}', 'data': result}
        result['question'] = talk_data.get('question', '')
        yield {'type': 'question', 'content': f'{result["question"]}', 'data': result}

    yield {'type': 'final', 'content': '✅ 处理完成', 'data': result}