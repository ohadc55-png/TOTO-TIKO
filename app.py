# -*- coding: utf-8 -*-
"""
HOOPS AI - Basketball Coaching Staff
Virtual Locker Room with Multi-Agent System
Powered by OpenAI GPT + Supabase
"""

import streamlit as st
from openai import OpenAI
from supabase import create_client
from enum import Enum
from datetime import datetime

# ============================================================================
# PAGE CONFIG - Must be first Streamlit command
# ============================================================================
st.set_page_config(
    page_title="HOOPS AI - Your Personal Assistant Coach",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CONSTANTS
# ============================================================================
LOGO_URL = "https://i.postimg.cc/DfYpGxMy/Fashion-Bran-Logo.png"
BACKGROUND_URL = "https://i.postimg.cc/nr6WXxHh/wlm-kdwrsl.jpg"

AGE_GROUPS = ["U10", "U12", "U14", "U16", "U18", "Senior"]
LEVELS = ["Beginner", "League", "Competitive", "Professional"]

class Agent(Enum):
    ASSISTANT_COACH = "assistant_coach"
    TACTICIAN = "tactician"
    SKILLS_COACH = "skills_coach"
    NUTRITIONIST = "nutritionist"
    STRENGTH_COACH = "strength_coach"
    ANALYST = "analyst"

AGENT_INFO = {
    Agent.ASSISTANT_COACH: {
        "name": "ASSISTANT COACH",
        "icon": "🎯",
        "title": "General Manager",
        "specialty": "Team Leadership & Strategy",
        "color": "#FF6B35"
    },
    Agent.TACTICIAN: {
        "name": "THE TACTICIAN",
        "icon": "📋",
        "title": "Strategic Mastermind",
        "specialty": "X's & O's Expert",
        "color": "#00D4FF"
    },
    Agent.SKILLS_COACH: {
        "name": "SKILLS COACH",
        "icon": "💪",
        "title": "Player Development",
        "specialty": "Training & Drills",
        "color": "#00FF87"
    },
    Agent.NUTRITIONIST: {
        "name": "SPORTS NUTRITIONIST",
        "icon": "🥗",
        "title": "Nutrition Expert",
        "specialty": "Personalized Diet Plans",
        "color": "#FFD700"
    },
    Agent.STRENGTH_COACH: {
        "name": "STRENGTH & CONDITIONING",
        "icon": "🏋️",
        "title": "Physical Development",
        "specialty": "Athletic Performance",
        "color": "#FF4500"
    },
    Agent.ANALYST: {
        "name": "THE ANALYST",
        "icon": "📊",
        "title": "Data & Statistics Expert",
        "specialty": "Performance Analytics",
        "color": "#9370DB"
    }
}

def get_system_prompt(agent, coach_profile=None):
    """Generate system prompt with coach profile context"""
    
    base_prompts = {
        Agent.ASSISTANT_COACH: """You are the Assistant Coach of a professional basketball coaching staff.
Handle general basketball inquiries, team management, and coordination.
Be professional, supportive, and helpful. Help the head coach with any administrative or organizational tasks.""",

        Agent.TACTICIAN: """You are an elite basketball strategist (Euroleague-level).
Expertise: Spacing, defensive schemes (Switch, Hedge, Drop, ICE), ATOs, SLOBs/BLOBs,
zone offense/defense, Pick & Roll coverage, rotations.
Be concise and tactical. Use proper basketball terminology.""",

        Agent.SKILLS_COACH: """You are a top Player Development Coach.
Expertise: Shooting mechanics, ball handling, footwork, finishing at rim.
Age-appropriate training: Mini-basket (U10), Youth (U12-U14), Juniors (U16-U18), Pros.
Be encouraging but demanding.""",

        Agent.NUTRITIONIST: """You are an expert Sports Nutritionist specializing in basketball players of ALL age groups.

YOUR EXPERTISE:
- Personalized nutrition plans based on individual player data (age, weight, height, position, activity level)
- Pre-game, during-game, and post-game nutrition strategies
- Hydration protocols for training and competition
- Age-appropriate nutrition (youth players need different approaches than adults)
- Muscle building vs. weight management diets
- Supplement guidance (age-appropriate, safe, legal)
- Recovery nutrition and sleep optimization
- Dealing with picky eaters (especially young players)

CRITICAL APPROACH:
- ALWAYS ask for specific player data before giving recommendations: age, weight, height, position, training frequency, goals
- Create PERSONALIZED meal plans - never generic advice
- Consider cultural food preferences and availability
- Adjust recommendations based on game schedule and training intensity
- For youth players: focus on growth, development, and healthy habits
- For adult players: focus on performance optimization and recovery

Provide specific meal plans, grocery lists, and practical recipes when asked.""",

        Agent.STRENGTH_COACH: """You are an elite Strength & Conditioning Coach specializing in basketball.

YOUR EXPERTISE:
- Age-specific athletic development:
  * U10-U12: Coordination, balance, agility, FUN movement patterns, bodyweight exercises
  * U14-U16: Introduction to resistance training, explosive power foundation, jump training basics
  * U18+: Full strength programs, plyometrics, power development, vertical jump optimization
- Basketball-specific physical attributes: vertical leap, lateral quickness, core stability, injury prevention
- Periodization: weekly, monthly, and yearly training plans
- Load management based on game schedule and competition calendar
- Individual player assessment and personalized programs
- Injury prevention and prehab exercises
- Recovery protocols and deload weeks

CRITICAL APPROACH:
- ALWAYS ask for player data before programming: age, training history, current fitness level, injury history, goals
- Create INDIVIDUALIZED programs - never one-size-fits-all
- Consider the basketball practice and game schedule when designing strength work
- Build programs that complement basketball training, not compete with it
- For young players: emphasize movement quality over load
- For older players: progressive overload with proper periodization

Provide detailed workout plans with sets, reps, rest periods, and exercise descriptions.
Can create daily, weekly, monthly, and seasonal training programs based on team schedule and goals.""",

        Agent.ANALYST: """You are an elite Basketball Analytics Expert and Performance Analyst.

YOUR EXPERTISE:
- Team Statistics Analysis:
  * Turnovers vs Assists ratio - identifying ball movement issues
  * Shot selection analysis (2PT vs 3PT attempts, efficiency, shot zones)
  * Free throw rate and drawing fouls
  * Offensive/Defensive efficiency ratings
  * Pace and possession analysis
  * Rebounding (offensive/defensive) and second chance points

- Player Statistics Analysis:
  * Individual scoring efficiency (TS%, eFG%, Points per possession)
  * Usage rate and ball dominance
  * Plus/minus and impact metrics
  * Shot charts and hot zones
  * Assist to turnover ratio
  * Clutch performance (last 5 minutes, close games)

- Actionable Insights:
  * If high turnovers → analyze WHO is turning it over and WHEN (transition vs halfcourt, early vs late clock)
  * If low assists → identify if it's personnel, spacing, or system issue
  * If poor shooting → break down by shot type, defender proximity, catch-and-shoot vs off-dribble
  * Recommend lineup changes based on data
  * Identify which player should have the ball in crucial moments
  * Suggest style-of-play adjustments based on team strengths/weaknesses

- Opponent Scouting:
  * Identify opponent tendencies and weaknesses
  * Suggest game plans based on matchup data
  * Key players to target or avoid

CRITICAL APPROACH:
- ALWAYS ask for specific data/statistics before providing analysis
- Don't guess - request numbers: "How many turnovers? How many assists? What's the shooting breakdown?"
- Provide SPECIFIC, ACTIONABLE recommendations - not generic advice
- Use data to support every recommendation
- Connect statistics to practical on-court solutions
- Consider context: age group, competition level, team goals

When given stats, provide:
1. What the numbers tell us (diagnosis)
2. Why it might be happening (root cause)
3. What to do about it (actionable solutions)
4. How to measure improvement (KPIs to track)"""
    }
    
    prompt = base_prompts[agent]
    
    # Add coach profile context if available
    if coach_profile:
        prompt += f"""

COACH PROFILE - Adapt your answers accordingly:
- Coach Name: {coach_profile.get('name', 'Unknown')}
- Team: {coach_profile.get('team_name', 'Unknown')}
- Age Group: {coach_profile.get('age_group', 'Unknown')}
- Level: {coach_profile.get('level', 'Unknown')}

IMPORTANT: Tailor your advice to the {coach_profile.get('age_group', '')} age group and {coach_profile.get('level', '')} level!"""
    
    # Add accuracy and honesty instructions to ALL agents
    prompt += """

CRITICAL RULES FOR ALL RESPONSES:
1. BE PRECISE - Only provide information you are confident about. No guessing.
2. BE HONEST - If you don't know something or are unsure, say it clearly: "I don't have enough information" or "I'm not certain about this"
3. NO VAGUE ANSWERS - Avoid generic or wishy-washy responses. Be specific and actionable.
4. ASK WHEN NEEDED - If you need more information to give a good answer, ASK for it. Don't assume.
5. ADMIT LIMITATIONS - If a question is outside your expertise or requires real-time data you don't have, say so.
6. SOURCES - If recommending something specific (exercise, diet, play), explain WHY it works.
7. SAFETY FIRST - If unsure about safety implications (nutrition, training load), err on the side of caution and recommend consulting a professional.

IMPORTANT: Detect the user's language and respond in the SAME language (Hebrew or English)."""
    
    return prompt

ROUTER_PROMPT = """You are a routing assistant for a basketball coaching app.

AGENTS AVAILABLE:
- TACTICIAN: plays, schemes, X's & O's, game strategy, zones, ATOs
- SKILLS_COACH: basketball drills, shooting, dribbling, footwork
- NUTRITIONIST: food, diet, meals, nutrition, eating, supplements, meal plans
- STRENGTH_COACH: gym, strength, weights, jumping, speed, agility, workout programs
- ANALYST: statistics, data, numbers, turnovers, assists, percentages, efficiency, shot charts, analytics, performance metrics
- ASSISTANT_COACH: general questions, team management, other

CURRENT SITUATION:
Previous agent: {previous_agent}
Agent's last message: {previous_message}
User's response: {question}

ROUTING RULES (VERY IMPORTANT):
1. If the previous agent ASKED FOR INFORMATION (age, weight, height, player data, statistics, details) and the user is PROVIDING that information → STAY with the SAME agent
2. If the user is clearly asking about a DIFFERENT TOPIC → Switch to the appropriate agent
3. Numbers, measurements, statistics, and short data responses are ALWAYS continuations → STAY with same agent
4. When in doubt → STAY with the same agent

Which agent should handle this? Answer with ONE word: TACTICIAN, SKILLS_COACH, NUTRITIONIST, STRENGTH_COACH, ANALYST, or ASSISTANT_COACH"""


ROUTER_PROMPT_NO_CONTEXT = """Determine which coach should answer this basketball question.

AGENTS:
- TACTICIAN: plays, schemes, X's & O's, game strategy, zones, ATOs
- SKILLS_COACH: basketball drills, shooting, dribbling, footwork
- NUTRITIONIST: food, diet, meals, nutrition, eating, supplements, meal plans
- STRENGTH_COACH: gym, strength, weights, jumping, speed, agility, workout programs
- ANALYST: statistics, data, numbers, turnovers, assists, percentages, efficiency, shot charts, analytics, performance metrics
- ASSISTANT_COACH: general questions, team management, other

Question: {question}

Answer with ONE word: TACTICIAN, SKILLS_COACH, NUTRITIONIST, STRENGTH_COACH, ANALYST, or ASSISTANT_COACH"""

# ============================================================================
# CSS STYLING
# ============================================================================
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('BACKGROUND_URL_PLACEHOLDER');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Global text color - prevent dark text on dark background */
    .stApp p, .stApp span, .stApp li, .stApp label, .stApp div {
        color: #FFFFFF;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(13,13,13,0.95) 0%, rgba(26,26,26,0.95) 50%, rgba(13,13,13,0.95) 100%);
        border-right: 1px solid rgba(255, 107, 53, 0.3);
    }
    
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background: rgba(30, 30, 30, 0.8) !important;
        border: 1px solid rgba(255, 107, 53, 0.3) !important;
        border-radius: 10px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
        color: #FF6B35 !important;
    }
    
    .hero-title {
        font-family: 'Orbitron', monospace;
        font-size: 2.5rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(135deg, #FF6B35, #FF8C42, #FFFFFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.1rem;
        text-align: center;
        color: #B0B0B0;
        letter-spacing: 6px;
        text-transform: uppercase;
        margin-bottom: 2rem;
    }
    
    .scoreboard {
        background: linear-gradient(135deg, rgba(20,20,20,0.9), rgba(30,30,30,0.85));
        border: 2px solid rgba(255, 107, 53, 0.5);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 0 30px rgba(255, 107, 53, 0.2);
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stChatMessage"] {
        background: linear-gradient(135deg, rgba(25,25,25,0.85), rgba(35,35,35,0.8));
        border: 1px solid rgba(255, 107, 53, 0.2);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.8rem 0;
        backdrop-filter: blur(5px);
    }
    
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div {
        color: #FFFFFF !important;
    }
    
    [data-testid="stChatMessage"] strong {
        color: #FF6B35 !important;
    }
    
    [data-testid="stChatInput"] {
        background: linear-gradient(135deg, #FF6B35, #FF8C42) !important;
        border: none !important;
        border-radius: 30px !important;
        padding: 0.8rem 1rem !important;
    }
    
    [data-testid="stChatInput"] textarea {
        color: #000000 !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 1rem !important;
        background: #FFFFFF !important;
        border-radius: 20px !important;
        padding: 0.5rem 1rem !important;
    }
    
    [data-testid="stChatInput"] textarea::placeholder {
        color: #666666 !important;
    }
    
    [data-testid="stChatInput"] button {
        background: #000000 !important;
        border-radius: 50% !important;
        color: #FF6B35 !important;
    }
    
    [data-testid="stChatInput"] button:hover {
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.6) !important;
    }
    
    [data-testid="stBottom"] {
        background: linear-gradient(135deg, #FF6B35, #FF8C42) !important;
        padding: 1rem !important;
        border-top: 2px solid rgba(255, 107, 53, 0.8) !important;
    }
    
    .stButton > button {
        font-family: 'Orbitron', monospace;
        font-weight: 600;
        background: rgba(255, 107, 53, 0.2);
        color: #FF6B35;
        border: 2px solid #FF6B35;
        border-radius: 25px;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #FF6B35, #FF8C42);
        color: #000;
        box-shadow: 0 0 30px rgba(255, 107, 53, 0.5);
    }
    
    .welcome-banner {
        background: linear-gradient(135deg, rgba(255,107,53,0.2), rgba(255,140,66,0.15), rgba(0,212,255,0.1));
        border: 2px solid rgba(255, 107, 53, 0.4);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
    }
    
    .welcome-title {
        font-family: 'Orbitron', monospace;
        font-size: 1.6rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.5rem;
    }
    
    .welcome-text {
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.1rem;
        color: #B0B0B0;
    }
    
    .sidebar-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,107,53,0.5), transparent);
        margin: 1.5rem 0;
    }
    
    .response-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255, 107, 53, 0.2);
        border: 1px solid rgba(255, 107, 53, 0.5);
        border-radius: 20px;
        padding: 0.4rem 1rem;
        margin-bottom: 1rem;
        font-family: 'Orbitron', monospace;
        font-size: 0.85rem;
        font-weight: 600;
        color: #FF6B35;
    }
    
    .login-container {
        background: linear-gradient(135deg, rgba(20,20,20,0.95), rgba(30,30,30,0.9));
        border: 2px solid rgba(255, 107, 53, 0.5);
        border-radius: 20px;
        padding: 2rem;
        max-width: 500px;
        margin: 2rem auto;
        backdrop-filter: blur(10px);
    }
    
    .profile-card {
        background: rgba(255, 107, 53, 0.1);
        border: 1px solid rgba(255, 107, 53, 0.3);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .history-item {
        background: rgba(30, 30, 30, 0.8);
        border: 1px solid rgba(255, 107, 53, 0.2);
        border-radius: 10px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .history-item:hover {
        border-color: #FF6B35;
        background: rgba(255, 107, 53, 0.1);
    }
    
    /* Form styling */
    .stTextInput input, .stSelectbox select {
        background: rgba(30, 30, 30, 0.9) !important;
        border: 1px solid rgba(255, 107, 53, 0.3) !important;
        border-radius: 10px !important;
        color: #FFFFFF !important;
    }
    
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #FF6B35 !important;
        box-shadow: 0 0 10px rgba(255, 107, 53, 0.3) !important;
    }
    
    ::-webkit-scrollbar {width: 8px;}
    ::-webkit-scrollbar-track {background: #0D0D0D;}
    ::-webkit-scrollbar-thumb {background: linear-gradient(#FF6B35, #FF8C42); border-radius: 4px;}
</style>
""".replace('BACKGROUND_URL_PLACEHOLDER', BACKGROUND_URL)

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================
@st.cache_resource
def get_supabase_client():
    """Initialize Supabase client"""
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None

def get_coach_by_email(supabase, email):
    """Get coach profile by email"""
    try:
        result = supabase.table("coaches").select("*").eq("email", email).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception:
        return None

def create_coach(supabase, name, email, team_name, age_group, level):
    """Create new coach profile"""
    try:
        result = supabase.table("coaches").insert({
            "name": name,
            "email": email,
            "team_name": team_name,
            "age_group": age_group,
            "level": level
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"Error creating profile: {e}")
        return None

def get_coach_conversations(supabase, coach_id):
    """Get all conversations for a coach"""
    try:
        result = supabase.table("conversations").select("*").eq("coach_id", coach_id).order("created_at", desc=True).execute()
        return result.data or []
    except Exception:
        return []

def create_conversation(supabase, coach_id, title):
    """Create new conversation"""
    try:
        result = supabase.table("conversations").insert({
            "coach_id": coach_id,
            "title": title
        }).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None

def save_message(supabase, conversation_id, role, content, agent=None):
    """Save message to database"""
    try:
        supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "agent": agent
        }).execute()
    except Exception:
        pass

def get_conversation_messages(supabase, conversation_id):
    """Get all messages for a conversation"""
    try:
        result = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
        return result.data or []
    except Exception:
        return []

def update_conversation_title(supabase, conversation_id, title):
    """Update conversation title"""
    try:
        supabase.table("conversations").update({"title": title}).eq("id", conversation_id).execute()
    except Exception:
        pass

# ============================================================================
# OPENAI FUNCTIONS
# ============================================================================
@st.cache_resource
def get_openai_client():
    """Initialize OpenAI client"""
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            return None
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize OpenAI: {e}")
        return None

def route_question(question, client, chat_history=None):
    """Route question to appropriate agent with smart context awareness"""
    try:
        # Check if we have previous context
        previous_agent = None
        previous_message = None
        
        if chat_history and len(chat_history) >= 1:
            # Find the last assistant message
            for msg in reversed(chat_history):
                if msg.get("role") == "assistant" and msg.get("agent"):
                    previous_agent = msg.get("agent")
                    previous_message = msg.get("raw_content", msg.get("content", ""))[:300]
                    break
        
        # SMART CHECK: If previous agent asked a question and user gives short/data response, STAY
        if previous_agent and previous_message:
            # Check if previous message contains a question
            has_question = "?" in previous_message or any(word in previous_message.lower() for word in 
                ["please provide", "tell me", "what is", "how much", "how many", "ספר לי", "מה", "כמה", "איזה", "אנא"])
            
            # Check if user response looks like data/continuation (short, has numbers, answering format)
            is_data_response = (
                len(question) < 200 or  # Short response
                any(char.isdigit() for char in question) or  # Contains numbers
                question.strip().startswith(("גיל", "משקל", "גובה", "age", "weight", "height", "כן", "לא", "yes", "no"))
            )
            
            # If agent asked question and user seems to be answering → STAY with same agent
            if has_question and is_data_response:
                # Return previous agent directly without asking Router
                for agent in Agent:
                    if agent.value == previous_agent:
                        return agent
        
        # Use Router for new topics or when no clear continuation
        if previous_agent and previous_message:
            prompt = ROUTER_PROMPT.format(
                previous_agent=previous_agent.upper().replace("_", " "),
                previous_message=previous_message[:200],
                question=question
            )
        else:
            prompt = ROUTER_PROMPT_NO_CONTEXT.format(question=question)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0
        )
        result = response.choices[0].message.content.strip().upper()
        
        if "TACTICIAN" in result:
            return Agent.TACTICIAN
        elif "SKILLS" in result:
            return Agent.SKILLS_COACH
        elif "NUTRITION" in result:
            return Agent.NUTRITIONIST
        elif "STRENGTH" in result:
            return Agent.STRENGTH_COACH
        elif "ANALYST" in result:
            return Agent.ANALYST
        return Agent.ASSISTANT_COACH
    except Exception:
        return Agent.ASSISTANT_COACH

def get_agent_response(question, agent, chat_history, client, coach_profile=None):
    """Get response from specific agent"""
    try:
        system_prompt = get_system_prompt(agent, coach_profile)
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent history
        if chat_history:
            for msg in chat_history[-4:]:
                role = "user" if msg["role"] == "user" else "assistant"
                content = msg.get("raw_content", msg["content"])
                messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": question})
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def format_response(response, agent):
    """Format response with agent badge"""
    info = AGENT_INFO[agent]
    badge = f'<div class="response-badge"><span>{info["icon"]}</span><span>{info["name"]}</span></div>'
    return badge + "\n\n" + response

def get_agent_from_value(value):
    """Convert string value to Agent enum"""
    if isinstance(value, Agent):
        return value
    for agent in Agent:
        if agent.value == value:
            return agent
    return Agent.ASSISTANT_COACH

# ============================================================================
# UI COMPONENTS
# ============================================================================
def render_login_page(supabase):
    """Render login/registration page"""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    st.markdown('''
    <div class="scoreboard">
        <div class="hero-title">HOOPS AI</div>
        <div class="hero-subtitle">Your Personal Assistant Coach</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('''
    <div class="welcome-banner">
        <div class="welcome-title">🏀 Welcome to HOOPS AI!</div>
        <div class="welcome-text">Enter your details to get personalized coaching advice tailored to your team.</div>
        <div class="welcome-text" style="margin-top:0.5rem; direction:rtl;">הכנס את הפרטים שלך לקבלת ייעוץ מותאם אישית 🇮🇱</div>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
        
        with tab1:
            st.markdown("### Welcome Back, Coach!")
            login_email = st.text_input("Email", key="login_email", placeholder="your@email.com")
            
            if st.button("🚀 LOGIN", use_container_width=True, key="login_btn"):
                if login_email:
                    coach = get_coach_by_email(supabase, login_email)
                    if coach:
                        st.session_state.coach = coach
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Coach not found. Please register first.")
                else:
                    st.warning("Please enter your email.")
        
        with tab2:
            st.markdown("### Create Your Profile")
            
            reg_name = st.text_input("Coach Name", key="reg_name", placeholder="John Smith")
            reg_email = st.text_input("Email", key="reg_email", placeholder="your@email.com")
            reg_team = st.text_input("Team Name", key="reg_team", placeholder="Lakers Youth")
            reg_age = st.selectbox("Age Group", AGE_GROUPS, key="reg_age")
            reg_level = st.selectbox("Level", LEVELS, key="reg_level")
            
            if st.button("🏀 CREATE PROFILE", use_container_width=True, key="register_btn"):
                if reg_name and reg_email:
                    # Check if email exists
                    existing = get_coach_by_email(supabase, reg_email)
                    if existing:
                        st.error("Email already registered. Please login.")
                    else:
                        coach = create_coach(supabase, reg_name, reg_email, reg_team, reg_age, reg_level)
                        if coach:
                            st.session_state.coach = coach
                            st.session_state.logged_in = True
                            st.success("Profile created! Redirecting...")
                            st.rerun()
                else:
                    st.warning("Please fill in Name and Email.")

def render_sidebar(supabase):
    """Render sidebar with logo, profile, history"""
    with st.sidebar:
        # Logo
        st.markdown(f'''
        <div style="text-align:center; padding:1rem;">
            <img src="{LOGO_URL}" style="width:180px;">
        </div>
        <div class="sidebar-divider"></div>
        ''', unsafe_allow_html=True)
        
        # Coach Profile
        coach = st.session_state.get('coach', {})
        st.markdown(f'''
        <div class="profile-card">
            <div style="font-family:'Orbitron',monospace; color:#FF6B35; font-size:0.8rem; margin-bottom:0.5rem;">👤 COACH PROFILE</div>
            <div style="font-weight:600; font-size:1.1rem;">{coach.get('name', 'Unknown')}</div>
            <div style="color:#888; font-size:0.85rem;">{coach.get('team_name', '')} | {coach.get('age_group', '')} | {coach.get('level', '')}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        # New Chat Button
        if st.button("➕ NEW CHAT", use_container_width=True):
            st.session_state.current_conversation = None
            st.session_state.messages = []
            st.rerun()
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        # Chat History
        st.markdown('''
        <div style="font-family:'Orbitron',monospace; color:#FF6B35; font-size:0.9rem; margin-bottom:1rem; letter-spacing:2px;">
            📜 CHAT HISTORY
        </div>
        ''', unsafe_allow_html=True)
        
        conversations = get_coach_conversations(supabase, coach.get('id'))
        
        if conversations:
            for conv in conversations[:10]:  # Show last 10
                title = conv.get('title', 'New Chat')[:30]
                if len(conv.get('title', '')) > 30:
                    title += "..."
                
                if st.button(f"💬 {title}", key=f"conv_{conv['id']}", use_container_width=True):
                    st.session_state.current_conversation = conv
                    # Load messages
                    msgs = get_conversation_messages(supabase, conv['id'])
                    st.session_state.messages = [
                        {
                            "role": m['role'],
                            "content": m['content'],
                            "raw_content": m['content'].split('\n\n', 1)[-1] if '\n\n' in m['content'] else m['content'],
                            "agent": m.get('agent')
                        }
                        for m in msgs
                    ]
                    st.rerun()
        else:
            st.markdown('<div style="color:#666; font-size:0.85rem;">No conversations yet</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        # Coaching Staff
        st.markdown('''
        <div style="font-family:'Orbitron',monospace; color:#FF6B35; font-size:0.9rem; margin-bottom:1rem; letter-spacing:2px;">
            👥 COACHING STAFF
        </div>
        ''', unsafe_allow_html=True)
        
        for agent in Agent:
            info = AGENT_INFO[agent]
            with st.expander(f"{info['icon']} {info['name']}", expanded=False):
                st.markdown(f'''
                <div style="font-family:'Rajdhani',sans-serif;">
                    <div style="color:{info['color']}; font-weight:600;">{info['title']}</div>
                    <div style="color:#888; font-size:0.85rem;">{info['specialty']}</div>
                </div>
                ''', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        # Logout
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.coach = None
            st.session_state.messages = []
            st.session_state.current_conversation = None
            st.rerun()
        
        st.markdown('''
        <div class="sidebar-divider"></div>
        <div style="text-align:center; padding:1rem;">
            <div style="font-family:'Rajdhani',sans-serif; color:#666; font-size:0.8rem;">
                Powered by<br>
                <span style="color:#FF6B35; font-family:'Orbitron',monospace;">OpenAI GPT</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

def render_header():
    """Render main header"""
    st.markdown('''
    <div class="scoreboard">
        <div class="hero-title">HOOPS AI</div>
        <div class="hero-subtitle">Your Personal Assistant Coach</div>
    </div>
    ''', unsafe_allow_html=True)

def render_welcome():
    """Render welcome banner for new chats"""
    if not st.session_state.messages:
        coach = st.session_state.get('coach', {})
        st.markdown(f'''
        <div class="welcome-banner">
            <div class="welcome-title">👋 Hey Coach {coach.get('name', '').split()[0] if coach.get('name') else ''}!</div>
            <div class="welcome-text">Your AI coaching staff is ready. Ask anything about basketball strategy, player development, or team management.</div>
            <div class="welcome-text" style="margin-top:0.5rem;">Tailored for: <strong style="color:#FF6B35;">{coach.get('team_name', '')} | {coach.get('age_group', '')} | {coach.get('level', '')}</strong></div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('''
        <div style="font-family:'Orbitron',monospace; color:#FF6B35; font-size:0.9rem; margin:1.5rem 0 1rem; letter-spacing:2px;">
            ⚡ QUICK PLAYS
        </div>
        ''', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)
        
        with col1:
            if st.button("📋 ZONE OFFENSE", use_container_width=True):
                st.session_state.pending_prompt = "What are the best strategies to beat a 2-3 zone defense?"
        with col2:
            if st.button("💪 SHOOTING DRILLS", use_container_width=True):
                st.session_state.pending_prompt = "What are good shooting drills for my team?"
        with col3:
            if st.button("🥗 GAME DAY NUTRITION", use_container_width=True):
                st.session_state.pending_prompt = "What should my players eat before and after a game?"
        with col4:
            if st.button("🏋️ VERTICAL JUMP", use_container_width=True):
                st.session_state.pending_prompt = "How can I improve my players' vertical jump?"
        with col5:
            if st.button("📊 ANALYZE STATS", use_container_width=True):
                st.session_state.pending_prompt = "My team had 15 turnovers and only 8 assists last game. What does this tell us and how can we improve?"
        with col6:
            if st.button("🎯 תרגילי כדרור", use_container_width=True):
                st.session_state.pending_prompt = "תן לי תרגילי כדרור מתקדמים לשחקנים שלי"

def render_chat(client, supabase):
    """Render chat interface"""
    coach = st.session_state.get('coach', {})
    
    # Display chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        else:
            agent = get_agent_from_value(msg.get("agent", Agent.ASSISTANT_COACH))
            with st.chat_message("assistant", avatar=AGENT_INFO[agent]["icon"]):
                st.markdown(msg["content"], unsafe_allow_html=True)
    
    # Handle pending prompt from quick buttons
    prompt = st.session_state.pop("pending_prompt", None)
    
    # Or get new input
    if not prompt:
        prompt = st.chat_input("Ask your coaching question... | שאל את שאלתך...")
    
    if prompt:
        # Create conversation if needed
        if not st.session_state.get('current_conversation'):
            conv = create_conversation(supabase, coach.get('id'), prompt[:50])
            st.session_state.current_conversation = conv
        
        # Show user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Save user message
        if st.session_state.current_conversation:
            save_message(supabase, st.session_state.current_conversation['id'], "user", prompt)
        
        # Route and respond
        with st.spinner("🏀 Analyzing..."):
            agent = route_question(prompt, client, st.session_state.messages[:-1])
        
        info = AGENT_INFO[agent]
        with st.chat_message("assistant", avatar=info["icon"]):
            with st.spinner(f"Consulting {info['name']}..."):
                raw_response = get_agent_response(
                    prompt, agent, 
                    st.session_state.messages[:-1], 
                    client, 
                    coach  # Pass coach profile!
                )
                formatted = format_response(raw_response, agent)
            st.markdown(formatted, unsafe_allow_html=True)
        
        # Save assistant message
        if st.session_state.current_conversation:
            save_message(supabase, st.session_state.current_conversation['id'], "assistant", formatted, agent.value)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": formatted,
            "raw_content": raw_response,
            "agent": agent.value
        })
        st.rerun()

# ============================================================================
# MAIN
# ============================================================================
def main():
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_conversation" not in st.session_state:
        st.session_state.current_conversation = None
    
    # Initialize clients
    supabase = get_supabase_client()
    openai_client = get_openai_client()
    
    if not supabase:
        st.error("⚠️ Database connection failed. Check SUPABASE_URL and SUPABASE_KEY in secrets.")
        st.stop()
    
    if not openai_client:
        st.error("⚠️ OpenAI connection failed. Check OPENAI_API_KEY in secrets.")
        st.stop()
    
    # Show login or main app
    if not st.session_state.logged_in:
        render_login_page(supabase)
    else:
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
        render_sidebar(supabase)
        render_header()
        render_welcome()
        render_chat(openai_client, supabase)

if __name__ == "__main__":
    main()