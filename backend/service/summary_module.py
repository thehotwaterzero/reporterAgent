from .system_prompt import summary_system_prompt
from langchain.chat_models import init_chat_model
import dotenv
import getpass
import os

def summary(context: str, debug: bool = False) -> str:
    """
    生成对话总结
    """    
    # 获取当前文件所在目录，确保正确加载api_keys.env
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(current_dir, 'api_keys.env')
    
    dotenv.load_dotenv(env_file)
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    
    if not api_key.strip():
        raise ValueError("DEEPSEEK_API_KEY is not set or empty")

    # 验证输入
    if not context or not context.strip():
        raise ValueError("Context is empty")
        
    # 初始化模型
    model = init_chat_model(
        model="deepseek-chat",
        model_provider="deepseek",
        temperature=0,
        openai_api_key=os.environ.get('DEEPSEEK_API_KEY'),
        base_url="https://api.deepseek.com/v1"
    )
    
    # 构造完整提示词
    full_prompt = summary_system_prompt + "\n\n" + context
    
    # 调用模型
    response = model.invoke(full_prompt)
    
    return response.content if response and hasattr(response, 'content') else ""