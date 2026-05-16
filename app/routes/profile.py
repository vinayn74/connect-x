import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Post, Notification

profile_bp = Blueprint('profile', __name__)


def save_avatar(file):
    """Save avatar image and return filename."""
    allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if file and '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext in allowed:
            filename = f"avatar_{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return filename
    return None


@profile_bp.route('/user/<username>')
@login_required
def view_profile(username):
    """View a user's profile."""
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    tab = request.args.get('tab', 'posts')
    
    if tab == 'likes':
        posts = user.liked_posts.order_by(Post.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
    elif tab == 'media':
        posts = user.posts.filter(Post.image_url.isnot(None)).order_by(
            Post.created_at.desc()
        ).paginate(page=page, per_page=10, error_out=False)
    else:
        posts = user.posts.order_by(Post.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
    
    return render_template('profile/profile.html', user=user, posts=posts, tab=tab)


@profile_bp.route('/user/<username>/followers')
@login_required
def followers(username):
    """View user's followers."""
    user = User.query.filter_by(username=username).first_or_404()
    followers_list = user.followers_list.all()
    return render_template('profile/followers.html', user=user, followers=followers_list, title='Followers')


@profile_bp.route('/user/<username>/following')
@login_required
def following(username):
    """View users the user is following."""
    user = User.query.filter_by(username=username).first_or_404()
    following_list = user.followed.all()
    return render_template('profile/followers.html', user=user, followers=following_list, title='Following')


@profile_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Edit profile settings."""
    if request.method == 'POST':
        display_name = request.form.get('display_name', '').strip()
        bio = request.form.get('bio', '').strip()
        location = request.form.get('location', '').strip()
        website = request.form.get('website', '').strip()
        
        current_user.display_name = display_name or current_user.username
        current_user.bio = bio
        current_user.location = location
        current_user.website = website
        
        # Handle avatar upload
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file.filename:
                filename = save_avatar(file)
                if filename:
                    current_user.avatar_url = filename
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.view_profile', username=current_user.username))
    
    return render_template('profile/settings.html')


@profile_bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    """Follow a user."""
    user = User.query.filter_by(username=username).first_or_404()
    
    if user.id == current_user.id:
        flash('You cannot follow yourself.', 'error')
        return redirect(url_for('profile.view_profile', username=username))
    
    if current_user.is_following(user):
        current_user.unfollow(user)
        following_status = False
    else:
        current_user.follow(user)
        following_status = True
        # Create notification
        notif = Notification(
            user_id=user.id,
            actor_id=current_user.id,
            action='follow'
        )
        db.session.add(notif)
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'following': following_status,
            'followers_count': user.followers_count
        })
    
    return redirect(url_for('profile.view_profile', username=username))
