# Import các package cần sử dụng
import os
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
import time
import requests
from datetime import datetime

# Load API key từ file .env
load_dotenv('.env', override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')
google_script_url = os.getenv('GOOGLE_SCRIPT_URL')  # URL của Google Apps Script Web App
client = OpenAI(api_key = openai_api_key)

# Thiết lập page config
st.set_page_config(
    page_title="Chat with AI Assistant",
    page_icon="🤖",
    layout="centered"
)

# Khởi tạo session state để lưu lịch sử chat
if 'messages' not in st.session_state:
    st.session_state.messages = []

def get_limited_history(messages, limit=10):
    """
    Hàm giới hạn lịch sử chat với số lượng tin nhắn tối đa
    Args:
        messages: Lịch sử chat hiện tại
        limit: Số lượng tin nhắn tối đa muốn giữ lại
    Returns:
        Danh sách tin nhắn đã được giới hạn
    """
    return messages[-limit:] if len(messages) > limit else messages

def save_to_sheets(timestamp, question, answer):
    """
    Hàm ghi dữ liệu vào Google Sheets thông qua Apps Script
    Args:
        timestamp: Thời gian ghi nhận
        question: Câu hỏi của người dùng
        answer: Câu trả lời của AI
    Returns:
        Boolean: True nếu ghi thành công, False nếu có lỗi
    """
    try:
        # Chuẩn bị dữ liệu để gửi
        data = {
            'timestamp': timestamp,
            'question': question,
            'answer': answer
        }
        
        # Gửi POST request đến Google Apps Script
        response = requests.post(google_script_url, json=data)
        
        # Kiểm tra response
        if response.status_code == 200:
            return True
        return False
    except Exception as e:
        print(f"Lỗi khi ghi vào Google Sheets: {str(e)}")
        return False

def chat_with_llm(message):
    """
    Hàm xử lý tin nhắn từ người dùng và trả về câu trả lời từ OpenAI
    Args:
        message: Tin nhắn từ người dùng
    Returns:
        Câu trả lời từ OpenAI
    """
    if not message.strip():  # Kiểm tra nếu tin nhắn rỗng
        return None
        
    # Tạo danh sách messages bao gồm system message và lịch sử chat
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant that provides clear and concise answers."
        }
    ]
    
    # Lấy lịch sử chat đã được giới hạn và thêm vào messages
    for msg in get_limited_history(st.session_state.messages):
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Thêm tin nhắn hiện tại của người dùng
    messages.append({"role": "user", "content": message})
    
    try:
        # Gọi API OpenAI để lấy response
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
        )
        
        response = completion.choices[0].message.content
        
        # Lưu vào Google Sheets
        timestamp = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
        save_to_sheets(timestamp, message, response)
        
        return response
        
    except Exception as e:
        return f"Có lỗi xảy ra: {str(e)}"

def main():
    """
    Hàm chính để tạo giao diện Streamlit
    """
    # Thiết lập tiêu đề và mô tả cho ứng dụng
    st.title("Chat with AI Assistant")
    st.write("Hãy đặt câu hỏi, AI sẽ trả lời bạn!")

    # Hiển thị lịch sử chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Tạo chat input
    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        # Thêm tin nhắn người dùng vào lịch sử
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Hiển thị tin nhắn người dùng
        with st.chat_message("user"):
            st.markdown(prompt)

        # Hiển thị đang xử lý
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤔 Đang suy nghĩ...")
            
            # Lấy câu trả lời từ AI
            response = chat_with_llm(prompt)
            
            # Cập nhật placeholder với câu trả lời
            message_placeholder.markdown(response)
        
        # Thêm câu trả lời vào lịch sử
        st.session_state.messages.append({"role": "assistant", "content": response})

# CSS để tùy chỉnh giao diện
st.markdown("""
    <style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    </style>
""", unsafe_allow_html=True)

# Chạy ứng dụng
if __name__ == "__main__":
    main()