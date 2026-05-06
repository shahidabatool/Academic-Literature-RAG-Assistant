"""
Premium Infographic HTML Builder v2
Generates pixel-perfect, NotebookLM-quality infographics from structured JSON data.
The LLM extracts content → this module renders the design.
"""

import json
import re

# Card color palette - refined with gradients
CARD_COLORS = [
    {"bg": "linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%)", "border": "#FF9800", "accent": "#E65100", "flat": "#FFF3E0"},
    {"bg": "linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)", "border": "#2196F3", "accent": "#0D47A1", "flat": "#E3F2FD"},
    {"bg": "linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%)", "border": "#9C27B0", "accent": "#6A1B9A", "flat": "#F3E5F5"},
    {"bg": "linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)", "border": "#4CAF50", "accent": "#2E7D32", "flat": "#E8F5E9"},
    {"bg": "linear-gradient(135deg, #FFFDE7 0%, #FFF9C4 100%)", "border": "#FFC107", "accent": "#F57F17", "flat": "#FFFDE7"},
    {"bg": "linear-gradient(135deg, #FCE4EC 0%, #F8BBD0 100%)", "border": "#E91E63", "accent": "#AD1457", "flat": "#FCE4EC"},
    {"bg": "linear-gradient(135deg, #E0F2F1 0%, #B2DFDB 100%)", "border": "#009688", "accent": "#00695C", "flat": "#E0F2F1"},
    {"bg": "linear-gradient(135deg, #EDE7F6 0%, #D1C4E9 100%)", "border": "#673AB7", "accent": "#4527A0", "flat": "#EDE7F6"},
    {"bg": "linear-gradient(135deg, #E8EAF6 0%, #C5CAE9 100%)", "border": "#3F51B5", "accent": "#283593", "flat": "#E8EAF6"},
    {"bg": "linear-gradient(135deg, #EFEBE9 0%, #D7CCC8 100%)", "border": "#795548", "accent": "#4E342E", "flat": "#EFEBE9"},
]

# Topic → emoji mapping (expanded for better coverage)
TOPIC_EMOJIS = {
    "classification": "🔬", "types": "🔬", "categor": "📂",
    "pattern": "🩸", "stain": "🩸",
    "spatter": "💧", "impact": "💥", "cast-off": "💫", "arterial": "🫀",
    "direction": "🎯", "angle": "📐", "trajectory": "📏", "convergence": "🎯",
    "crime scene": "🔍", "investigation": "🕵️", "evidence": "📋", "collection": "📦",
    "reconstruction": "🏗️",
    "machine learning": "🤖", "deep learning": "🧠", "computational": "💻",
    "cnn": "🧠", "random forest": "🌲", "neural": "🧬",
    "accuracy": "🎯", "model": "📊",
    "fluid": "🌊", "viscosity": "⚗️", "dynamics": "🔄", "surface tension": "💧",
    "velocity": "💨",
    "morphology": "🔎", "shape": "🔷", "size": "📏", "diameter": "⭕",
    "elongat": "↗️",
    "anatomy": "🫀", "blood": "🩸", "physiology": "💉", "coagul": "🧬",
    "cell": "🔴", "plasma": "💛",
    "experiment": "🧪", "laboratory": "🏥", "method": "⚙️", "apparatus": "🔧",
    "substrate": "🧱", "controlled": "📏",
    "legal": "⚖️", "daubert": "📜", "testimony": "🏛️", "court": "⚖️",
    "expert": "👨‍⚖️", "standard": "📋", "quality": "✅",
    "conclusion": "📝", "result": "📈", "finding": "💡", "future": "🔮",
    "passive": "⬇️", "active": "⚡", "projected": "➡️", "transfer": "🔄",
    "default": "📌"
}

def get_emoji(heading):
    """Get the most specific emoji match for a heading."""
    h = heading.lower()
    # Try longer phrases first for specificity
    sorted_keys = sorted(TOPIC_EMOJIS.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in h:
            return TOPIC_EMOJIS[key]
    return TOPIC_EMOJIS["default"]


def build_infographic_html(data, hero_img_path=None):
    """
    Build a premium dark-mode HTML infographic from structured JSON data.
    """
    title = data.get("title", "Bloodstain Pattern Analysis")
    authors = data.get("authors", "")
    hero_steps = data.get("hero_steps", [])
    sections = data.get("sections", [])
    bottom_stats = data.get("bottom_stats", [])
    
    # Hero Image handling (base64 or direct)
    hero_style = ""
    if hero_img_path:
        import base64
        try:
            with open(hero_img_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
                hero_style = f'background-image: url("data:image/png;base64,{img_data}");'
        except:
            pass

    # Filter out obviously hallucinated/default stats
    filtered_stats = []
    for s in bottom_stats:
        val = str(s.get("value", ""))
        if val not in ["2025", "2026", "N/A", "", "null", "None"]:
            filtered_stats.append(s)
    bottom_stats = filtered_stats[:3]
    
    # Build hero pills
    hero_html = ""
    for i, step in enumerate(hero_steps):
        emoji = get_emoji(step)
        color = CARD_COLORS[i % len(CARD_COLORS)]
        hero_html += f'<div class="pill" style="border-color: {color["border"]};">{emoji} {step}</div>'
        if i < len(hero_steps) - 1:
            hero_html += '<span class="arrow">→</span>'
    
    # Split sections into groups
    mid = max(len(sections) // 2, 1)
    group1 = sections[:mid]
    group2 = sections[mid:]
    
    def build_card(section, idx, global_idx):
        color = CARD_COLORS[global_idx % len(CARD_COLORS)]
        emoji = get_emoji(section.get("heading", ""))
        heading = section.get("heading", "")
        points = section.get("points", [])
        stat = section.get("stat")
        stat_label = section.get("stat_label", "")
        
        if stat in [None, "null", "None", "N/A", ""]: stat = None
        
        points_html = ""
        for p in points:
            pt_emoji = get_emoji(p)
            points_html += f'<li><span class="bullet-emoji">{pt_emoji}</span> {p}</li>'
        
        stat_html = ""
        if stat:
            stat_html = f'''
            <div class="stat-badge" style="background: rgba(255,255,255,0.05); border: 1px solid {color['border']}50;">
                <div class="stat-value" style="color: {color['border']};">{stat}</div>
                <div class="stat-label" style="color: rgba(255,255,255,0.5);">{stat_label}</div>
            </div>'''
        
        return f'''
        <div class="card" style="background: rgba(30, 41, 59, 0.7); border-left: 4px solid {color['border']};">
            <h3 style="color: {color['border']};">{emoji} {heading}</h3>
            <ul>{points_html}</ul>
            {stat_html}
        </div>'''
    
    cards_group1 = "\n".join(build_card(s, i, i) for i, s in enumerate(group1))
    cards_group2 = "\n".join(build_card(s, i, i + mid) for i, s in enumerate(group2))
    
    stats_html = ""
    stat_colors = ["#F59E0B", "#3B82F6", "#10B981"]
    for i, s in enumerate(bottom_stats):
        color = stat_colors[i % len(stat_colors)]
        stats_html += f'''
        <div class="bottom-stat">
            <div class="bottom-stat-value" style="color: {color};">{s.get("value", "")}</div>
            <div class="bottom-stat-label">{s.get("label", "")}</div>
        </div>'''
    
    bottom_bar_html = f'<div class="bottom-bar">{stats_html}</div>' if stats_html else ""
    section_count = len(sections)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: 'Outfit', sans-serif;
    background: #0f172a;
    color: #f8fafc;
    padding: 40px 16px;
    -webkit-font-smoothing: antialiased;
}}

.container {{
    max-width: 1000px;
    margin: 0 auto;
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(20px);
    border-radius: 32px;
    overflow: hidden;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.1);
}}

/* ─── Hero Banner ─── */
.hero-banner {{
    height: 400px;
    {hero_style}
    background-size: cover;
    background-position: center;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    padding: 40px;
}}
.hero-banner::after {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(to top, #0f172a 0%, transparent 100%);
}}
.hero-content {{
    position: relative;
    z-index: 10;
}}
.hero-banner h1 {{
    font-size: 2.5em;
    font-weight: 800;
    letter-spacing: -1px;
    line-height: 1.1;
    margin-bottom: 8px;
    background: linear-gradient(to right, #fff, #94a3b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.hero-banner .authors {{
    font-size: 1.1em;
    color: #94a3b8;
    font-weight: 400;
}}

/* ─── Hero Flow ─── */
.flow-container {{
    padding: 24px 40px;
    background: rgba(30, 41, 59, 0.5);
    border-bottom: 1px solid rgba(255,255,255,0.05);
}}
.hero-flow {{
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}}
.pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: rgba(255,255,255,0.05);
    border-radius: 50px;
    font-size: 0.8em;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,0.1);
}}
.arrow {{ color: #475569; font-weight: 300; }}

/* ─── Grid ─── */
.content-area {{ padding: 32px 40px; }}
.band {{
    font-size: 0.75em;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #64748b;
    margin: 32px 0 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}}
.band::after {{
    content: '';
    height: 1px;
    flex-grow: 1;
    background: rgba(255,255,255,0.05);
}}

.grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}}

.card {{
    border-radius: 20px;
    padding: 24px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.03);
}}
.card h3 {{
    font-size: 0.9em;
    font-weight: 700;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.card ul {{ list-style: none; }}
.card li {{
    font-size: 0.85em;
    color: #94a3b8;
    line-height: 1.5;
    margin-bottom: 8px;
    display: flex;
    gap: 8px;
}}
.bullet-emoji {{ opacity: 0.8; }}

.stat-badge {{
    margin-top: 20px;
    padding: 12px;
    border-radius: 12px;
    text-align: center;
}}
.stat-value {{ font-size: 1.8em; font-weight: 800; }}
.stat-label {{ font-size: 0.6em; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}

/* ─── Bottom Bar ─── */
.bottom-bar {{
    display: flex;
    justify-content: space-around;
    padding: 40px;
    background: rgba(2, 6, 23, 0.5);
    border-top: 1px solid rgba(255,255,255,0.05);
}}
.bottom-stat {{ text-align: center; }}
.bottom-stat-value {{ font-size: 2.2em; font-weight: 800; margin-bottom: 4px; }}
.bottom-stat-label {{ font-size: 0.65em; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 2px; }}

.footer {{
    padding: 24px;
    text-align: center;
    font-size: 0.65em;
    color: #475569;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
</style>
</head>
<body>
<div class="container">
    <div class="hero-banner">
        <div class="hero-content">
            <h1>{title}</h1>
            <p class="authors">by {authors}</p>
        </div>
    </div>
    
    <div class="flow-container">
        <div class="hero-flow">{hero_html}</div>
    </div>
    
    <div class="content-area">
        <div class="band">Forensic Methodology</div>
        <div class="grid">{cards_group1}</div>
        
        <div class="band">Research Findings</div>
        <div class="grid">{cards_group2}</div>
    </div>
    
    {bottom_bar_html}
    
    <div class="footer">
        Generated by BPA RAG Assistant • {section_count} Data Points Analyzed
    </div>
</div>
</body>
</html>'''
    
    return html


def parse_llm_json(response_text):
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try to find JSON in code blocks
    match = re.search(r'```(?:json)?\s*\n(.*?)```', response_text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
    else:
        # Try raw JSON
        json_str = response_text.strip()
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Try to find any JSON object in the text
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None
