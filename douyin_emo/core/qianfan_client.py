"""
千帆API客户端
对接百度千帆LLM（DeepSeek等）
"""

import os
import json
import requests
from typing import Optional, Dict, Any


class QianfanClient:
    """
    百度千帆LLM客户端
    
    环境变量配置：
    - QIANFAN_API_KEY: API Key
    - QIANFAN_ENDPOINT: 端点地址（默认DeepSeek）
    """
    
    DEFAULT_ENDPOINT = "https://qianfan.baidubce.com/v2/ai/deepseek-v3"
    
    def __init__(self, api_key: str = None, endpoint: str = None):
        self.api_key = api_key or os.getenv("QIANFAN_API_KEY") or os.getenv("BAIDU_API_KEY")
        self.endpoint = endpoint or os.getenv("QIANFAN_ENDPOINT", self.DEFAULT_ENDPOINT)
        
        if not self.api_key:
            raise ValueError("未配置千帆API Key，请设置 QIANFAN_API_KEY 或 BAIDU_API_KEY 环境变量")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Appbuilder-From": "openclaw-douyin"
        }

    def chat(self, prompt: str, max_tokens: int = 512, temperature: float = 0.8) -> str:
        """
        发送对话请求
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度（0-2），越高越有创意
            
        Returns:
            模型生成的文本
        """
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
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
            
            # 解析响应
            if "body" in result:
                # 流式响应结构
                body = result["body"]
                if "choices" in body:
                    return body["choices"][0]["message"]["content"]
                elif "content" in body:
                    return body["content"]
            
            # 非流式响应结构
            if "output" in result:
                return result["output"]["text"]
            
            if "content" in result:
                return result["content"]
            
            print(f"[QianfanClient] 响应结构: {result}")
            return str(result)
            
        except requests.exceptions.Timeout:
            print("[QianfanClient] 请求超时")
            raise
        except requests.exceptions.HTTPError as e:
            print(f"[QianfanClient] HTTP错误: {e.response.text}")
            raise
        except json.JSONDecodeError:
            print(f"[QianfanClient] JSON解析失败: {response.text}")
            raise

    def generate_batch(self, prompts: list, max_tokens: int = 512) -> list:
        """
        批量生成（串行）
        
        Args:
            prompts: 提示词列表
            
        Returns:
            生成结果列表
        """
        results = []
        for i, prompt in enumerate(prompts):
            print(f"[QianfanClient] 批量生成 {i+1}/{len(prompts)}")
            try:
                content = self.chat(prompt, max_tokens)
                results.append({"success": True, "content": content})
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        return results


# 测试
if __name__ == "__main__":
    try:
        client = QianfanClient()
        
        test_prompt = "你是抖音文案专家，写一条扎心的情感文案，15秒以内。"
        print(f"测试提示词: {test_prompt}\n")
        
        result = client.chat(test_prompt)
        print(f"生成结果: {result}")
        
    except ValueError as e:
        print(f"配置错误: {e}")
        print("请设置环境变量: export QIANFAN_API_KEY='your-api-key'")
