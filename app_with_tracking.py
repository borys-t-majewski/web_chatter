# app.py
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import openai
from dotenv import load_dotenv
import os
import dspy
from typing import List

from app_modules.extensions import db
from app_modules.database_models import Conversation, Message, SystemInstructions, clear_conversation_data, clear_conversation_data_fully
from app_modules.conversation_handlers import (
    create_new_conversation,
    handle_chat_message,
    end_current_conversation,
    change_assistant_role
)
from app_modules.chatbot import StructuredChatbot

from constants import model, temperature, max_tokens, ALLOWED_ROLES


# Load environment variables
load_dotenv()

app = Flask(__name__)
# change here to have different users - for prototype it's fixed
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///conversations.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db with app
db.init_app(app)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')
lm = dspy.LM(f'openai/{model}',temperature=temperature, max_tokens=max_tokens)


# dspy.settings.configure(lm=lm, global_instructions=under_role_system_prompt)




# Initialize DSPy chatbot
chatbot = StructuredChatbot()

def check_system_instructions():
    """Check and print the latest system instructions."""
    try:
        latest_instruction = SystemInstructions.query.order_by(SystemInstructions.timestamp.desc()).first().content
        print("Using modified instruction")
        print(latest_instruction[0:200])
        print(latest_instruction[-500:])
    except:
        print("Using default instruction")

# Create tables
with app.app_context():
    db.create_all()  # This will create tables with the new schema
    check_system_instructions()

clear_conversation_data(app)


@app.route('/')
def home():
    if 'conversation_id' not in session:
        # Create a new conversation
        conv = Conversation(session_id=os.urandom(24).hex())
        db.session.add(conv)
        db.session.commit()
        session['conversation_id'] = conv.id
    
    # Get conversation history
    messages = Message.query.filter_by(
        conversation_id=session['conversation_id']
    ).order_by(Message.timestamp).all()
    
    # Pass ALLOWED_ROLES to template
    return render_template('index.html', messages=messages, roles=ALLOWED_ROLES)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    return handle_chat_message(user_message)

@app.route('/new-conversation', methods=['POST'])
def new_conversation():
    clear_conversation_data(app)
    check_system_instructions()
    return create_new_conversation()

@app.route('/end-conversation', methods=['POST'])
def end_conversation():
    return end_current_conversation()

@app.route('/change-roles', methods=['POST'])
def change_roles():
    """Handle role change requests."""
    new_role = request.json.get('role', '')

    # if not new_role or new_role not in ALLOWED_ROLES:
    #     return jsonify({'error': 'Invalid role selected'}), 400
    
    return change_assistant_role(new_role)

@app.route('/clear-all', methods=['POST'])
def clear_all():
    """Clear all data from the database and start fresh."""
    try:
        clear_conversation_data_fully(app)
        
        # Create new conversation
        conv = Conversation(session_id=os.urandom(24).hex())
        db.session.add(conv)
        db.session.commit()
        session['conversation_id'] = conv.id
        
        # Clear any existing session data
        session.pop('awaiting_feedback', None)
        session.pop('ended_conversation_id', None)
        
        return jsonify({
            'status': 'success',
            'message': 'All data cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)