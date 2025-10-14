import dotenv
import getpass
import os
import json
import time
import sys
from typing import Dict, Optional, Any, Generator
from langchain.chat_models import init_chat_model
from .system_prompt import check_system_prompt
# from system_prompt import check_system_prompt

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
        required_fields = ['dubious']
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
                required_fields = ['dubious']
                for field in required_fields:
                    if field not in parsed:
                        return None
                return parsed
        except Exception as extract_error:
            pass
            
        return None
    except Exception as e:
        return None

def check(context: str, debug: bool = False) -> Dict[str, Any]:
    """
    进行史实校验
    :param context: 上下文信息
    :param debug: 是否启用调试模式
    :return: 包含 dubious 字段的字典
    dubious 字段是一个列表，包含所有可疑内容
    """
    try:
        # 验证环境
        if not validate_environment():
            raise EnvironmentError("环境配置错误，请检查 DEEPSEEK_API_KEY 是否正确设置")
            
        # 验证输入
        if not context or not context.strip():
            raise ValueError("上下文不能为空")
                    
        # 初始化模型
        model = init_chat_model(
            model="deepseek-chat",
            model_provider="deepseek",
            temperature=0,
            openai_api_key=os.environ.get('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com/v1"
        )
                
        # 构造完整提示词
        full_prompt = check_system_prompt + "\n\n" + context
        
        # 调用模型
        response = model.invoke(full_prompt)
        
        if not response or not hasattr(response, 'content'):
            raise ValueError("AI响应无效")
            
        raw_content = response.content
        
        # 解析响应
        parsed_data = parse_response(raw_content)
        
        if parsed_data is None:
            raise ValueError("无法解析AI响应，可能格式不正确")
        
        return parsed_data['dubious']
                        
    except Exception as e:
        raise e
    
if __name__ == "__main__":
    # 简单测试
    test_context = "1992年初邓小平南巡讲话一公布，上海9月就出台《全民所有制工业企业转换经营机制实施办法》，明确国企可自主决定投资、定价和用工。我10月就拍板：砍掉70%计划奶指标，把原本用于完成统购的2000吨日产能全部转向“小房子”鲜牛奶，并首次贷款3000万元从瑞典引进超高温瞬时灭菌线，当年12月“光明”牌屋顶包鲜奶进超市，售价翻倍仍脱销，企业从完成计划转向追逐市场的开关就是那两个月按下去的。"
    result = check(test_context)
    print(result)