from typing import Dict, List, Optional
from flask import session, jsonify
import os
from datetime import datetime

from .extensions import db
from .database_models import Conversation, Message, UserFeedback, SystemInstructions
from .chatbot import chatbot, under_role_system_prompt  # We'll create this next
from constants import ALLOWED_ROLES  # Import at the top of the file

def create_new_conversation() -> Dict:
    """Create a new conversation and store it in the database.
    
    Returns:
        Dict: Response with status and any error messages
    """
    try:
        # Clean up old conversation data if it exists
        if session.get('ended_conversation_id'):
            old_messages = Message.query.filter_by(
                conversation_id=session['ended_conversation_id']
            ).delete()
            
            old_conversation = Conversation.query.filter_by(
                id=session['ended_conversation_id']
            ).delete()
        
        # Create new conversation
        conv = Conversation(session_id=os.urandom(24).hex())
        db.session.add(conv)
        db.session.commit()
        session['conversation_id'] = conv.id
        
        # Clear feedback-related session variables
        session.pop('awaiting_feedback', None)
        session.pop('ended_conversation_id', None)
        
        # Add system message about new conversation
        system_msg = Message(
            conversation_id=conv.id,
            role='system',
            content='Thank you for your feedback! Starting new conversation. Please select a role for the assistant.'
        )
        db.session.add(system_msg)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'response': 'Thank you for your feedback! Starting new conversation...',
            'new_conversation': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def handle_chat_message(user_message: str) -> Dict:
    """Process a chat message and generate a response.
    
    Args:
        user_message: The message sent by the user
        
    Returns:
        Dict: Response containing the bot's reply or error message
    """
    # Add role check at the start
    conversation_id = session.get('conversation_id')
    if not conversation_id:
        return jsonify({'error': 'No conversation found'}), 400
        
    # Get conversation and check for role
    conversation = Conversation.query.get(conversation_id)
    if not conversation or not conversation.current_role:
        return jsonify({
            'error': 'Please select a role before starting the conversation',
            'needs_role': True
        }), 400

    # Check if we're awaiting feedback
    if session.get('awaiting_feedback'):
        try:
            # Store feedback in variable
            user_feedback = user_message
            
            # Store feedback in database
            feedback = UserFeedback(
                conversation_id=session['ended_conversation_id'],
                feedback=user_feedback
            )

            db.session.add(feedback)
            db.session.commit()
            
            feedback_system_prompt = chatbot.feedback_system_prompt(starting_system_prompt=under_role_system_prompt, feedback=user_feedback)


            extra_system_push = SystemInstructions(
                content=feedback_system_prompt
            )
            
            db.session.add(extra_system_push)
            db.session.commit()


            # Create new conversation
            return create_new_conversation()
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    try:
        # Get conversation history
        conversation_messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.timestamp).all()
        
        # Prepare context for DSPy
        context_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation_messages[:-1]
        ]
        
        # Generate response based on whether there's a custom role
        # Add null check for current_role
        try:
            latest_feedbacks = ' '.join([f.feedback for f in UserFeedback.query.order_by(UserFeedback.timestamp.desc()).all()])
        except:
            latest_feedbacks = ''
        print("FEEDBACKS: ", latest_feedbacks)
        
        if conversation and conversation.current_role:
            bot_response = chatbot.respond_in_role(context_messages, user_message, conversation.current_role, feedback=latest_feedbacks)
        else:
            bot_response = chatbot(context_messages, user_message)

        bot_msg = Message(
            conversation_id=conversation_id,
            role='assistant',
            content=bot_response
        )
        db.session.add(bot_msg)
        db.session.commit()

        suspicion = chatbot.assess_suspicion(context_messages)
        print(f'Suspicion: {suspicion}')

        return jsonify({'response': bot_response})
    
    except Exception as e:
        print(f"Error in handle_chat_message: {str(e)}")  # Add logging
        return jsonify({'error': str(e)}), 500

def end_current_conversation() -> Dict:
    """End the current conversation and generate a summary.
    
    Returns:
        Dict: Response containing the conversation summary or error message
    """
    conversation_id = session.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'error': 'No conversation found'}), 400
    
    try:
        # Get conversation messages
        messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.timestamp).all()
        
        conversation_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Generate summary
        summary = chatbot.generate_summary(conversation_messages)

        print(summary)


        # Save summary
        summary_msg = Message(
            conversation_id=conversation_id,
            role='assistant',
            content=f"Conversation Summary: {summary}"
        )
        db.session.add(summary_msg)
        db.session.commit()
        
        # Set session state to await feedback
        session['awaiting_feedback'] = True
        session['ended_conversation_id'] = conversation_id
        
        return jsonify({
            'status': 'success', 
            'summary': summary,
            'awaiting_feedback': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def change_assistant_role(role: str) -> Dict:
    """Update the assistant's role for the current conversation.
    
    Args:
        role: The new role for the assistant
        
    Returns:
        Dict: Response with status and any error messages
    """
    conversation_id = session.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'error': 'No conversation found'}), 400
    
    if not role or role not in ALLOWED_ROLES:
        return jsonify({'error': 'Invalid role selected'}), 400
        
    try:
        conversation = Conversation.query.get(conversation_id)
        conversation.current_role = role
        db.session.commit()
        
        # Add a system message about the role change
        system_msg = Message(
            conversation_id=conversation_id,
            role='system',
            content=f'Assistant role set to: {role}'
        )
        db.session.add(system_msg)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Assistant will now act as: {role}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500