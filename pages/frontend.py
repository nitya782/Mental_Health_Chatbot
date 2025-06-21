import streamlit as st
import requests
import time
import logging
import sqlite3
import uuid
from datetime import datetime

# API Endpoint
API_URL = "https://mental-health-chatbot-0yvl.onrender.com/frontend"  # Update this if your backend is hosted elsewhere

# Connect to the SQLite database
conn = sqlite3.connect("chat_history.db", check_same_thread=False)
cursor = conn.cursor()

# Create table for storing chat history
cursor.execute('''CREATE TABLE IF NOT EXISTS conversations (
    chat_id TEXT,
    role TEXT,
    message TEXT
)''')
conn.commit()

# Function to store messages
def save_message(chat_id, role, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add timestamp
    cursor.execute("INSERT INTO conversations (chat_id, role, message, timestamp) VALUES (?, ?, ?, ?)", 
                   (chat_id, role, message, timestamp))
    conn.commit()

# Function to load chat history
def load_chat_history(chat_id):
    cursor.execute("SELECT role, message, timestamp FROM conversations WHERE chat_id = ? ORDER BY timestamp", (chat_id,))
    return cursor.fetchall()

# logging to store messages
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Function to fetch chat sessions with timestamps
def get_chat_sessions():
    cursor.execute("SELECT DISTINCT chat_id, MIN(timestamp) FROM conversations GROUP BY chat_id ORDER BY MIN(timestamp) DESC")
    return cursor.fetchall()

def get_all_chat_ids():
    cursor.execute("SELECT DISTINCT chat_id FROM conversations")
    return [row[0] for row in cursor.fetchall()]

chat_ids = get_all_chat_ids()

def get_chat_name(chat_id):
    messages = load_chat_history(chat_id)  # Fetch chat messages from the database
    if messages:
        first_message = messages[0][1]  # Get the first user message
        return first_message[:30]  # Truncate to 30 chars for display
    return "New Chat"

# Function to generate a chat title from the first user message
def get_chat_title(chat_id):
    cursor.execute("SELECT message FROM conversations WHERE chat_id = ? AND role = 'user' ORDER BY timestamp LIMIT 1", (chat_id,))
    first_message = cursor.fetchone()
    return first_message[0][:30] if first_message else "New Chat"

# Generate chat session names dynamically
chat_sessions = {chat_id: get_chat_name(chat_id) for chat_id in chat_ids}

# Function to fetch all chat sessions grouped by day
def get_chat_history_grouped_by_day():
    cursor.execute("""
        SELECT chat_id, MIN(timestamp)
        FROM conversations
        GROUP BY chat_id
        ORDER BY MIN(timestamp) DESC
    """)
    chat_sessions = cursor.fetchall()  # Fetch chat sessions

    # DEBUG: Print what we got from the database
    print("DEBUG: Retrieved chat_sessions ->", chat_sessions)

    # Initialize grouped_sessions dictionary
    grouped_sessions = {}

    # Iterate through chat sessions
    for row in chat_sessions:
        print("DEBUG: Row contents ->", row) 
        
        if len(row) == 2:  
            chat_id, first_message_time = row
            if first_message_time:  # Ensure timestamp exists
                date = first_message_time.split(" ")[0]  # Extract date
                grouped_sessions.setdefault(date, []).append((chat_id, first_message_time))
        else:
            print("⚠️ Unexpected number of values in row, skipping:", row)  

    return grouped_sessions  


# Fetch chat sessions properly
chat_sessions = get_chat_history_grouped_by_day()  

# Sidebar for Chat History
st.sidebar.title("📝 Chat History")

if st.sidebar.button("➕ New Chat", key="new_chat"):
    new_chat_id = str(uuid.uuid4())
    st.session_state["current_chat"] = new_chat_id
    st.sidebar.success("New chat created!")

# Display chat history grouped by date
for date, chats in chat_sessions.items(): 
    st.sidebar.markdown(f"<div class='date-header'>{date}</div>", unsafe_allow_html=True)  
    for chat_id, first_message_time in chats:
        title = get_chat_title(chat_id)  
        if st.sidebar.button(title, key=f"{chat_id}_{date}"):
            st.session_state["current_chat"] = chat_id

# chatbot avatar GIF 
col1, col2 = st.columns((0.1, 0.9)) 

with col1:
    st.image("chatbot_avatar.gif.gif", width=60) 

with col2:
    st.markdown("<h1 style='color: black;'>Calm Chatbot</h1>", unsafe_allow_html=True)


# Styling
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }

        /* Background Gradient Animation */
        @keyframes gradientAnimation {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .stApp {
            background: linear-gradient(-45deg, #d4eaf7, #e3d7ff, #f5e6cc, #d3f3e3);
            background-size: 400% 400%;
            animation: gradientAnimation 15s ease infinite;
        }
          /* Sidebar background gradient */
        [data-testid="stSidebar"] {
            background: linear-gradient(135deg, #fdfcfb, #e2d1c3, #f5e6cc, #d3f3e3);
            background-size: 400% 400%;
            animation: gradientAnimation 15s ease infinite;
        }
         /* Rounded colored New Chat button */
        div.stButton > button:first-child {
            background: linear-gradient(to right, #A18CD1, #FBC2EB);
            color: #333;
            border-radius: 30px;
            padding: 10px 25px;
            font-weight: bold;
            font-size: 15px;
            border: none;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            transition: 0.3s ease;
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(to right, #8e76bd, #ebb8dc);
            color: #000;
        }

        /* Chat history bubbles like new chat button */
        .chat-bubble {
            background: linear-gradient(to right, #f3f3f3, #eaeaea);
            color: #333;
            border-radius: 20px;
            padding: 10px 15px;
            margin: 6px 0;
            font-size: 14px;
            font-weight: 500;
            text-align: left;
            display: inline-block;
            width: 100%;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .chat-bubble:hover {
            background: linear-gradient(to right, #e0e0e0, #d9d9d9);
            transform: scale(1.02);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            filter: brightness(1.05);
        }

        /* Date header styling */
        .date-header {
            font-size: 16px;
            font-weight: bold;
            color: #444;
            margin-top: 20px;
            margin-bottom: 10px;
        }
                                                          /* Chat Bubble Styling */
       .chat-container {
              display: flex;
              width: 100%;
              margin-bottom: 10px;
         }
   
        .chat-bubble {
            max-width: 60%;
            padding: 10px 15px;
            border-radius: 20px;
            margin-bottom: 10px;
            word-wrap: break-word;
            display: inline-block;
        }
       
        .user-bubble {
            background-color: #EADCF8; /* Soft Muted Purple */
            color: black;
            align-self: flex-end;
            border-radius: 18px;
            padding: 12px 16px;
            max-width: 80%;
            border: none;
            transition: background-color 0.5s ease-in-out; /* Smooth color transition */
            text-align: left;
       }

       .bot-bubble {
            background-color: #FFEFE2; /* Lighter Soft Peach */
            color: black;
            align-self: flex-start;
            border-radius: 18px;
            padding: 12px 16px;
            max-width: 80%;
            border: none;
            transition: background-color 0.5s ease-in-out; /* Smooth color transition */
            text-align: left;
       }
                                                 /* Floating Bubbles */
        .bubble {
            position: absolute;
            background-color: rgba(255, 255, 255, 0.5); /* Increase opacity for better visibility */
            border-radius: 50%;
            opacity: 0.4; /* Make the bubbles more visible */
            animation: floatUp 12s infinite ease-in-out; /* Adjust animation duration for smoother movement */
            }
        @keyframes floatUp {
             0% { transform: translateY(100vh); opacity: 0.4; }
             50% { opacity: 0.4; } /* Make bubbles more visible mid-animation */
            100% { transform: translateY(-10vh); opacity: 0; }
        }
                                        /* Bubble Container */
        .bubble-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100vh;
            pointer-events: none;
            overflow: hidden;
        }
                                          /* Emergency Contacts */
        .emergency-contacts {
            position: fixed;
            bottom: 50px;
            right: 20px;
            font-size: 14px;
            color: #333;
            text-align: right;
            font-weight: bold;
        }
    </style>
   
    """,
    unsafe_allow_html=True
)
# Initialize session state for user input
if "user_input" not in st.session_state:
    st.session_state["user_input"] = ""
#function to send message
def send_message():
     user_input = st.session_state.get("user_input", "").strip()

     if user_input:
        chat_id = st.session_state.current_chat

        # Save user message in the database
        save_message(chat_id, "user", user_input)

        # Clear the input field
        st.session_state["user_input"] = ""

        with st.spinner("Typing..."):
            time.sleep(0.5)  #  typing delay

        try:
            response = requests.post(API_URL, json={"message": user_input})
            logging.debug("API Response: %s", response.json())

            if response.status_code == 200:
                response_data = response.json()
                bot_response = response_data.get("response", "I'm not sure how to respond.")
                bot_response = bot_response.replace("</div>", "").strip() # Sanitize bot response to prevent unintended HTML rendering
                video = response_data.get("video", {})
                video_title = video.get("title", "")
                video_url = video.get("url", "")
               # Include the video link in the bot's response if available
            if video_url:
                 bot_response += f"<br><br>🎵 <b>{video_title}</b>: <a href='{video_url}' target='_blank'>Watch on YouTube</a>"
   
               
            else:
                bot_response = f"❌ Error {response.status_code}: {response.text}"
                video_title = ""
                video_url = ""

        except Exception as e:
            bot_response = f"❌ Error: {e}"
            video_title = ""
            video_url = ""
        save_message(chat_id, "bot", bot_response)
        # Clear input box
        st.session_state.pop("user_input", None)
send_message() 
# Bubbles
def create_bubbles():
    bubble_styles = "".join(
        f'<div class="bubble" style="width:{size}px; height:{size}px; left:{left}%; animation-duration:{duration}s;"></div>'
        for size, left, duration in  [(30, 5, 10), (50, 15, 12), (40, 25, 14), (60, 35, 16), (70, 45, 18),  # Larger bubbles
            (20, 55, 8), (30, 65, 10), (40, 75, 12), (50, 85, 14), (60, 95, 16),  # More bubbles
            (25, 10, 9), (35, 20, 11), (45, 30, 13), (55, 40, 15), (65, 50, 17)   # Additional bubbles
        ]
    )
    st.markdown(f'<div class="bubble-container">{bubble_styles}</div>', unsafe_allow_html=True)

create_bubbles()

# user authentication
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("⚠️ Please log in first.")
    st.stop()
# Automatically create a new chat session after login
if "authenticated" in st.session_state and st.session_state["authenticated"]:
    if "current_chat" not in st.session_state or st.session_state["current_chat"] == "New Chat":
        # Automatically create a new chat session
        new_chat_id = str(uuid.uuid4())
        st.session_state["current_chat"] = new_chat_id
        st.sidebar.success("New chat session created automatically!")
        
st.write("Start chatting with our AI-powered assistant. Your messages are private and secure.")

# Load chat history from the database for the selected session
chat_history = load_chat_history(st.session_state.current_chat) if st.session_state.get("current_chat", "New Chat") != "New Chat" else []

# Display user and bot messages with proper alignment
def handle_user_and_bot_messages(chat_history):
  for role, msg, timestamp in chat_history:
    if role == "user":  # User message
        col1, col2 = st.columns([0.3, 0.7])  # User on the right
        with col2:
            st.markdown(
                f"""
                <div class="user-bubble">
                    <b>{datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")}</b><br>
                    {msg}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:  # Bot message
        col1, col2 = st.columns([0.7, 0.3])  # Bot on the left
        with col1:
            st.markdown(
                f"""
                <div class="bot-bubble">
                    <b>{datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")}</b><br>
                    {msg}
                </div>
                """,
                unsafe_allow_html=True
            )
# Call the function to display messages
handle_user_and_bot_messages(chat_history)

#input bar for user message
st.text_input("Type your message here...", key="user_input", on_change=send_message)

# Logout Button
if st.button("Logout"):
    st.session_state["authenticated"] = False
    st.success("Logged out successfully! Redirecting...")
    time.sleep(2)
    st.rerun()

# Emergency Contacts
st.markdown(
    '<div class="emergency-contacts">'
    'Emergency Contacts:<br>'
    'Mental Health Support: 123-456-7890<br>'
    'Suicide Prevention: 987-654-3210<br>'
    'Crisis Helpline: 555-777-9999'
    '</div>',
    unsafe_allow_html=True
)
