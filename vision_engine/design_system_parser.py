#!/usr/bin/env python3
"""
DESIGN.md 设计系统解析器
解析 awesome-design-md 格式的 DESIGN.md 文件
"""

import os
import re
from typing import Dict, List, Optional

DESIGN_SYSTEMS_DIR = "/root/.openclaw/workspace/vision_engine/design_systems"

# 品牌中文名称映射
BRAND_NAMES = {
    "airbnb": "Airbnb",
    "airtable": "Airtable",
    "apple": "Apple",
    "bmw": "BMW",
    "cal": "Cal.com",
    "claude": "Claude",
    "clay": "Clay",
    "clickhouse": "ClickHouse",
    "cohere": "Cohere",
    "coinbase": "Coinbase",
    "composio": "Composio",
    "cursor": "Cursor",
    "elevenlabs": "ElevenLabs",
    "expo": "Expo",
    "figma": "Figma",
    "framer": "Framer",
    "hashicorp": "HashiCorp",
    "ibm": "IBM",
    "intercom": "Intercom",
    "kraken": "Kraken",
    "linear.app": "Linear",
    "lovable": "Lovable",
    "minimax": "Minimax",
    "mintlify": "Mintlify",
    "miro": "Miro",
    "mistral.ai": "Mistral AI",
    "mongodb": "MongoDB",
    "notion": "Notion",
    "nvidia": "NVIDIA",
    "ollama": "Ollama",
    "opencode.ai": "OpenCode AI",
    "pinterest": "Pinterest",
    "posthog": "PostHog",
    "raycast": "Raycast",
    "replicate": "Replicate",
    "resend": "Resend",
    "revolut": "Revolut",
    "runwayml": "RunwayML",
    "sanity": "Sanity",
    "sentry": "Sentry",
    "spacex": "SpaceX",
    "spotify": "Spotify",
    "stripe": "Stripe",
    "supabase": "Supabase",
    "superhuman": "Superhuman",
    "together.ai": "Together AI",
    "uber": "Uber",
    "vercel": "Vercel",
    "voltagent": "VoltAgent",
    "warp": "Warp",
    "webflow": "Webflow",
    "wise": "Wise",
    "x.ai": "xAI",
    "zapier": "Zapier",
}

# 品牌分类
BRAND_CATEGORIES = {
    "AI & 开发工具": ["claude", "cursor", "vercel", "stripe", "supabase", "linear.app", "notion", "raycast", "ollama", "cohere", "mistral.ai", "elevenlabs", "minimax", "opencode.ai", "replicate", "runwayml", "together.ai", "voltagent", "x.ai"],
    "设计工具": ["figma", "framer", "webflow", "miro", "clay"],
    "开发者工具": ["expo", "sentry", "posthog", "resend", "mongodb", "sanity", "hashicorp", "clickhouse", "composio", "warp", "lovable"],
    "金融科技": ["stripe", "coinbase", "kraken", "revolut", "wise"],
    "消费品牌": ["apple", "spotify", "airbnb", "uber", "pinterest", "superhuman", "intercom", "cal", "mintlify"],
    "企业服务": ["ibm", "zapier", "bmw", "spacex", "nvidia"],
}

class DesignSystemParser:
    """解析 DESIGN.md 文件"""
    
    def __init__(self, brand_id: str):
        self.brand_id = brand_id
        self.brand_name = BRAND_NAMES.get(brand_id, brand_id)
        self.file_path = os.path.join(DESIGN_SYSTEMS_DIR, brand_id, "DESIGN.md")
        self.content = ""
        self.parsed = {}
        
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            self._parse()
    
    def _parse(self):
        """解析 DESIGN.md 内容"""
        self.parsed = {
            "brand_id": self.brand_id,
            "brand_name": self.brand_name,
            "exists": True,
            "theme": self._extract_theme(),
            "colors": self._extract_colors(),
            "typography": self._extract_typography(),
            "components": self._extract_components(),
            "layout": self._extract_layout(),
            "shadows": self._extract_shadows(),
        }
    
    def _extract_theme(self) -> Dict:
        """提取视觉主题"""
        theme = {
            "name": self.brand_name,
            "description": "",
            "mood": "",
            "keywords": [],
        }
        
        # 提取第一段描述
        match = re.search(r'# Design System:.*?\n\n## 1\. Visual Theme & Atmosphere\n\n(.*?)(?=\n##)', self.content, re.DOTALL)
        if match:
            desc = match.group(1).strip()
            # 取前200字符作为描述
            theme["description"] = desc[:200] + "..." if len(desc) > 200 else desc
            
            # 提取关键词（粗体内容）
            keywords = re.findall(r'\*\*([^*]+)\*\*', desc)
            theme["keywords"] = keywords[:5]
        
        return theme
    
    def _extract_colors(self) -> Dict:
        """提取颜色系统"""
        colors = {
            "primary": "",
            "secondary": "",
            "accent": "",
            "background": "",
            "text": "",
            "all_colors": []
        }
        
        # 提取所有 hex 颜色
        hex_colors = re.findall(r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})', self.content)
        hex_colors = ['#' + c for c in hex_colors]
        colors["all_colors"] = list(dict.fromkeys(hex_colors))[:20]  # 去重，最多20个
        
        # 提取主要颜色
        patterns = [
            ("primary", r'(?:Primary|Brand).*?`?(#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3})`?'),
            ("accent", r'(?:Accent|CTA|Action).*?`?(#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3})`?'),
            ("background", r'(?:Background|Surface).*?`?(#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3})`?'),
            ("text", r'(?:Text|Foreground).*?`?(#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3})`?'),
        ]
        
        for key, pattern in patterns:
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                colors[key] = match.group(1)
        
        # 如果没有找到主要颜色，使用第一个颜色
        if not colors["primary"] and colors["all_colors"]:
            colors["primary"] = colors["all_colors"][0]
        
        return colors
    
    def _extract_typography(self) -> Dict:
        """提取字体系统"""
        typography = {
            "heading_font": "Inter",
            "body_font": "Inter",
            "scale": []
        }
        
        # 提取字体名称
        font_match = re.search(r'(?:font|typeface|typography).*?["\']([A-Za-z\s]+)["\']', self.content, re.IGNORECASE)
        if font_match:
            typography["heading_font"] = font_match.group(1).strip()
            typography["body_font"] = font_match.group(1).strip()
        
        # 查找 Google Fonts URL
        gf_match = re.search(r'https://fonts\.google\.com/[^\s\)]+', self.content)
        if gf_match:
            typography["google_fonts_url"] = gf_match.group(0)
        
        return typography
    
    def _extract_components(self) -> Dict:
        """提取组件样式"""
        components = {
            "buttons": {},
            "cards": {},
            "inputs": {}
        }
        
        # 提取按钮圆角
        radius_match = re.search(r'(?:button|radius).*?(\d+)px', self.content, re.IGNORECASE)
        if radius_match:
            components["buttons"]["border_radius"] = radius_match.group(1) + "px"
        
        # 提取卡片圆角
        card_radius = re.search(r'(?:card).*?(\d+)px', self.content, re.IGNORECASE)
        if card_radius:
            components["cards"]["border_radius"] = card_radius.group(1) + "px"
        
        return components
    
    def _extract_layout(self) -> Dict:
        """提取布局原则"""
        layout = {
            "max_width": "1200px",
            "spacing_scale": [],
            "grid": "12-column"
        }
        
        # 提取最大宽度
        width_match = re.search(r'(?:max.?width|container).*?(\d+)px', self.content, re.IGNORECASE)
        if width_match:
            layout["max_width"] = width_match.group(1) + "px"
        
        return layout
    
    def _extract_shadows(self) -> List:
        """提取阴影系统"""
        shadows = []
        
        # 提取 CSS box-shadow
        shadow_matches = re.findall(r'box-shadow:\s*([^;]+)', self.content)
        for shadow in shadow_matches[:3]:
            shadows.append(shadow.strip())
        
        return shadows
    
    def get_summary(self) -> Dict:
        """获取设计系统摘要"""
        return self.parsed
    
    def get_css_variables(self) -> str:
        """生成 CSS 变量"""
        colors = self.parsed.get("colors", {})
        typography = self.parsed.get("typography", {})
        
        css = f":root {{\n"
        css += f"  --brand-primary: {colors.get('primary', '#3B82F6')};\n"
        css += f"  --brand-accent: {colors.get('accent', '#06B6D4')};\n"
        css += f"  --brand-bg: {colors.get('background', '#ffffff')};\n"
        css += f"  --brand-text: {colors.get('text', '#1f2937')};\n"
        css += f"  --font-heading: '{typography.get('heading_font', 'Inter')}', sans-serif;\n"
        css += f"  --font-body: '{typography.get('body_font', 'Inter')}', sans-serif;\n"
        css += "}\n"
        
        return css


def get_available_brands() -> List[Dict]:
    """获取所有可用的设计系统品牌"""
    brands = []
    
    if not os.path.exists(DESIGN_SYSTEMS_DIR):
        return brands
    
    for brand_id in os.listdir(DESIGN_SYSTEMS_DIR):
        brand_dir = os.path.join(DESIGN_SYSTEMS_DIR, brand_id)
        design_md_path = os.path.join(brand_dir, "DESIGN.md")
        
        if os.path.isdir(brand_dir) and os.path.exists(design_md_path):
            parser = DesignSystemParser(brand_id)
            summary = parser.get_summary()
            
            # 获取分类
            category = "其他"
            for cat, items in BRAND_CATEGORIES.items():
                if brand_id in items:
                    category = cat
                    break
            
            brands.append({
                "id": brand_id,
                "name": summary.get("brand_name", brand_id),
                "category": category,
                "primary_color": summary.get("colors", {}).get("primary", "#3B82F6"),
                "description": summary.get("theme", {}).get("description", "")[:100],
                "exists": summary.get("exists", False),
            })
    
    # 按分类排序
    brands.sort(key=lambda x: (x["category"], x["name"]))
    return brands


def get_brand_by_id(brand_id: str) -> Optional[Dict]:
    """根据ID获取品牌设计系统"""
    parser = DesignSystemParser(brand_id)
    return parser.get_summary() if parser.parsed.get("exists") else None


if __name__ == "__main__":
    # 测试解析器
    brands = get_available_brands()
    print(f"Found {len(brands)} design systems:\n")
    
    for brand in brands[:5]:
        print(f"- {brand['name']} ({brand['id']})")
        print(f"  Category: {brand['category']}")
        print(f"  Primary Color: {brand['primary_color']}")
        print(f"  Description: {brand['description'][:80]}...")
        print()
