"""
智谱AI客户端
对接智谱GLM大模型
"""

import os
import json
import requests
from typing import Optional

try:
    import zhipuai
    ZHIPUAI_SDK_AVAILABLE = True
except ImportError:
    ZHIPUAI_SDK_AVAILABLE = False


class ZhipuAIClient:
    """
    智谱AI LLM客户端
    
    环境变量配置：
    - ZHIPU_API_KEY: 智谱 API Key
    """
    
    DEFAULT_MODEL = "glm-4"
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        self.model = model or self.DEFAULT_MODEL
        
        if not self.api_key:
            raise ValueError("未配置智谱API Key，请设置 ZHIPU_API_KEY 环境变量")
        
        # 优先使用 SDK
        if ZHIPUAI_SDK_AVAILABLE:
            try:
                self.client = zhipuai.ZhipuAI(api_key=self.api_key)
                self.use_sdk = True
                print(f"[ZhipuAIClient] 使用SDK模式，模型: {self.model}")
            except Exception as e:
                print(f"[ZhipuAIClient] SDK初始化失败: {e}")
                self.use_sdk = False
        else:
            self.use_sdk = False
            self.endpoint = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            print(f"[ZhipuAIClient] 使用HTTP模式，模型: {self.model}")

    def chat(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.8) -> str:
        """
        发送对话请求
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度（0-2），越高越有创意
            
        Returns:
            模型生成的文本
        """
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        if self.use_sdk:
            return self._chat_sdk(messages, max_tokens, temperature)
        else:
            return self._chat_http(messages, max_tokens, temperature)
    
    def _chat_sdk(self, messages: list, max_tokens: int, temperature: float) -> str:
        """使用SDK调用"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[ZhipuAIClient] SDK调用失败: {e}")
            raise
    
    def _chat_http(self, messages: list, max_tokens: int, temperature: float) -> str:
        """使用HTTP调用"""
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            
            print(f"[ZhipuAIClient] 响应结构: {result}")
            return str(result)
            
        except requests.exceptions.Timeout:
            print("[ZhipuAIClient] 请求超时")
            raise
        except requests.exceptions.HTTPError as e:
            print(f"[ZhipuAIClient] HTTP错误: {e.response.text if e.response else e}")
            raise
        except Exception as e:
            print(f"[ZhipuAIClient] 错误: {e}")
            raise


# 测试
if __name__ == "__main__":
    try:
        client = ZhipuAIClient()
        
        test_prompt = "你是故事创作助手，请用一句话介绍自己能做什么。"
        print(f"测试提示词: {test_prompt}\n")
        
        result = client.chat(test_prompt)
        print(f"生成结果: {result}")
        
    except ValueError as e:
        print(f"配置错误: {e}")
        print("请设置环境变量: export ZHIPU_API_KEY='your-api-key'")
