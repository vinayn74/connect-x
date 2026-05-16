import os
import uuid
from flask import Blueprint, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Post, Comment, Notification

posts_bp = Blueprint('posts', __name__, url_prefix='/posts')


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_image(file):
    """Save uploaded image and return filename."""
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None


@posts_bp.route('/create', methods=['POST'])
@login_required
def create_post():
    """Create a new post."""
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Post content cannot be empty.', 'error')
        return redirect(request.referrer or url_for('main.feed'))
    
    if len(content) > 500:
        flash('Post must be 500 characters or less.', 'error')
        return redirect(request.referrer or url_for('main.feed'))
    
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file.filename:
            image_url = save_image(file)
    
    post = Post(
        content=content,
        image_url=image_url,
        user_id=current_user.id
    )
    db.session.add(post)
    db.session.commit()
    
    flash('Post published!', 'success')
    return redirect(request.referrer or url_for('main.feed'))


@posts_bp.route('/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    """Toggle like on a post."""
    post = Post.query.get_or_404(post_id)
    
    if current_user.has_liked(post):
        current_user.unlike_post(post)
        liked = False
    else:
        current_user.like_post(post)
        liked = True
        # Create notification
        if post.user_id != current_user.id:
            notif = Notification(
                user_id=post.user_id,
                actor_id=current_user.id,
                action='like',
                post_id=post.id
            )
            db.session.add(notif)
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'liked': liked,
            'likes_count': post.likes_count
        })
    
    return redirect(request.referrer or url_for('main.feed'))


@posts_bp.route('/<int:post_id>/bookmark', methods=['POST'])
@login_required
def bookmark_post(post_id):
    """Toggle bookmark on a post."""
    post = Post.query.get_or_404(post_id)
    
    if current_user.has_bookmarked(post):
        current_user.unbookmark_post(post)
        bookmarked = False
    else:
        current_user.bookmark_post(post)
        bookmarked = True
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'bookmarked': bookmarked})
    
    return redirect(request.referrer or url_for('main.feed'))


@posts_bp.route('/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    """Add a comment to a post."""
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(request.referrer or url_for('main.feed'))
    
    comment = Comment(
        content=content,
        user_id=current_user.id,
        post_id=post.id
    )
    db.session.add(comment)
    
    # Create notification
    if post.user_id != current_user.id:
        notif = Notification(
            user_id=post.user_id,
            actor_id=current_user.id,
            action='comment',
            post_id=post.id
        )
        db.session.add(notif)
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': current_user.display_name,
                'username': current_user.username,
                'avatar': current_user.avatar_url,
                'created_at': comment.created_at.strftime('%b %d, %Y')
            },
            'comments_count': post.comments_count
        })
    
    flash('Comment added.', 'success')
    return redirect(request.referrer or url_for('main.feed'))


@posts_bp.route('/<int:post_id>/repost', methods=['POST'])
@login_required
def repost(post_id):
    """Repost a post."""
    original = Post.query.get_or_404(post_id)
    
    # Check if already reposted
    existing = Post.query.filter_by(
        user_id=current_user.id,
        is_repost=True,
        original_post_id=original.id
    ).first()
    
    if existing:
        db.session.delete(existing)
        reposted = False
    else:
        repost_entry = Post(
            content=original.content,
            image_url=original.image_url,
            user_id=current_user.id,
            is_repost=True,
            original_post_id=original.id
        )
        db.session.add(repost_entry)
        reposted = True
        
        # Create notification
        if original.user_id != current_user.id:
            notif = Notification(
                user_id=original.user_id,
                actor_id=current_user.id,
                action='repost',
                post_id=original.id
            )
            db.session.add(notif)
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'reposted': reposted,
            'reposts_count': original.reposts_count
        })
    
    return redirect(request.referrer or url_for('main.feed'))


@posts_bp.route('/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """Delete a post (only by author)."""
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        flash('You cannot delete this post.', 'error')
        return redirect(request.referrer or url_for('main.feed'))
    
    # Delete image file if exists
    if post.image_url:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], post.image_url)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Post deleted.', 'info')
    return redirect(request.referrer or url_for('main.feed'))


@posts_bp.route('/<int:post_id>/comments', methods=['GET'])
@login_required
def get_comments(post_id):
    """Get comments for a post (AJAX)."""
    post = Post.query.get_or_404(post_id)
    comments = post.comments.order_by(Comment.created_at.asc()).all()
    
    return jsonify({
        'comments': [{
            'id': c.id,
            'content': c.content,
            'author': c.author.display_name,
            'username': c.author.username,
            'avatar': c.author.avatar_url,
            'created_at': c.created_at.strftime('%b %d, %Y at %I:%M %p')
        } for c in comments]
    })
