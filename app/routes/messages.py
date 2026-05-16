from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app.models import User, Message
from app import db
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/messages')
@login_required
def index():
    """Show list of recent conversations."""
    conversations = current_user.get_recent_conversations()
    return render_template('messages/inbox.html', conversations=conversations)

@messages_bp.route('/messages/<username>')
@login_required
def chat(username):
    """Show chat with a specific user."""
    other_user = User.query.filter_by(username=username).first_or_404()
    if other_user == current_user:
        abort(400, "You cannot message yourself.")
    
    # Get all messages between current_user and other_user
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user.id)) |
        ((Message.sender_id == other_user.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    
    # Mark received messages as read
    Message.query.filter_by(sender_id=other_user.id, receiver_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return render_template('messages/chat.html', other_user=other_user, messages=messages)

@messages_bp.route('/api/messages/send', methods=['POST'])
@login_required
def send_message():
    """API endpoint to send a message."""
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()
    
    if not receiver_id or not content:
        return jsonify({'error': 'Invalid data'}), 400
    
    receiver = User.query.get_or_404(receiver_id)
    if receiver == current_user:
        return jsonify({'error': 'Cannot message self'}), 400
    
    message = Message(sender_id=current_user.id, receiver_id=receiver.id, content=content)
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': {
            'id': message.id,
            'content': message.content,
            'created_at': message.created_at.strftime('%I:%M %p'),
            'is_mine': True
        }
    })

@messages_bp.route('/api/messages/unread-count')
@login_required
def unread_count():
    """API endpoint for unread message count."""
    count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})
