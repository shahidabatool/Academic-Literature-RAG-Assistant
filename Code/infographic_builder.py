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


def build_infographic_html(data):
    """
    Build a premium HTML infographic from structured JSON data.
    
    Expected data format:
    {
        "title": "Paper Title",
        "authors": "Author names",
        "hero_steps": ["Step 1", "Step 2", ...],
        "sections": [
            {
                "heading": "Section Title",
                "points": ["point 1", "point 2", ...],
                "stat": "94%",           # optional
                "stat_label": "Accuracy"  # optional
            }
        ],
        "bottom_stats": [
            {"value": "94%", "label": "Accuracy"},
            ...
        ]
    }
    """
    title = data.get("title", "Bloodstain Pattern Analysis")
    authors = data.get("authors", "")
    hero_steps = data.get("hero_steps", [])
    sections = data.get("sections", [])
    bottom_stats = data.get("bottom_stats", [])
    
    # Filter out obviously hallucinated/default stats
    filtered_stats = []
    for s in bottom_stats:
        val = str(s.get("value", ""))
        # Skip if it's just a default year or empty
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
    
    # Split sections into two groups
    mid = max(len(sections) // 2, 1)
    group1 = sections[:mid]
    group2 = sections[mid:]
    
    # Build cards
    def build_card(section, idx, global_idx):
        color = CARD_COLORS[global_idx % len(CARD_COLORS)]
        emoji = get_emoji(section.get("heading", ""))
        heading = section.get("heading", "")
        points = section.get("points", [])
        stat = section.get("stat")
        stat_label = section.get("stat_label", "")
        
        # Filter out null/None stats
        if stat in [None, "null", "None", "N/A", ""]:
            stat = None
        
        points_html = ""
        for p in points:
            pt_emoji = get_emoji(p)
            points_html += f'''<li style="border-left-color: {color['border']};">
                <span class="bullet-emoji">{pt_emoji}</span> {p}
            </li>'''
        
        stat_html = ""
        if stat:
            stat_html = f'''
            <div class="stat-badge" style="background: {color['accent']}15;">
                <div class="stat-value" style="color: {color['accent']};">{stat}</div>
                <div class="stat-label" style="color: {color['accent']}99;">{stat_label}</div>
            </div>'''
        
        return f'''
        <div class="card" style="background: {color['bg']}; border-top: 4px solid {color['border']};">
            <h3 style="color: {color['accent']};">{emoji} {heading}</h3>
            <ul>{points_html}</ul>
            {stat_html}
        </div>'''
    
    cards_group1 = "\n".join(build_card(s, i, i) for i, s in enumerate(group1))
    cards_group2 = "\n".join(build_card(s, i, i + mid) for i, s in enumerate(group2))
    
    # Bottom stats bar
    stats_html = ""
    stat_accents = ["#E65100", "#0D47A1", "#2E7D32"]
    for i, s in enumerate(bottom_stats):
        accent = stat_accents[i % len(stat_accents)]
        stats_html += f'''
        <div class="bottom-stat">
            <div class="bottom-stat-value" style="color: {accent};">{s.get("value", "")}</div>
            <div class="bottom-stat-label">{s.get("label", "")}</div>
        </div>'''
    
    bottom_bar_html = f'<div class="bottom-bar">{stats_html}</div>' if stats_html else ""
    
    # Count sections for the section counter badge
    section_count = len(sections)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: 'Inter', -apple-system, sans-serif;
    background: #f0f4f8;
    background-image: radial-gradient(circle, #d5d8dc 0.8px, transparent 0.8px);
    background-size: 16px 16px;
    padding: 50px 16px 60px;
    -webkit-font-smoothing: antialiased;
}}

.container {{
    max-width: 1100px;
    margin: 0 auto;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 28px;
    box-shadow: 
        0 4px 6px rgba(0,0,0,0.02),
        0 12px 24px rgba(0,0,0,0.04),
        0 24px 48px rgba(0,0,0,0.06);
    padding: 52px 36px 36px;
    border: 1px solid rgba(255,255,255,0.8);
}}

/* ─── Header ─── */
.header {{
    text-align: center;
    margin-bottom: 28px;
    padding-bottom: 24px;
    border-bottom: 2px solid #f0f0f0;
}}
.header h1 {{
    font-size: 1.85em;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.25;
    margin-bottom: 10px;
    letter-spacing: -0.5px;
}}
.header .authors {{
    font-size: 0.95em;
    color: #64748b;
    font-style: italic;
    font-weight: 400;
}}
.section-count {{
    display: inline-block;
    margin-top: 10px;
    padding: 4px 14px;
    background: #f1f5f9;
    border-radius: 20px;
    font-size: 0.75em;
    font-weight: 600;
    color: #64748b;
    letter-spacing: 0.5px;
}}

/* ─── Hero Flow ─── */
.hero {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    flex-wrap: wrap;
    padding: 16px 20px;
    background: linear-gradient(135deg, #f8fafc, #e2e8f0);
    border-radius: 16px;
    margin-bottom: 24px;
    border: 1px solid #e2e8f0;
}}
.pill {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 8px 16px;
    background: white;
    border-radius: 50px;
    font-size: 0.78em;
    font-weight: 600;
    color: #1e293b;
    white-space: nowrap;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    border: 1.5px solid #e2e8f0;
    transition: transform 0.15s;
}}
.arrow {{
    font-size: 1em;
    color: #94a3b8;
    flex-shrink: 0;
    font-weight: 300;
}}

/* ─── Section Bands ─── */
.band {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 20px;
    border-radius: 12px;
    font-size: 0.82em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 24px 0 16px 0;
}}
.band::before {{
    content: '';
    width: 4px;
    height: 20px;
    border-radius: 2px;
    flex-shrink: 0;
}}
.band-1 {{ 
    background: linear-gradient(135deg, #FEF3C7, #FDE68A);
    color: #92400E;
}}
.band-1::before {{ background: #F59E0B; }}
.band-2 {{ 
    background: linear-gradient(135deg, #CFFAFE, #A5F3FC);
    color: #155E75;
}}
.band-2::before {{ background: #06B6D4; }}

/* ─── Card Grid ─── */
.grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}}

.card {{
    border-radius: 16px;
    padding: 20px 22px;
    min-height: 160px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    border: 1px solid rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
}}
.card::after {{
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 80px;
    height: 80px;
    background: rgba(255,255,255,0.3);
    border-radius: 0 0 0 80px;
    pointer-events: none;
}}

.card h3 {{
    font-size: 0.82em;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 12px;
    line-height: 1.3;
}}

.card ul {{
    list-style: none;
    padding: 0;
    margin: 0;
}}
.card li {{
    padding: 5px 0 5px 12px;
    border-left: 2.5px solid #ddd;
    margin-bottom: 4px;
    font-size: 0.8em;
    color: #374151;
    line-height: 1.45;
    font-weight: 400;
}}
.bullet-emoji {{
    margin-right: 3px;
    font-size: 0.85em;
}}

/* ─── Stat Badge ─── */
.stat-badge {{
    margin-top: 14px;
    padding: 12px 16px;
    border-radius: 12px;
    text-align: center;
}}
.stat-value {{
    font-size: 2em;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -1px;
}}
.stat-label {{
    font-size: 0.65em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 3px;
}}

/* ─── Bottom Stats Bar ─── */
.bottom-bar {{
    display: flex;
    justify-content: space-evenly;
    align-items: center;
    background: linear-gradient(135deg, #1e293b, #334155);
    border-radius: 16px;
    padding: 28px 20px;
    margin-top: 24px;
}}
.bottom-stat {{
    text-align: center;
}}
.bottom-stat-value {{
    font-size: 2.4em;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -1px;
}}
.bottom-stat-label {{
    font-size: 0.65em;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #94a3b8;
    margin-top: 5px;
}}

.footer {{
    text-align: center;
    margin-top: 20px;
    font-size: 0.7em;
    color: #94a3b8;
    font-weight: 500;
    letter-spacing: 0.5px;
}}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>{title}</h1>
        <p class="authors">by {authors}</p>
        <div class="section-count">📄 {section_count} SECTIONS EXTRACTED</div>
    </div>
    
    <div class="hero">{hero_html}</div>
    
    <div class="band band-1">📋 Methodology &amp; Classification</div>
    <div class="grid">{cards_group1}</div>
    
    <div class="band band-2">📊 Results &amp; Conclusions</div>
    <div class="grid">{cards_group2}</div>
    
    {bottom_bar_html}
    
    <div class="footer">GENERATED BY BPA RAG RESEARCH ASSISTANT</div>
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
