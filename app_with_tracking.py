# app.py
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')  # Required for sessions

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///conversations.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Database Models
class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    messages = db.relationship('Message', backref='conversation', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()

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
    
    return render_template('index.html', messages=messages)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    conversation_id = session.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'error': 'No conversation found'}), 400
    
    try:
        # Save user message to database
        user_msg = Message(
            conversation_id=conversation_id,
            role='user',
            content=user_message
        )
        db.session.add(user_msg)
        db.session.commit()
        
        # Get conversation history for context
        conversation_messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.timestamp).all()
        
        # Prepare messages for API call
        api_messages = [{"role": "system", "content": "You are a helpful assistant."}]
        api_messages.extend([
            {"role": msg.role, "content": msg.content}
            for msg in conversation_messages
        ])
        
        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=api_messages
        )
        
        # Extract and save the assistant's response
        bot_response = response.choices[0].message.content
        bot_msg = Message(
            conversation_id=conversation_id,
            role='assistant',
            content=bot_response
        )
        db.session.add(bot_msg)
        db.session.commit()
        
        return jsonify({'response': bot_response})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/new-conversation', methods=['POST'])
def new_conversation():
    # Create new conversation
    conv = Conversation(session_id=os.urandom(24).hex())
    db.session.add(conv)
    db.session.commit()
    session['conversation_id'] = conv.id
    return jsonify({'status': 'success'})



if __name__ == '__main__':
    app.run(debug=True)
    