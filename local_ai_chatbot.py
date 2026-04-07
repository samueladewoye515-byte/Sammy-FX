import ollama
import json
import os
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

class LocalAI:
    def __init__(self):
        self.conversation_history = []
        self.load_history()
    
    def load_history(self):
        if os.path.exists('local_chat_history.json'):
            with open('local_chat_history.json', 'r') as f:
                self.conversation_history = json.load(f)
    
    def save_history(self):
        with open('local_chat_history.json', 'w') as f:
            json.dump(self.conversation_history[-50:], f, indent=2)
    
    def chat(self, user_message):
        # Build conversation context
        messages = []
        
        # System prompt
        messages.append({
            'role': 'system',
            'content': 'You are uzi, a helpful AI assistant. Be conversational, friendly, and helpful.'
        })
        
        # Add conversation history
        messages.extend(self.conversation_history[-20:])
        
        # Add user message
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        try:
            # Get response from local AI
            response = ollama.chat(model='llama2', messages=messages)
            ai_response = response['message']['content']
            
            # Save to history
            self.conversation_history.append({'role': 'user', 'content': user_message})
            self.conversation_history.append({'role': 'assistant', 'content': ai_response})
            self.save_history()
            
            return ai_response
            
        except Exception as e:
            return f"Error: {str(e)}. Make sure Ollama is running (run 'ollama serve' in terminal)"

# Same HTML template as above
HTML_TEMPLATE = '''(Same HTML as previous version)'''

ai = LocalAI()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    response = ai.chat(message)
    return jsonify({'response': response})

if __name__ == '__main__':
    print("\nStarting Local AI Chatbot...")
    print("Make sure Ollama is running!")
    app.run(debug=True, port=5000)