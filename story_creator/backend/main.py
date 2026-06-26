"""
故事创作引擎 - 后端API
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import json
import os
import sys
import requests
import asyncio

app = FastAPI(title="故事创作引擎 API")

# LLM 客户端配置 (优先智谱，回退千帆)
llm_client = None
LLM_AVAILABLE = False

# 尝试智谱AI
try:
    from core.zhipuai_client import ZhipuAIClient
    llm_client = ZhipuAIClient()
    LLM_AVAILABLE = True
    print("[故事创作引擎] 智谱AI LLM 已连接")
except Exception as e:
    print(f"[故事创作引擎] 智谱AI 不可用: {e}")
    
    # 回退到千帆
    try:
        sys.path.insert(0, "/root/.openclaw/workspace/douyin_emo")
        from core.qianfan_client import QianfanClient
        llm_client = QianfanClient()
        LLM_AVAILABLE = True
        print("[故事创作引擎] 千帆LLM 已连接")
    except Exception as e2:
        print(f"[故事创作引擎] 千帆也不可用: {e2}")

# LLM 生成函数
def generate_with_llm(prompt: str, max_tokens: int = 2000) -> str:
    """使用 LLM 生成内容"""
    if not LLM_AVAILABLE or not llm_client:
        return None
    
    try:
        return llm_client.chat(prompt, max_tokens=max_tokens, temperature=0.8)
    except Exception as e:
        print(f"[LLM] 生成失败: {e}")
        return None


def generate_with_llm_json(prompt: str, max_tokens: int = 3000) -> dict:
    """使用 LLM 生成 JSON 内容"""
    if not LLM_AVAILABLE or not llm_client:
        return None
    
    full_prompt = f"""请根据以下要求生成JSON格式的内容。只输出JSON，不要输出其他内容。

要求：
{prompt}

JSON："""
    
    try:
        result = llm_client.chat(full_prompt, max_tokens=max_tokens, temperature=0.8)
        # 尝试解析JSON
        import json
        import re
        
        # 查找JSON块（可能是数组或对象）
        # 先尝试找整个 JSON 块
        json_patterns = [
            r'\[.*\]',  # 数组
            r'\{.*\}'   # 对象
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, result, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
        
        # 如果正则失败，尝试原始方法
        start = result.find('{')
        if start < 0:
            start = result.find('[')
        end = result.rfind('}')
        if end < 0:
            end = result.rfind(']')
            
        if start >= 0 and end > start:
            json_str = result[start:end+1]
            return json.loads(json_str)
            
        return {"raw": result}
    except Exception as e:
        print(f"[LLM] JSON解析失败: {e}")
        return None


def generate_framework_with_llm(idea_data: dict) -> dict:
    """使用LLM生成故事框架"""
    prompt = f"""你是一个故事创作助手。请根据以下信息生成一个完整的故事框架。

项目构思信息：
- 题材：{idea_data.get('题材', '待确定')}
- 主题：{idea_data.get('主题', '待确定')}
- 主角：{idea_data.get('主角', '待确定')}
- 期望结局：{idea_data.get('结局', '待确定')}

请生成一个JSON格式的故事框架，包含以下字段：
{{
    "世界观": "描述故事发生的世界/背景",
    "时代背景": "具体的时代设定",
    "时间线": [
        {{"时间点": "故事开始", "事件": "具体事件"}},
        {{"时间点": "故事发展", "事件": "具体事件"}},
        {{"时间点": "故事高潮", "事件": "具体事件"}},
        {{"时间点": "故事结局", "事件": "具体事件"}}
    ],
    "核心冲突": "故事的核心矛盾",
    "主题": "故事的主题思想",
    "风格": "整体叙事风格"
}}

请直接输出JSON，不要有其他内容。"""
    
    result = generate_with_llm_json(prompt, 3000)
    # 确保返回的是字典
    if result and isinstance(result, dict) and "raw" not in result:
        return result
    
    # 如果LLM失败，返回默认值
    return {
        "世界观": f"这是一个{idea_data.get('题材', '都市')}背景的故事时代",
        "时代背景": "待完善",
        "时间线": [
            {"时间点": "故事开始", "事件": "主角出场"},
            {"时间点": "故事发展", "事件": "冲突展开"},
            {"时间点": "故事高潮", "事件": "核心冲突爆发"},
            {"时间点": "故事结局", "事件": "最终解决"}
        ],
        "核心冲突": idea_data.get("主题", "成长与救赎"),
        "主题": idea_data.get("主题", ""),
        "风格": "待确定"
    }


def generate_characters_with_llm(idea_data: dict, framework: dict) -> list:
    """使用LLM生成角色"""
    # 确保 framework 是字典
    if not isinstance(framework, dict):
        framework = {}
        
    prompt = f"""你是一个故事创作助手。请根据以下信息生成故事角色。

项目构思信息：
- 题材：{idea_data.get('题材', '待确定')}
- 主题：{idea_data.get('主题', '待确定')}
- 主角：{idea_data.get('主角', '待确定')}
- 期望结局：{idea_data.get('结局', '待确定')}

故事框架：
- 世界观：{framework.get('世界观', '')}
- 时代背景：{framework.get('时代背景', '')}
- 核心冲突：{framework.get('核心冲突', '')}

请生成3个JSON格式的角色，包含以下字段：
{{
    "name": "角色名称",
    "role": "主角/配角/反派",
    "description": "角色简介",
    "appearance": "外貌特征",
    "personality": "性格特点",
    "background": "背景故事",
    "relationships": [{{"name": "其他角色名", "relation": "关系"}}]
}}

请直接输出JSON数组，不要有其他内容。"""
    
    result = generate_with_llm_json(prompt, 3000)
    if result and isinstance(result, list):
        # 添加ID
        for char in result:
            char["id"] = str(uuid.uuid4())
            if "relationships" not in char:
                char["relationships"] = []
        return result
    
    # 如果LLM失败，返回默认值
    return [
        {
            "id": str(uuid.uuid4()),
            "name": "主角",
            "role": "主角",
            "description": idea_data.get("主角", "待确定"),
            "appearance": "待完善",
            "personality": "待完善",
            "background": "待完善",
            "relationships": []
        }
    ]


def generate_chapters_with_llm(idea_data: dict, framework: dict, num_chapters: int = 6) -> list:
    """使用LLM生成章节规划"""
    # 确保 framework 是字典
    if not isinstance(framework, dict):
        framework = {}
        
    prompt = f"""你是一个故事创作助手。请根据以下信息生成章节规划。

项目构思信息：
- 题材：{idea_data.get('题材', '待确定')}
- 主题：{idea_data.get('主题', '待确定')}
- 主角：{idea_data.get('主角', '待确定')}
- 期望结局：{idea_data.get('结局', '待确定')}

故事框架：
- 世界观：{framework.get('世界观', '')}
- 核心冲突：{framework.get('核心冲突', '')}
- 时间线：{framework.get('时间线', [])}

请生成{num_chapters}个章节的规划，每个章节包含：
{{
    "order": 序号,
    "title": "章节标题",
    "summary": "章节内容概要",
    "status": "待创作"
}}

请直接输出JSON数组，不要有其他内容。"""
    
    result = generate_with_llm_json(prompt, 3000)
    if result and isinstance(result, list):
        # 确保有ID
        for ch in result:
            if "id" not in ch:
                ch["id"] = str(uuid.uuid4())
            if "status" not in ch:
                ch["status"] = "待创作"
        return result
    
    # 如果LLM失败，返回默认值
    return [
        {"order": i+1, "id": str(uuid.uuid4()), "title": f"第{i+1}章", "summary": "待完善", "status": "待创作"}
        for i in range(num_chapters)
    ]


def generate_directions_with_llm(chapter: dict, project: dict, characters: list) -> list:
    """使用LLM生成章节创作方向建议"""
    prompt = f"""你是一个故事创作助手。请为以下章节生成3个不同的创作方向。

章节信息：
- 标题：{chapter.get('title', '')}
- 概要：{chapter.get('summary', '')}
- 当前状态：{chapter.get('content', '暂无内容')[:200]}...

项目信息：
- 标题：{project.get('title', '')}
- 类型：{project.get('project_type', '小说')}
- 框架：{project.get('framework', {})}

角色：{', '.join([c.get('name', '') for c in characters[:3]])}

请生成3个JSON格式的方向建议，包含以下字段：
{{
    "id": "dir_序号",
    "title": "方向标题",
    "description": "详细的创作方向描述",
    "tone": "文风特点"
}}

请直接输出JSON数组，不要有其他内容。"""
    
    result = generate_with_llm_json(prompt, 2000)
    if result and isinstance(result, list):
        # 确保有正确的ID格式
        for i, d in enumerate(result):
            d["id"] = f"dir_{chapter.get('id', 'unknown')}_{i+1}"
        return result
    
    # 如果LLM失败，返回默认值
    return [
        {
            "id": f"dir_{chapter.get('id', 'unknown')}_1",
            "title": "情感方向",
            "description": "继续丰富情感描写",
            "tone": "情感细腻"
        }
    ]

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= 数据模型 =============

class ProjectCreate(BaseModel):
    idea: str
    project_type: str = "小说"  # 小说/游戏策划/剧本/自传

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    framework: Optional[dict] = None

class CharacterCreate(BaseModel):
    project_id: str
    name: str
    role: str  # 主角/配角/反派
    description: str = ""
    appearance: str = ""
    personality: str = ""
    background: str = ""

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    appearance: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    relationships: Optional[List[dict]] = None

class ChapterCreate(BaseModel):
    project_id: str
    order: int
    title: str
    summary: str = ""

class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None

class DirectionGenerate(BaseModel):
    """方向生成请求"""
    direction_id: str

class DirectionOption(BaseModel):
    """方向选项"""
    id: str
    title: str
    description: str
    tone: str

# ============= 模拟数据库 =============

projects_db = {}
characters_db = {}
chapters_db = {}
idea_conversations = {}  # 存储AI引导对话

# ============= 项目API =============

@app.get("/api/projects")
async def list_projects():
    """获取项目列表"""
    return list(projects_db.values())

@app.post("/api/projects")
async def create_project(data: ProjectCreate):
    """创建新项目"""
    project_id = str(uuid.uuid4())
    project = {
        "id": project_id,
        "title": "未命名项目",
        "idea": data.idea,
        "project_type": data.project_type,
        "status": "构思中",
        "progress": 10,
        "framework": {},
        "chapters": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    projects_db[project_id] = project
    
    # 初始化对话
    idea_conversations[project_id] = {
        "messages": [],
        "stage": "initial",  # initial / confirming / framework
        "idea_data": {
            "题材": "",
            "主题": "",
            "主角": "",
            "结局": ""
        }
    }
    
    return project

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """获取项目详情"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="项目不存在")
    return projects_db[project_id]

@app.patch("/api/projects/{project_id}")
async def update_project(project_id: str, data: ProjectUpdate):
    """更新项目"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project = projects_db[project_id]
    if data.title is not None:
        project["title"] = data.title
    if data.status is not None:
        project["status"] = data.status
    if data.progress is not None:
        project["progress"] = data.progress
    if data.framework is not None:
        project["framework"] = data.framework
    
    project["updated_at"] = datetime.now().isoformat()
    return project

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="项目不存在")
    del projects_db[project_id]
    return {"message": "删除成功"}

# ============= 构思引导API =============

@app.get("/api/projects/{project_id}/idea/conversation")
async def get_idea_conversation(project_id: str):
    """获取构思引导对话"""
    if project_id not in idea_conversations:
        raise HTTPException(status_code=404, detail="项目不存在")
    return idea_conversations[project_id]

@app.post("/api/projects/{project_id}/idea/message")
async def send_idea_message(project_id: str, message: dict):
    """发送构思引导消息"""
    if project_id not in idea_conversations:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    conversation = idea_conversations[project_id]
    user_msg = message.get("content", "")
    
    # 添加用户消息
    conversation["messages"].append({
        "role": "user",
        "content": user_msg,
        "timestamp": datetime.now().isoformat()
    })
    
    # AI回复逻辑
    ai_response = generate_ai_response(conversation, user_msg)
    
    # 添加AI消息
    conversation["messages"].append({
        "role": "assistant",
        "content": ai_response["content"],
        "timestamp": datetime.now().isoformat()
    })
    
    return conversation

def generate_ai_response(conversation: dict, user_message: str) -> dict:
    """生成AI引导回复（优先使用LLM）"""
    idea_data = conversation["idea_data"]
    
    # 先保存用户的回答
    if not idea_data.get("题材"):
        idea_data["题材"] = user_message
    elif not idea_data.get("主题"):
        idea_data["主题"] = user_message
    elif not idea_data.get("主角"):
        idea_data["主角"] = user_message
    elif not idea_data.get("结局"):
        idea_data["结局"] = user_message
    
    # 构建上下文信息（已更新）
    context_parts = []
    if idea_data.get("题材"):
        context_parts.append(f"题材：{idea_data['题材']}")
    if idea_data.get("主题"):
        context_parts.append(f"主题：{idea_data['主题']}")
    if idea_data.get("主角"):
        context_parts.append(f"主角：{idea_data['主角']}")
    if idea_data.get("结局"):
        context_parts.append(f"期望结局：{idea_data['结局']}")
    
    current_context = "，".join(context_parts) if context_parts else "尚未确定任何信息"
    
    # 确定下一个问题
    next_question = ""
    if not idea_data.get("题材"):
        next_question = "用户说想创作【" + user_message + "】的故事。请用一句友好简洁的话确认这个题材，并询问下一个问题：故事的核心主题是什么？"
    elif not idea_data.get("主题"):
        next_question = f"用户选择了【{idea_data['题材']}】题材，主题是【{user_message}】。请确认主题，并询问下一个问题：主角是什么样的？"
    elif not idea_data.get("主角"):
        next_question = f"用户选择的主题是【{idea_data['主题']}】。请确认，并询问：希望塑造什么样的主角？描述一下主角的特点。"
    elif not idea_data.get("结局"):
        next_question = f"主角设定：【{user_message}】。请确认主角设定，并询问最后一个问题：希望故事是什么类型的结局？"
    else:
        next_question = "所有信息已收集完成。请总结已确定的创作意图，并提醒用户可以开始生成故事框架了。"
    
    # 优先使用LLM生成回复
    if LLM_AVAILABLE and llm_client:
        try:
            llm_prompt = f"""你是一个故事创作助手。用户正在与你交流创作构思。

当前已收集的信息：
{current_context}

{next_question}

请直接回复用户，简洁明了，不超过60字。一次只问一个问题。"""
            
            response = llm_client.chat(llm_prompt, max_tokens=300, temperature=0.7)
            
            # 检查是否收集完成
            if idea_data.get("题材") and idea_data.get("主题") and idea_data.get("主角") and idea_data.get("结局"):
                # 更新项目状态
                project_id = [k for k, v in idea_conversations.items() if v == conversation]
                if project_id:
                    projects_db[project_id[0]]["status"] = "框架生成中"
                    projects_db[project_id[0]]["progress"] = 30
                    projects_db[project_id[0]]["title"] = f"{idea_data['题材']}故事"
                
                return {
                    "content": f"太好了！我已经了解了你的创作意图：\n\n"
                               f"📚 题材：{idea_data['题材']}\n"
                               f"🎯 主题：{idea_data['主题']}\n"
                               f"👤 主角：{idea_data['主角']}\n"
                               f"🏁 结局：{idea_data['结局']}\n\n"
                               f"现在我将为你生成故事框架，包括世界观、角色设定和剧情大纲。请稍候...\n\n"
                               f"✨ 点击下方「生成故事框架」按钮开始创作！"
                }
            
            return {"content": response}
            
        except Exception as e:
            print(f"[AI引导] LLM生成失败: {e}")
    
    # LLM不可用时，使用固定回复（回退方案）
    # ... 原有代码 ...
    
    # LLM不可用时，使用固定回复作为回退
    # 注意：用户回答已在前面保存到 idea_data 中
    if idea_data.get("题材") and idea_data.get("主题") and idea_data.get("主角") and idea_data.get("结局"):
        # 更新项目状态
        project_id = [k for k, v in idea_conversations.items() if v == conversation]
        if project_id:
            projects_db[project_id[0]]["status"] = "框架生成中"
            projects_db[project_id[0]]["progress"] = 30
            projects_db[project_id[0]]["title"] = f"{idea_data['题材']}故事"
        
        return {
            "content": f"太好了！我已经了解了你的创作意图：\n\n"
                       f"📚 题材：{idea_data['题材']}\n"
                       f"🎯 主题：{idea_data['主题']}\n"
                       f"👤 主角：{idea_data['主角']}\n"
                       f"🏁 结局：{idea_data['结局']}\n\n"
                       f"现在我将为你生成故事框架，包括世界观、角色设定和剧情大纲。请稍候...\n\n"
                       f"✨ 点击下方「生成故事框架」按钮开始创作！"
        }
    elif not idea_data.get("题材"):
        return {"content": "明白了。那么这个故事的核心主题是什么？比如：复仇、成长、爱情、救赎、探案等。"}
    elif not idea_data.get("主题"):
        return {"content": "很好。请描述一下你的主角是什么样的？（年龄、身份、性格特点、有什么特别之处）"}
    elif not idea_data.get("主角"):
        return {"content": "你希望故事的结局是怎样的？比如：圆满、悲剧、留有悬念、主角牺牲等。"}
    else:
        return {"content": "你的创作意图已经确认完毕！点击下方「生成故事框架」开始创作吧～"}

# ============= 框架生成API =============

async def generate_framework_stream(project_id: str):
    """流式生成故事框架（带进度提示）"""
    if project_id not in projects_db:
        yield 'data: {"error": "项目不存在"}\n\n'
        return
    
    project = projects_db[project_id]
    idea_data = idea_conversations.get(project_id, {}).get("idea_data", {})
    
    # 检查是否已经生成过框架
    existing_chars = [c for c in characters_db.values() if c.get("project_id") == project_id]
    existing_chapters = [c for c in chapters_db.values() if c.get("project_id") == project_id]
    
    if existing_chars or existing_chapters:
        response_data = json.dumps({"status": "complete", "framework": project.get("framework", {}), "characters": existing_chars, "chapters": existing_chapters}, ensure_ascii=False)
        yield f'data: {response_data}\n\n'
        return
    
    # 步骤1: 准备
    yield 'data: {"step": "preparing", "message": "📜 准备工作纸笔...", "progress": 10}\n\n'
    await asyncio.sleep(0.5)
    
    # 步骤2: 生成框架
    yield 'data: {"step": "framework", "message": "🏗️ 构思故事框架，构建世界观...", "progress": 30}\n\n'
    framework = generate_framework_with_llm(idea_data)
    await asyncio.sleep(0.5)
    
    # 步骤3: 生成角色
    yield 'data: {"step": "characters", "message": "👤 塑造人物形象，刻画角色性格...", "progress": 50}\n\n'
    characters = generate_characters_with_llm(idea_data, framework)
    await asyncio.sleep(0.5)
    
    # 步骤4: 生成章节
    yield 'data: {"step": "chapters", "message": "📖 规划剧情走向，设计章节大纲...", "progress": 70}\n\n'
    chapters = generate_chapters_with_llm(idea_data, framework)
    await asyncio.sleep(0.5)
    
    # 步骤5: 保存数据
    yield 'data: {"step": "saving", "message": "💾 整理并保存创作成果...", "progress": 85}\n\n'
    
    project["framework"] = framework
    project["status"] = "框架已生成"
    project["progress"] = 50
    projects_db[project_id] = project
    
    for char in characters:
        char["project_id"] = project_id
        characters_db[char["id"]] = char
    
    for ch in chapters:
        ch["id"] = str(uuid.uuid4())
        ch["project_id"] = project_id
        ch["content"] = ""
        ch["word_count"] = 0
        chapters_db[ch["id"]] = ch
    
    await asyncio.sleep(0.3)
    
    # 完成 - 修复 f-string 格式化问题
    response_data = json.dumps({
        "status": "complete",
        "framework": framework,
        "characters": characters,
        "chapters": chapters,
        "message": "✨ 故事框架生成完成！",
        "progress": 100
    }, ensure_ascii=False)
    yield f'data: {response_data}\n\n'


@app.get("/api/projects/{project_id}/framework/generate/stream")
async def generate_framework_stream_endpoint(project_id: str):
    """流式生成故事框架（带进度）"""
    return StreamingResponse(
        generate_framework_stream(project_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/api/projects/{project_id}/framework/generate")
async def generate_framework(project_id: str):
    """生成故事框架"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project = projects_db[project_id]
    idea_data = idea_conversations.get(project_id, {}).get("idea_data", {})
    
    # 检查是否已经生成过框架，避免重复生成
    existing_chars = [c for c in characters_db.values() if c.get("project_id") == project_id]
    existing_chapters = [c for c in chapters_db.values() if c.get("project_id") == project_id]
    
    if existing_chars or existing_chapters:
        print(f"[框架生成] 项目已有数据，跳过生成")
        return {
            "framework": project.get("framework", {}),
            "characters": existing_chars,
            "chapters": existing_chapters
        }
    
    # 优先使用LLM生成框架
    framework = generate_framework_with_llm(idea_data)
    print(f"[框架生成] 使用LLM生成故事框架")
    
    # 优先使用LLM生成角色
    characters = generate_characters_with_llm(idea_data, framework)
    print(f"[角色生成] 使用LLM生成{len(characters)}个角色")
    
    # 优先使用LLM生成章节规划
    chapters = generate_chapters_with_llm(idea_data, framework)
    print(f"[章节生成] 使用LLM生成{len(chapters)}个章节")
    
    # 保存到数据库
    project["framework"] = framework
    project["status"] = "框架已生成"
    project["progress"] = 50
    projects_db[project_id] = project
    
    for char in characters:
        char["project_id"] = project_id
        characters_db[char["id"]] = char
    
    for ch in chapters:
        ch["id"] = str(uuid.uuid4())
        ch["project_id"] = project_id
        ch["content"] = ""
        ch["word_count"] = 0
        chapters_db[ch["id"]] = ch
    
    return {
        "framework": framework,
        "characters": characters,
        "chapters": chapters
    }

# ============= 角色API =============

@app.get("/api/projects/{project_id}/characters")
async def list_characters(project_id: str):
    """获取角色列表"""
    return [c for c in characters_db.values() if c.get("project_id") == project_id]

@app.post("/api/characters")
async def create_character(data: CharacterCreate):
    """创建角色"""
    char_id = str(uuid.uuid4())
    character = {
        "id": char_id,
        "project_id": data.project_id,
        "name": data.name,
        "role": data.role,
        "description": data.description,
        "appearance": data.appearance,
        "personality": data.personality,
        "background": data.background,
        "relationships": []
    }
    characters_db[char_id] = character
    return character

@app.patch("/api/characters/{char_id}")
async def update_character(char_id: str, data: CharacterUpdate):
    """更新角色并用LLM同步章节内容"""
    if char_id not in characters_db:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    char = characters_db[char_id]
    old_name = char.get("name", "")
    old_info = {
        "name": char.get("name", ""),
        "description": char.get("description", ""),
        "appearance": char.get("appearance", ""),
        "personality": char.get("personality", ""),
        "background": char.get("background", "")
    }
    
    # 更新角色信息
    if data.name is not None:
        char["name"] = data.name
    if data.role is not None:
        char["role"] = data.role
    if data.description is not None:
        char["description"] = data.description
    if data.appearance is not None:
        char["appearance"] = data.appearance
    if data.personality is not None:
        char["personality"] = data.personality
    if data.background is not None:
        char["background"] = data.background
    if data.relationships is not None:
        char["relationships"] = data.relationships
    
    # 同步章节内容 - 使用 LLM 重新生成
    project_id = char.get("project_id")
    sync_result = {"status": "completed", "chapters_updated": 0, "method": "none"}
    
    if project_id:
        project = projects_db.get(project_id, {})
        all_characters = [c for c in characters_db.values() if c.get("project_id") == project_id]
        project_chapters = [c for c in chapters_db.values() if c.get("project_id") == project_id]
        project_chapters = sorted(project_chapters, key=lambda x: x.get("order", 0))
        
        # 获取项目设定
        framework = project.get("framework", {})
        story_theme = framework.get("主题", "")
        story_type = project.get("project_type", "小说")
        
        # 首先尝试使用 LLM（如果可用）
        if LLM_AVAILABLE and llm_client:
            sync_result["method"] = "llm"
            for chapter in project_chapters:
                if not chapter.get("content"):
                    continue
                    
                # 构建 LLM 提示词
                prompt = f"""你是一个小说作家。用户修改了角色设定，你需要根据新的角色设定，重写相关章节内容，保持故事一致性。

## 原始章节内容
{chapter['content']}

## 修改的角色设定
- 角色名: {old_info['name']} → {char['name']}
- 角色描述: {old_info['description']} → {char['description']}
- 外貌特征: {old_info['appearance']} → {char['appearance']}
- 性格特点: {old_info['personality']} → {char['personality']}
- 背景故事: {old_info['background']} → {char['background']}

## 故事背景
- 类型: {story_type}
- 主题: {story_theme}
- 所有角色: {', '.join([c['name'] for c in all_characters])}

## 要求
1. 根据新的角色设定重写章节内容
2. 保持原有剧情结构和章节标题不变
3. 只修改与该角色相关的描写部分
4. 确保修改后的内容与新设定保持一致，不矛盾、不穿帮
5. 输出完整的章节内容（包含之前的部分）

请直接输出重写后的章节内容："""

                try:
                    print(f"[LLM] 正在重写章节: {chapter['title']}")
                    new_content = generate_with_llm(prompt, max_tokens=3000)
                    
                    if new_content:
                        chapter["content"] = new_content
                        chapter["word_count"] = len(new_content)
                        sync_result["chapters_updated"] += 1
                        print(f"[LLM] 章节 {chapter['title']} 已更新")
                except Exception as e:
                    print(f"[LLM] 重写失败: {e}")
        else:
            # 降级：简单替换名字
            sync_result["method"] = "simple_replace"
            for chapter in project_chapters:
                if chapter.get("content"):
                    # 替换旧名字为新名字
                    if data.name and old_name and data.name != old_name:
                        chapter["content"] = chapter["content"].replace(old_name, data.name)
                        sync_result["chapters_updated"] += 1
                    
                    # 添加修改说明
                    if data.description or data.personality or data.appearance or data.background:
                        chapter["content"] += f"\n\n---\n*角色设定已更新：{char['name']}*"
                    
                    if sync_result["chapters_updated"] > 0:
                        chapter["word_count"] = len(chapter["content"])
    
    return {
        "character": char,
        "sync": sync_result
    }


@app.patch("/api/projects/{project_id}/framework")
async def update_framework(project_id: str, data: ProjectUpdate):
    """更新项目框架信息"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project = projects_db[project_id]
    old_framework = project.get("framework", {}).copy()
    
    if data.framework is not None:
        project["framework"] = data.framework
        
        # 同步章节中的世界观信息
        project_chapters = [c for c in chapters_db.values() if c.get("project_id") == project_id]
        
        # 提取世界观关键词
        new_framework = data.framework
        world_info = ""
        if new_framework.get("world"):
            world_info += f"\n世界观：{new_framework.get('world', '')}"
        if new_framework.get("main_plot"):
            world_info += f"\n主线：{new_framework.get('main_plot', '')}"
        
        # 更新章节内容（添加世界观说明）
        for chapter in project_chapters:
            if chapter.get("content") and world_info:
                # 检查是否已添加过
                if "世界观设定已更新" not in chapter["content"]:
                    chapter["content"] += f"\n\n---\n*世界观设定已更新*{world_info}*"
    
    return project

# ============= 章节API =============

@app.get("/api/projects/{project_id}/chapters")
async def list_chapters(project_id: str):
    """获取章节列表"""
    chapters = [c for c in chapters_db.values() if c.get("project_id") == project_id]
    return sorted(chapters, key=lambda x: x.get("order", 0))

@app.post("/api/chapters")
async def create_chapter(data: ChapterCreate):
    """创建章节"""
    ch_id = str(uuid.uuid4())
    chapter = {
        "id": ch_id,
        "project_id": data.project_id,
        "order": data.order,
        "title": data.title,
        "summary": data.summary,
        "content": "",
        "status": "待创作",
        "word_count": 0
    }
    chapters_db[ch_id] = chapter
    return chapter

@app.get("/api/chapters/{ch_id}")
async def get_chapter(ch_id: str):
    """获取章节详情"""
    if ch_id not in chapters_db:
        raise HTTPException(status_code=404, detail="章节不存在")
    return chapters_db[ch_id]

@app.patch("/api/chapters/{ch_id}")
async def update_chapter(ch_id: str, data: ChapterUpdate):
    """更新章节"""
    if ch_id not in chapters_db:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    chapter = chapters_db[ch_id]
    if data.title is not None:
        chapter["title"] = data.title
    if data.summary is not None:
        chapter["summary"] = data.summary
    if data.content is not None:
        chapter["content"] = data.content
        chapter["word_count"] = len(data.content)
    if data.status is not None:
        chapter["status"] = data.status
    
    return chapter

# ============= 章节创作API =============

@app.post("/api/chapters/{ch_id}/directions")
async def get_chapter_directions(ch_id: str):
    """获取章节创作方向建议（3个选项）"""
    if ch_id not in chapters_db:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    chapter = chapters_db[ch_id]
    project_id = chapter["project_id"]
    project = projects_db[project_id]
    framework = project.get("framework", {})
    
    # 获取项目上下文用于生成方向
    title = project.get("title", "未命名")
    genre = project.get("project_type", "小说")
    characters = [c for c in characters_db.values() if c.get("project_id") == project_id]
    
    # 优先使用LLM生成方向建议
    directions = generate_directions_with_llm(chapter, project, characters)
    print(f"[方向生成] 使用LLM生成{len(directions)}个方向建议")
    
    return {
        "directions": directions,
        "chapter_id": ch_id,
        "chapter_title": chapter.get("title", ""),
        "interaction_count": chapter.get("interaction_count", 0)
    }


@app.post("/api/chapters/{ch_id}/generate")
async def generate_chapter_content(ch_id: str, data: DirectionGenerate = None):
    """AI生成章节内容（支持多轮方向选择）"""
    if ch_id not in chapters_db:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    chapter = chapters_db[ch_id]
    project_id = chapter["project_id"]
    project = projects_db[project_id]
    framework = project.get("framework", {})
    all_chapters = [c for c in chapters_db.values() if c.get("project_id") == project_id]
    all_chapters = sorted(all_chapters, key=lambda x: x.get("order", 0))
    
    # 查找当前章节的位置
    current_index = -1
    for i, c in enumerate(all_chapters):
        if c["id"] == ch_id:
            current_index = i
            break
    
    # 初始化方向历史和互动次数
    if "direction_history" not in chapter:
        chapter["direction_history"] = []
    if "interaction_count" not in chapter:
        chapter["interaction_count"] = 0
    
    # 处理方向选择
    direction_info = ""
    if data and data.direction_id:
        # 找到选择的方向
        directions = chapter.get("direction_history", [])
        selected_dir = None
        for d in directions:
            if d.get("id") == data.direction_id:
                selected_dir = d
                break
        
        if selected_dir:
            direction_info = f"（方向：{selected_dir['title']}）"
            chapter["selected_direction"] = selected_dir
    
    # 更新互动次数
    chapter["interaction_count"] = chapter.get("interaction_count", 0) + 1
    
    # 构建上下文
    previous_chapters = all_chapters[:current_index] if current_index > 0 else []
    next_chapters = all_chapters[current_index+1:] if current_index < len(all_chapters) - 1 else []
    
    # 获取已选择的方向信息
    selected_dir = chapter.get("selected_direction", {})
    direction_title = selected_dir.get("title", "未知方向")
    direction_tone = selected_dir.get("tone", "标准叙事")
    
    # 生成内容（模板版本，后续可接入LLM）
    # 根据方向生成不同风格的内容
    content_parts = []
    
    if chapter.get("content"):
        # 追加新内容
        content_parts.append(chapter["content"])
    
    # 新生成的内容
    new_content = f"""

---
## 第{chapter['interaction_count']}轮创作 {direction_info}

{direction_tone}风格内容：

{chapter['title']} - 继续发展

{chapter.get('summary', '')}

"""
    
    # 根据不同方向生成不同内容
    if "情感" in direction_title:
        new_content += f"""在这一章节中，情感的波澜达到了高潮。主角内心充满了复杂的情绪，既有对未来的期待，也有对过去的留恋。

【情感描写】
主角静静地站在窗前，回忆起这段时间发生的种种。每一个画面都如同电影一般在脑海中回放，那些欢笑、泪水、争执、和解...所有的片段交织在一起，构成了难忘的回忆。

（此处应有更详细的情感描写，根据LLM生成）
"""
    elif "悬疑" in direction_title:
        new_content += f"""在这一章节中，事情发生了意想不到的转折。就在主角以为一切都在掌握之中的时候，一个意外的发现彻底改变了局面。

【悬念迭起】
突然，手机震动了一下。一条陌生号码发来的短信："你以为你知道全部真相吗？"

主角的心跳骤然加快，一种不安的预感油然而生。究竟是谁在暗中观察着一切？这个谜团的背后又隐藏着怎样的秘密？

（此处应有更详细的悬疑情节，根据LLM生成）
"""
    else:  # 冒险
        new_content += f"""在这一章节中，主角踏上新的征程。前方充满了未知和挑战，但主角的眼神中充满了坚定。

【冒险启程】
主人公收拾行装，踏上了寻找答案的旅程。一路上，他遇到了各种各样的人，有敌人，也有盟友。每一个相遇都是一次考验，每一次选择都可能改变命运的走向。

（此处应有更详细的冒险描写，根据LLM生成）
"""
    
    new_content += f"""

---
*第{chapter['interaction_count']}轮创作完成。继续创作将提供新的方向选择。*
"""
    
    content_parts.append(new_content)
    chapter["content"] = "\n\n".join(content_parts)
    chapter["word_count"] = len(chapter["content"])
    
    # 判断是否完成（至少3轮互动）
    if chapter["interaction_count"] >= 3:
        chapter["status"] = "已完成"
    else:
        chapter["status"] = "进行中"
    
    # 更新项目进度
    completed_chapters = len([c for c in all_chapters if c.get("status") == "已完成"])
    if len(all_chapters) > 0:
        project["progress"] = 50 + int(completed_chapters / len(all_chapters) * 50)
    project["status"] = "创作中"
    
    return {
        "chapter": chapter,
        "interaction_count": chapter["interaction_count"],
        "is_complete": chapter["interaction_count"] >= 3,
        "can_continue": chapter["interaction_count"] < 3
    }

# ============= 导出API =============

@app.get("/api/projects/{project_id}/export")
async def export_project(project_id: str, format: str = "markdown"):
    """导出项目"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project = projects_db[project_id]
    characters = [c for c in characters_db.values() if c.get("project_id") == project_id]
    chapters = [c for c in chapters_db.values() if c.get("project_id") == project_id]
    chapters = sorted(chapters, key=lambda x: x.get("order", 0))
    
    # 获取项目的 framework 数据
    project_framework = project.get('framework', {})
    
    # 构建Markdown
    md = f"""# {project['title']}

**类型**: {project['project_type']}  
**创作时间**: {project['created_at']}

---

## 世界观

{project_framework.get('世界观', '')}

**时代背景**: {project_framework.get('时代背景', '')}

---

## 角色介绍

"""
    
    for char in characters:
        md += f"""### {char['name']} ({char['role']})

{char['description']}

- 外貌: {char['appearance']}
- 性格: {char['personality']}
- 背景: {char['background']}

"""
    
    md += "\n---\n\n## 章节内容\n\n"
    
    for ch in chapters:
        md += f"""### {ch['title']}

*{ch['summary']}*

{ch['content'] if ch.get('content') else '（待创作）'}

---
"""
    
    return {
        "format": "markdown",
        "content": md,
        "filename": f"{project['title']}.md"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
