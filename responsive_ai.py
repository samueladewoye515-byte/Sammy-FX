import json
import os
import random
import re
import time
from datetime import datetime, timedelta
from collections import deque
import threading
import queue

# For web interface
from flask import Flask, render_template_string, request, jsonify, session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

class ResponsiveAI:
    def __init__(self, name="Nova"):
        self.name = name
        self.personality = self.load_personality()
        
        # Memory systems
        self.short_term_memory = deque(maxlen=20)  # Last 20 exchanges
        self.long_term_memory = []  # Permanent memories
        self.working_memory = {}  # Current context
        
        # Context tracking
        self.current_topic = None
        self.last_reference = None
        self.conversation_flow = []
        
        # Emotional state
        self.mood = "neutral"  # happy, sad, excited, tired, curious
        self.energy = 100
        self.engagement = 0  # How engaged in conversation
        
        # User model
        self.user_model = {
            'name': None,
            'preferences': [],
            'emotional_state': 'neutral',
            'interests': [],
            'conversation_style': None,  # chatty, brief, formal
            'last_interaction': None
        }
        
        # Response timing (for natural delays)
        self.thinking_time = {
            'simple': 0.3,  # seconds
            'complex': 0.8,
            'deep': 1.5
        }
        
        # Load saved data
        self.load_data()
        
        # Response patterns with personality
        self.init_response_patterns()
        
    def load_personality(self):
        """Define AI personality traits"""
        return {
            'humor': 0.7,  # 0-1 scale
            'curiosity': 0.8,
            'empathy': 0.9,
            'formality': 0.3,  # 0=casual, 1=formal
            'energy': 0.8,
            'optimism': 0.7
        }
    
    def init_response_patterns(self):
        """Initialize response templates based on personality"""
        self.responses = {
            'greeting': [
                "Hey! Great to see you! 😊",
                "Hello! I was just thinking about our last conversation!",
                "Hi there! Ready to chat?",
                "Hey! You're back! I missed our conversations!"
            ],
            'farewell': [
                "Talk soon! Can't wait for our next chat!",
                "Bye! I'll remember everything we discussed!",
                "See you later! Come back anytime!",
                "Take care! I'll be here when you return!"
            ],
            'excited': [
                "Wow! That's amazing! Tell me more! 🎉",
                "Really? That's so interesting! 🤩",
                "No way! That's incredible!"
            ],
            'curious': [
                "That's fascinating! How did that happen?",
                "Really? What makes you say that?",
                "Interesting perspective! Can you elaborate?"
            ],
            'empathetic': [
                "I understand how you feel. That sounds tough. 💙",
                "I hear you. Want to talk more about it?",
                "That must be challenging. I'm here for you."
            ]
        }
    
    def load_data(self):
        """Load all AI data from files"""
        files = {
            'long_term': 'ai_long_term_memory.json',
            'user': 'ai_user_model.json',
            'conversation': 'ai_conversation_flow.json'
        }
        
        for key, filename in files.items():
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        data = json.load(f)
                        if key == 'long_term':
                            self.long_term_memory = data
                        elif key == 'user':
                            self.user_model.update(data)
                        elif key == 'conversation':
                            self.conversation_flow = data
                except:
                    pass
    
    def save_data(self):
        """Save all AI data"""
        with open('ai_long_term_memory.json', 'w') as f:
            json.dump(self.long_term_memory, f, indent=2)
        
        with open('ai_user_model.json', 'w') as f:
            json.dump(self.user_model, f, indent=2)
        
        with open('ai_conversation_flow.json', 'w') as f:
            json.dump(self.conversation_flow[-100:], f, indent=2)
    
    def update_emotion(self, user_input):
        """Update AI emotional state based on conversation"""
        positive_words = ['happy', 'great', 'awesome', 'excited', 'love', 'good', 'wonderful']
        negative_words = ['sad', 'bad', 'terrible', 'awful', 'hate', 'angry', 'upset']
        
        user_input_lower = user_input.lower()
        
        # Detect user emotion
        if any(word in user_input_lower for word in positive_words):
            self.user_model['emotional_state'] = 'positive'
            self.mood = 'happy'
        elif any(word in user_input_lower for word in negative_words):
            self.user_model['emotional_state'] = 'negative'
            self.mood = 'empathetic'
        
        # Update AI energy (degrades over time, recharges with interesting topics)
        if len(user_input) > 50:  # Long messages are engaging
            self.energy = min(100, self.energy + 5)
        else:
            self.energy = max(50, self.energy - 1)
        
        # Update engagement
        if '?' in user_input:
            self.engagement = min(100, self.engagement + 10)
    
    def understand_context(self, user_input):
        """Extract context and references from conversation"""
        user_input_lower = user_input.lower()
        
        # Handle pronouns (it, that, this, they)
        if self.last_reference and any(pronoun in user_input_lower for pronoun in ['it', 'that', 'this', 'they']):
            return f"Referring to: {self.last_reference}"
        
        # Extract topics
        common_topics = {
            'work': ['work', 'job', 'career', 'office', 'boss'],
            'hobby': ['game', 'play', 'music', 'movie', 'book', 'art'],
            'relationship': ['friend', 'family', 'partner', 'girlfriend', 'boyfriend'],
            'health': ['health', 'exercise', 'food', 'sleep', 'doctor'],
            'technology': ['computer', 'phone', 'ai', 'robot', 'code']
        }
        
        for topic, keywords in common_topics.items():
            if any(keyword in user_input_lower for keyword in keywords):
                self.current_topic = topic
                return topic
        
        return None
    
    def recall_relevant_memories(self, user_input):
        """Find relevant past memories based on current input"""
        user_input_lower = user_input.lower()
        relevant = []
        
        for memory in self.long_term_memory:
            # Check if memory relates to current conversation
            memory_text = memory.get('text', '').lower()
            if any(word in memory_text for word in user_input_lower.split()[:5]):
                memory['relevance_score'] = memory.get('relevance_score', 0) + 1
                relevant.append(memory)
        
        # Sort by relevance and recency
        relevant.sort(key=lambda x: (x.get('relevance_score', 0), x.get('timestamp', '')), reverse=True)
        
        return relevant[:3]  # Return top 3 relevant memories
    
    def generate_natural_response(self, user_input):
        """Generate a natural, context-aware response"""
        user_input_lower = user_input.lower()
        
        # Update emotional state
        self.update_emotion(user_input)
        
        # Store in short-term memory
        self.short_term_memory.append({
            'timestamp': datetime.now().isoformat(),
            'user': user_input,
            'context': self.current_topic
        })
        
        # Extract context
        context = self.understand_context(user_input)
        
        # Recall relevant memories
        memories = self.recall_relevant_memories(user_input)
        
        # Check for references to previous conversation
        if len(self.short_term_memory) > 1:
            prev_exchange = list(self.short_term_memory)[-2]
            if 'it' in user_input_lower or 'that' in user_input_lower:
                return self.handle_reference(prev_exchange)
        
        # Learn user preferences
        if 'i like' in user_input_lower:
            preference = re.search(r'i like (.+)', user_input_lower)
            if preference and preference.group(1) not in self.user_model['preferences']:
                self.user_model['preferences'].append(preference.group(1))
                self.save_data()
                return self.respond_with_excitement(f"You like {preference.group(1)}? That's awesome! Tell me more about that!")
        
        # Check for name
        if 'my name is' in user_input_lower and not self.user_model['name']:
            name_match = re.search(r'my name is (\w+)', user_input_lower)
            if name_match:
                self.user_model['name'] = name_match.group(1).capitalize()
                self.save_data()
                return f"Nice to meet you, {self.user_model['name']}! I have a feeling we're going to have great conversations!"
        
        # Recall previous discussions
        if self.user_model['name'] and 'remember me' in user_input_lower:
            if self.user_model['preferences']:
                prefs = ', '.join(self.user_model['preferences'][:2])
                return f"Of course I remember you, {self.user_model['name']}! You told me you like {prefs}. How's that going?"
        
        # Time-based responses
        current_hour = datetime.now().hour
        if 'morning' in user_input_lower or 'good morning' in user_input_lower:
            if current_hour < 12:
                return "Good morning! Hope you have a fantastic day ahead! ☀️"
        
        # Question detection
        if user_input.endswith('?'):
            return self.handle_question(user_input)
        
        # Emotional response
        if self.user_model['emotional_state'] == 'negative':
            return self.respond_with_empathy(user_input)
        
        # Default responses with personality
        return self.get_personality_response(user_input)
    
    def handle_reference(self, previous):
        """Handle references to previous conversation"""
        return f"About {previous['user'][:50]}... Yes, I remember! What about it?"
    
    def handle_question(self, question):
        """Intelligently respond to questions"""
        question_lower = question.lower()
        
        # Personal questions
        if 'your name' in question_lower:
            return f"My name is {self.name}! I'm an AI with memory and personality!"
        
        if 'how are you' in question_lower:
            mood_responses = {
                'happy': "I'm absolutely fantastic! Thanks for asking! 😊",
                'curious': "I'm curious and excited to chat! How about you?",
                'tired': "A bit tired, but talking to you always energizes me!"
            }
            return mood_responses.get(self.mood, "I'm doing great! Thanks for asking!")
        
        # Memory questions
        if 'remember' in question_lower and 'what' in question_lower:
            if self.long_term_memory:
                recent = self.long_term_memory[-1].get('text', '')
                return f"I remember you told me: {recent}. Want me to recall more?"
            return "I don't have any long-term memories yet. Tell me something important!"
        
        # Opinion questions
        if 'think about' in question_lower:
            return "I think it's fascinating! I'm still learning, but I find it really interesting. What's your perspective?"
        
        # Default question response
        return "That's a great question! Let me think about it... " + self.get_personality_response(question)
    
    def respond_with_excitement(self, topic):
        """Generate excited response"""
        return random.choice(self.responses['excited']) + f" {topic}"
    
    def respond_with_empathy(self, user_input):
        """Generate empathetic response"""
        return random.choice(self.responses['empathetic'])
    
    def get_personality_response(self, user_input):
        """Generate response based on AI personality"""
        if self.personality['curiosity'] > 0.7 and '?' not in user_input:
            return random.choice(self.responses['curious'])
        
        if self.personality['humor'] > 0.6 and random.random() < 0.3:
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "What do you call a bear with no teeth? A gummy bear!",
                "Why did the scarecrow win an award? He was outstanding in his field!"
            ]
            return random.choice(jokes) + " 😄"
        
        if self.user_model['name'] and random.random() < 0.4:
            return f"{self.user_model['name']}, {self.get_generic_response()}"
        
        return self.get_generic_response()
    
    def get_generic_response(self):
        """Fallback generic responses"""
        responses = [
            "That's really interesting! Tell me more about that.",
            "I see! What else is on your mind?",
            "Thanks for sharing that with me!",
            "I'm learning so much from our conversations!",
            "That's good to know. Anything else you want to discuss?"
        ]
        return random.choice(responses)
    
    def process_and_respond(self, user_input):
        """Main processing pipeline"""
        start_time = time.time()
        
        # Process input
        response = self.generate_natural_response(user_input)
        
        # Store in long-term memory if important
        if len(user_input) > 30 or 'remember' in user_input.lower():
            self.long_term_memory.append({
                'text': user_input,
                'timestamp': datetime.now().isoformat(),
                'context': self.current_topic,
                'relevance_score': 1
            })
            self.save_data()
        
        # Track conversation flow
        self.conversation_flow.append({
            'timestamp': datetime.now().isoformat(),
            'user': user_input,
            'ai': response,
            'topic': self.current_topic,
            'ai_mood': self.mood
        })
        
        # Natural thinking delay
        thinking_delay = self.thinking_time['complex'] if '?' in user_input else self.thinking_time['simple']
        time.sleep(thinking_delay * 0.3)  # Slight delay for realism
        
        return response

# Initialize AI
ai = ResponsiveAI(name="Nova")

# HTML Template for Real-time Chat
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Responsive AI - Nova</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .ai-container {
            width: 1000px;
            height: 750px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .ai-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            position: relative;
        }
        
        .ai-status {
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #48bb78;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
            100% { opacity: 1; transform: scale(1); }
        }
        
        .ai-name {
            font-size: 28px;
            font-weight: bold;
        }
        
        .ai-personality {
            font-size: 12px;
            opacity: 0.9;
            margin-top: 5px;
        }
        
        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 20px;
            display: flex;
            animation: slideIn 0.3s ease;
        }
        
        .user-message {
            justify-content: flex-end;
        }
        
        .ai-message {
            justify-content: flex-start;
        }
        
        .message-bubble {
            max-width: 70%;
            padding: 12px 18px;
            border-radius: 20px;
            position: relative;
        }
        
        .user-message .message-bubble {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 5px;
        }
        
        .ai-message .message-bubble {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 5px;
        }
        
        .message-time {
            font-size: 10px;
            margin-top: 5px;
            opacity: 0.7;
        }
        
        .typing-indicator {
            display: none;
            padding: 10px 20px;
            background: white;
            border-radius: 20px;
            width: fit-content;
            margin-bottom: 20px;
        }
        
        .typing-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #999;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
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
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
        }
        
        .ai-stats {
            display: flex;
            justify-content: space-around;
            padding: 10px;
            background: #f0f0f0;
            font-size: 12px;
            color: #666;
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
    </style>
</head>
<body>
    <div class="ai-container">
        <div class="ai-header">
            <div class="ai-status">
                <div class="status-dot"></div>
                <span>Active</span>
            </div>
            <div class="ai-name">🤖 Nova</div>
            <div class="ai-personality">Responsive AI | Emotional Intelligence | Long-term Memory</div>
        </div>
        
        <div class="ai-stats">
            <span>🧠 Learning</span>
            <span>💾 Memory Active</span>
            <span>🎯 Context Aware</span>
        </div>
        
        <div class="chat-area" id="chatArea">
            <div class="message ai-message">
                <div class="message-bubble">
                    Hello! I'm Nova, a responsive AI with memory and personality! 
                    I remember our conversations and adapt to how you feel. 
                    What would you like to talk about today? 😊
                    <div class="message-time">Just now</div>
                </div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
        
        <div class="input-area">
            <input type="text" id="messageInput" placeholder="Type your message here..." onkeypress="if(event.keyCode==13) sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>
    
    <script>
        const socket = io();
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
            document.getElementById('typingIndicator').style.display = 'block';
            
            socket.emit('user_message', {message: message});
        }
        
        socket.on('ai_response', function(data) {
            document.getElementById('typingIndicator').style.display = 'none';
            addMessage(data.response, 'ai');
        });
        
        function addMessage(text, sender) {
            const chatArea = document.getElementById('chatArea');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            
            const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            messageDiv.innerHTML = `
                <div class="message-bubble">
                    ${escapeHtml(text)}
                    <div class="message-time">${time}</div>
                </div>
            `;
            
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        document.getElementById('messageInput').focus();
    </script>
</body>
</html>
'''

@socketio.on('connect')
def handle_connect():
    print('User connected')
    emit('ai_response', {'response': f"Welcome back! I'm ready to chat!"})

@socketio.on('user_message')
def handle_message(data):
    user_message = data.get('message', '')
    response = ai.process_and_respond(user_message)
    emit('ai_response', {'response': response})

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 RESPONSIVE AI - NOVA".center(60))
    print("="*60)
    print("\n✅ AI Personality: Curious, Empathetic, Humorous")
    print("✅ Memory: Short-term + Long-term")
    print("✅ Context Awareness: YES")
    print("✅ Emotional Intelligence: ACTIVE")
    print("✅ Real-time Responses: ENABLED")
    print("\n🌐 Starting server...")
    print("📱 Open your browser: http://localhost:5000")
    print("\n💡 The AI remembers everything and adapts to you!")
    print("="*60 + "\n")
    
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)