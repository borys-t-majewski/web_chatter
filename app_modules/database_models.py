from datetime import datetime
from app_modules.extensions import db

# Database Models
class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    messages = db.relationship('Message', backref='conversation', lazy=True)
    current_role = db.Column(db.Text, nullable=True, default=None)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class UserFeedback(db.Model):
    """Store user feedback after conversations."""
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class SystemInstructions(db.Model):
    """Store system instructions for the AI assistant."""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# if this is empty, it will use text system instruction, otherwise it will use this one!
def clear_conversation_data(app):
    with app.app_context():
        try:
            # Save UserFeedback data
            feedback_data = [
                {
                    'conversation_id': f.conversation_id,
                    'feedback': f.feedback,
                    'timestamp': f.timestamp
                } 
                for f in UserFeedback.query.all()
            ]
            
            # Save SystemInstructions data
            instructions_data = [
                {
                    'content': i.content,
                    'timestamp': i.timestamp
                }
                for i in SystemInstructions.query.all()
            ]
            
            # Drop all tables
            db.drop_all()
            
            # Recreate tables
            db.create_all()
            
            # Restore UserFeedback data
            for data in feedback_data:
                feedback = UserFeedback(**data)
                db.session.add(feedback)
            
            # Restore SystemInstructions data
            for data in instructions_data:
                instruction = SystemInstructions(**data)
                db.session.add(instruction)
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing data: {str(e)}")


def clear_conversation_data_fully(app):
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            
            db.create_all()
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing data: {str(e)}")