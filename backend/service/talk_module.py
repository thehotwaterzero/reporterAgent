import dotenv
import getpass
import os
import json
import time
import sys
from typing import Dict, Optional, Any, Generator
from langchain.chat_models import init_chat_model
from .system_prompt import talk_system_prompt

def validate_environment() -> bool:
    """验证环境配置是否正确"""
    try:
        # 获取当前文件所在目录，确保正确加载api_keys.env
        current_dir = os.path.dirname(os.path.abspath(__file__))
        env_file = os.path.join(current_dir, 'api_keys.env')
        
        dotenv.load_dotenv(env_file)
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        
        if not api_key:
            return False
            
        if not api_key.strip():
            return False
            
        return True
        
    except Exception as e:
        return False

def parse_response(response_content: str) -> Optional[Dict[str, Any]]:
    """解析AI响应的JSON内容"""
    try:
        # 尝试直接解析JSON
        parsed = json.loads(response_content.strip())
        
        # 验证必需字段（新增 is_finished 字段）
        required_fields = ['process', 'question', 'aim', 'is_finished']
        for field in required_fields:
            if field not in parsed:
                return None
                
        return parsed
        
    except json.JSONDecodeError as e:
        # 尝试提取JSON部分（如果响应包含其他文本）
        try:
            start = response_content.find('{')
            end = response_content.rfind('}') + 1
            if start >= 0 and end > start:
                json_part = response_content[start:end]
                parsed = json.loads(json_part)
                # 验证必需字段
                required_fields = ['process', 'question', 'aim', 'is_finished']
                for field in required_fields:
                    if field not in parsed:
                        return None
                return parsed
        except Exception as extract_error:
            pass
            
        return None
    except Exception as e:
        return None

def talk_stream(context: str, debug: bool = False) -> Generator[Dict[str, Any], None, None]:
    """
    流式智能对话函数
    
    Args:
        context (str): 对话上下文
        debug (bool): 是否开启调试模式
        
    Yields:
        Dict[str, Any]: 包含状态和部分内容的响应
        结构如下：
        {
            'type': 'status' | 'content' | 'final',
            'content': str,
            'data': Optional[Dict[str, Any]]
        }
    """
    try:
        # 验证环境
        if not validate_environment():
            yield {'type': 'error', 'content': '❌ 环境验证失败', 'data': None}
            return
            
        # 验证输入
        if not context or not context.strip():
            yield {'type': 'error', 'content': '❌ 上下文不能为空', 'data': None}
            return
                    
        # 初始化模型
        model = init_chat_model(
            model="deepseek-chat",
            model_provider="deepseek",
            temperature=0,
            openai_api_key=os.environ.get('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com/v1"
        )
                
        # 构造完整提示词
        full_prompt = talk_system_prompt + "\n\n" + context
        
        # 调用模型获取流式响应
        try:
            response = model.stream(full_prompt)
            collected_content = ""
                        
            for chunk in response:
                if hasattr(chunk, 'content') and chunk.content:
                    collected_content += chunk.content
                        
            # 解析最终响应
            parsed_data = parse_response(collected_content)
            
            if parsed_data is None:
                yield {'type': 'error', 'content': '❌ 解析回答失败', 'data': None}
                return
            
            # 返回最终结果
            yield {'type': 'final', 'content': '✅ AI分析完成', 'data': parsed_data}
            return
                            
        except Exception as stream_error:
            # 如果流式调用失败，回退到普通调用
            yield {'type': 'error', 'content': '⚠️ 流式模式失败，切换到普通模式...', 'data': None}
            
            response = model.invoke(full_prompt)
            
            if not response or not hasattr(response, 'content'):
                yield {'type': 'error', 'content': '❌ AI模型响应无效', 'data': None}
                return
                
            raw_content = response.content
            
            # 解析响应
            parsed_data = parse_response(raw_content)
            
            if parsed_data is None:
                yield {'type': 'error', 'content': '❌ 解析回答失败', 'data': None}
                return
            
            # 返回最终结果
            yield {'type': 'final', 'content': '✅ AI分析完成', 'data': parsed_data}
            return
                        
    except Exception as e:
        yield {'type': 'error', 'content': f'❌ 发生错误: {str(e)}', 'data': None}

def talk(context: str, debug: bool = False) -> Dict[str, Any]:
    """
    智能对话函数
    
    Args:
        context (str): 对话上下文
        debug (bool): 是否开启调试模式
        
    Returns:
        Dict[str, Any]: 包含解析后的响应或错误信息
        结构如下：
        {
            'success': bool,
            'data': Optional[Dict[str, Any]],
            'error': Optional[str],
            'raw_response': Optional[str]
        }
    """
    result = {
        'success': False,
        'data': None,
        'error': None,
        'raw_response': None
    }
    
    try:
        # 验证环境
        if not validate_environment():
            result['error'] = "Environment validation failed"
            return result
            
        # 验证输入
        if not context or not context.strip():
            result['error'] = "Context cannot be empty"
            return result
            
        # 初始化模型
        model = init_chat_model(
            model="deepseek-chat",
            model_provider="deepseek",
            temperature=0,
            openai_api_key=os.environ.get('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com/v1"
        )
        
        # 构造完整提示词
        full_prompt = talk_system_prompt + "\n\n" + context
        
        # 调用模型
        response = model.invoke(full_prompt)
        
        if not response or not hasattr(response, 'content'):
            result['error'] = "Invalid response from AI model"
            return result
            
        raw_content = response.content
        result['raw_response'] = raw_content
        
        # 解析响应
        parsed_data = parse_response(raw_content)
        
        if parsed_data is None:
            result['error'] = "Failed to parse response as JSON"
            return result
            
        result['success'] = True
        result['data'] = parsed_data
        
        return result
        
    except Exception as e:
        error_msg = f"Unexpected error in talk function: {str(e)}"
        result['error'] = error_msg
        return result

def talk_simple(context: str) -> str:
    """
    简化版talk函数，保持向后兼容
    
    Args:
        context (str): 对话上下文
        
    Returns:
        str: AI响应内容
    """
    result = talk(context)
    
    if result['success']:
        return json.dumps(result['data'], ensure_ascii=False, indent=2)
    else:
        return f"Error: {result['error']}"