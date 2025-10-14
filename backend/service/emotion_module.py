from aip import AipNlp
import dotenv
import getpass
import os

def emotion(text: str, options: bool = False) -> str:
    """调用百度AI开放平台的情绪识别接口，返回情绪标签"""
    # 获取当前文件所在目录，确保正确加载api_keys.env
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(current_dir, 'api_keys.env')
    
    dotenv.load_dotenv(env_file)

    BAIDU_APP_ID = os.environ.get("BAIDU_APP_ID")
    BAIDU_API_KEY = os.environ.get("BAIDU_API_KEY")
    BAIDU_SECRET_KEY = os.environ.get("BAIDU_SECRET_KEY")

    # print(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)

    client = AipNlp(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)

    if options:
        # 调用对话情绪识别接口
        # :param text: string 必选 参数：待识别情感文本，输入限制 512字节/254个汉字
        # :param scene: string 非必选 参数：场景选择，默认default
        #     取值包括：
        #     default（默认项-不区分场景），
        #     talk（闲聊对话-如度秘聊天等），
        #     task（任务型对话-如导航对话等），
        #     customer_service（客服对话-如电信/银行客服等）
        result = client.emotion(text)

        # print(result['items'][0])

        return result['items'][0]['label']
    
    # 调用情绪倾向分析接口
    # :param text: string 必选 参数：待识别情感文本，输入限制 2048字节/1024个汉字
    # return: dict 返回情感倾向分析结果
    #     items: list 情感分析结果数组
    #         sentiment: int 情感倾向类别
    #             0：负面情绪
    #             1：中性情绪
    #             2：正面情绪
    result = client.sentimentClassify(text)
    sentiments = result['items'][0]['sentiment']
    return {0: 'negative', 1: 'neutral', 2: 'positive'}.get(sentiments, 'neutral')