from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import Post, User, Notification
from app import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page - redirect to feed if authenticated."""
    if current_user.is_authenticated:
        return feed()
    return render_template('main/landing.html')


@main_bp.route('/feed')
@login_required
def feed():
    """Show the main feed with posts from followed users."""
    page = request.args.get('page', 1, type=int)
    posts = current_user.get_feed_posts().paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('main/feed.html', posts=posts)


@main_bp.route('/explore')
@login_required
def explore():
    """Show explore page with trending posts."""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    # Suggest users to follow
    suggested_users = User.query.filter(
        User.id != current_user.id
    ).order_by(db.func.random()).limit(5).all()
    
    return render_template('main/explore.html', posts=posts, suggested_users=suggested_users)


@main_bp.route('/search')
@login_required
def search():
    """Search for users and posts."""
    query = request.args.get('q', '').strip()
    tab = request.args.get('tab', 'users')
    
    users = []
    posts = []
    
    if query:
        if tab == 'users':
            users = User.query.filter(
                (User.username.ilike(f'%{query}%')) |
                (User.display_name.ilike(f'%{query}%'))
            ).limit(20).all()
        else:
            posts = Post.query.filter(
                Post.content.ilike(f'%{query}%')
            ).order_by(Post.created_at.desc()).limit(20).all()
    
    return render_template('main/search.html', query=query, tab=tab, users=users, posts=posts)


@main_bp.route('/notifications')
@login_required
def notifications():
    """Show user notifications."""
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).limit(50).all()
    
    # Mark as read
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return render_template('main/notifications.html', notifications=notifs)


@main_bp.route('/bookmarks')
@login_required
def bookmarks_page():
    """Show bookmarked posts."""
    page = request.args.get('page', 1, type=int)
    posts = current_user.bookmarked_posts.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('main/bookmarks.html', posts=posts)


@main_bp.route('/api/unread-notifications')
@login_required
def unread_notifications_count():
    """API endpoint for unread notification count."""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})
