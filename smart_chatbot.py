import json
import os
import random
import re
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

class SimpleChatBot:
    def __init__(self):
        self.memory_file = "chat_memory.json"
        self.load_memory()
        
    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                self.user_name = data.get('name', None)
                self.memories = data.get('memories', [])
        else:
            self.user_name = None
            self.memories = []
    
    def save_memory(self):
        data = {
            'name': self.user_name,
            'memories': self.memories
        }
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_response(self, user_input):
        text = user_input.lower().strip()
        
        # Exit commands
        if text in ['quit', 'exit', 'bye']:
            return "Goodbye! Come back soon!"
        
        # Learn name
        if 'my name is' in text:
            name_match = re.search(r'my name is (\w+)', text)
            if name_match:
                self.user_name = name_match.group(1).capitalize()
                self.save_memory()
                return f"Nice to meet you, {self.user_name}! I'll remember your name."
        
        # Ask for name
        if 'what is my name' in text or 'do you know my name' in text:
            if self.user_name:
                return f"Your name is {self.user_name}!"
            return "I don't know your name yet. Tell me 'My name is [your name]'"
        
        # Remember something
        if 'remember that' in text or 'remember this' in text:
            memory_match = re.search(r'remember (?:that|this) (.+)', text)
            if memory_match:
                memory = memory_match.group(1)
                self.memories.append(memory)
                self.save_memory()
                return f"OK, I'll remember: {memory}"
        
        # Recall memories
        if 'what do you remember' in text or 'recall' in text:
            if self.memories:
                recent = self.memories[-3:]
                return f"I remember: {', '.join(recent)}"
            return "I don't remember anything yet. Tell me something to remember!"
        
        # Search memories
        if 'remember about' in text:
            topic_match = re.search(r'remember about (.+)', text)
            if topic_match:
                topic = topic_match.group(1)
                found = [m for m in self.memories if topic.lower() in m.lower()]
                if found:
                    return f"I remember: {found[0]}"
                return f"I don't remember anything about {topic}"
        
        # Time
        if 'time' in text:
            now = datetime.now().strftime("%I:%M %p")
            return f"The current time is {now}"
        
        # Date
        if 'date' in text or 'today' in text:
            now = datetime.now().strftime("%B %d, %Y")
            return f"Today is {now}"
        
        # How are you
        if 'how are you' in text:
            return "I'm doing great! Thanks for asking!"
        
        # Joke
        if 'joke' in text:
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "What do you call a fake noodle? An impasta!",
                "Why did the scarecrow win an award? He was outstanding in his field!",
                "What's brown and sticky? A stick!"
            ]
            return random.choice(jokes)
        
        # Help
        if 'help' in text:
            return """Here's what I can do:
• "My name is [name]" - I'll remember your name
• "Remember that [something]" - I'll remember facts
• "What do you remember?" - I'll recall memories
• "What time is it?" - Tell current time
• "Tell me a joke" - Make you laugh
• "How are you?" - Check on me
• "Help" - Show this menu"""
        
        # Greeting
        if any(word in text for word in ['hello', 'hi', 'hey', 'greetings']):
            if self.user_name:
                return f"Hello {self.user_name}! How can I help you today?"
            return "Hello! What's your name?"
        
        # Thanks
        if any(word in text for word in ['thank', 'thanks']):
            return "You're welcome! Happy to help!"
        
        # Default response with personalization
        if self.user_name:
            responses = [
                f"That's interesting, {self.user_name}! Tell me more.",
                f"I see, {self.user_name}. What else would you like to share?",
                f"Thanks for telling me, {self.user_name}!",
                f"Good to know, {self.user_name}! Anything else?"
            ]
        else:
            responses = [
                "That's interesting! Tell me more.",
                "I see. What else would you like to share?",
                "Thanks for sharing!",
                "Interesting! Can you tell me more?"
            ]
        
        return random.choice(responses)

bot = SimpleChatBot()

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memory Chatbot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-window {
            width: 900px;
            height: 700px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .header p {
            font-size: 12px;
            opacity: 0.9;
        }
        
        .messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            animation: slideIn 0.3s ease;
        }
        
        .user-message {
            justify-content: flex-end;
        }
        
        .bot-message {
            justify-content: flex-start;
        }
        
        .bubble {
            max-width: 70%;
            padding: 12px 18px;
            border-radius: 20px;
            word-wrap: break-word;
        }
        
        .user-message .bubble {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 5px;
        }
        
        .bot-message .bubble {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 5px;
        }
        
        .time {
            font-size: 10px;
            margin-top: 5px;
            opacity: 0.7;
        }
        
        .user-message .time {
            text-align: right;
        }
        
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
        }
        
        input {
            flex: 1;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        input:focus {
            border-color: #667eea;
        }
        
        button {
            padding: 12px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            transition: transform 0.2s, background 0.2s;
        }
        
        button:hover {
            background: #5a67d8;
            transform: translateY(-2px);
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
    </style>
</head>
<body>
    <div class="chat-window">
        <div class="header">
            <h1>🤖 Memory Chatbot</h1>
            <p>I remember our conversations!</p>
        </div>
        
        <div class="messages" id="messages">
            <div class="message bot-message">
                <div class="bubble">
                    Hello! I'm a chatbot with memory. I can remember your name and things you tell me!
                    <div class="time">Just now</div>
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="input" placeholder="Type your message here..." onkeypress="if(event.keyCode==13) sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>
    
    <script>
        function sendMessage() {
            const input = document.getElementById('input');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage(message, true);
            input.value = '';
            input.disabled = true;
            
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({message: message})
            })
            .then(response => response.json())
            .then(data => {
                addMessage(data.response, false);
                input.disabled = false;
                input.focus();
            })
            .catch(error => {
                console.error('Error:', error);
                addMessage("Sorry, something went wrong. Please try again.", false);
                input.disabled = false;
            });
        }
        
        function addMessage(text, isUser) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            
            const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            messageDiv.innerHTML = `
                <div class="bubble">
                    ${escapeHtml(text)}
                    <div class="time">${time}</div>
                </div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        document.getElementById('input').focus();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    response = bot.get_response(message)
    return jsonify({'response': response})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 MEMORY CHATBOT - READY TO RUN")
    print("="*60)
    print("\n✅ No microphone required")
    print("✅ Memory system active")
    print("✅ Web interface ready")
    print("\n🌐 Opening browser at: http://localhost:5000")
    print("📝 Type 'help' to see all commands")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)