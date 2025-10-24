import streamlit as st
from backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid



################Utility##############
def generate_thread_id():
    return str(uuid.uuid4())

def add_thread(thread_id):
    if 'chat_threads' not in st.session_state:
        st.session_state['chat_threads'] = []
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []
    # ✅ set placeholder title
    st.session_state['thread_titles'][thread_id] = "Started new conversation"

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])


# ----------- Initialize Session State ----------- #
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'thread_titles' not in st.session_state:
    st.session_state['thread_titles'] = {}

# Ensure current thread exists and has placeholder title
add_thread(st.session_state['thread_id'])
if st.session_state['thread_id'] not in st.session_state['thread_titles']:
    st.session_state['thread_titles'][st.session_state['thread_id']] = "Started new conversation"


# ----------- Sidebar UI ----------- #
st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    title = st.session_state['thread_titles'].get(thread_id, "🆕 Started new conversation")
    if st.sidebar.button(title, key=f"btn_{thread_id}"):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages


# ----------- Main Chat UI ----------- #
for message in st.session_state['message_history']:
    with st.chat_message(message["role"]):
        st.text(message["content"])


CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
user_input = st.chat_input("Type your message here...")

if user_input:
    st.session_state['message_history'].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)

    # ✅ Update title from placeholder if this is first message
    thread_id = st.session_state['thread_id']
    current_title = st.session_state['thread_titles'].get(thread_id, "")
    if current_title == "🆕 Started new conversation":
        title = " ".join(user_input.split()[:8])  # first 8 words
        if len(title) > 50:
            title = title[:50] + "..."
        st.session_state['thread_titles'][thread_id] = title


    with st.chat_message("assistant"):
        ai_response = ""
        placeholder = st.empty()  # create a placeholder for streaming text

        for message_chunk, metadata in chatbot.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=CONFIG,
            stream_mode="messages"
        ):
            if isinstance(message_chunk, AIMessage) and message_chunk.content:
                ai_response += message_chunk.content
                placeholder.markdown(ai_response)  # updates in real time

    # Save full assistant message at the end
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_response})
