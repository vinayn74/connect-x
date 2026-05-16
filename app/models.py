from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

# ============================================================
# Association Tables
# ============================================================

# Many-to-many: User follows User
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

# Many-to-many: User likes Post
likes = db.Table('likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

# Many-to-many: User bookmarks Post
bookmarks = db.Table('bookmarks',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)


# ============================================================
# User Model
# ============================================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(500), default='default-avatar.png')
    cover_url = db.Column(db.String(500), default='default-cover.jpg')
    location = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    
    # Follow relationships
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers_list', lazy='dynamic'),
        lazy='dynamic'
    )
    
    # Liked posts
    liked_posts = db.relationship(
        'Post', secondary=likes,
        backref=db.backref('liked_by', lazy='dynamic'),
        lazy='dynamic'
    )
    
    # Bookmarked posts
    bookmarked_posts = db.relationship(
        'Post', secondary=bookmarks,
        backref=db.backref('bookmarked_by', lazy='dynamic'),
        lazy='dynamic'
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
    
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
    
    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0
    
    def like_post(self, post):
        if not self.has_liked(post):
            self.liked_posts.append(post)
    
    def unlike_post(self, post):
        if self.has_liked(post):
            self.liked_posts.remove(post)
    
    def has_liked(self, post):
        return self.liked_posts.filter(likes.c.post_id == post.id).count() > 0
    
    def bookmark_post(self, post):
        if not self.has_bookmarked(post):
            self.bookmarked_posts.append(post)
    
    def unbookmark_post(self, post):
        if self.has_bookmarked(post):
            self.bookmarked_posts.remove(post)
    
    def has_bookmarked(self, post):
        return self.bookmarked_posts.filter(bookmarks.c.post_id == post.id).count() > 0
    
    @property
    def followers_count(self):
        return self.followers_list.count()
    
    @property
    def following_count(self):
        return self.followed.count()
    
    def get_feed_posts(self):
        """Get posts from users this user follows + own posts."""
        followed_posts = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)
        ).filter(followers.c.follower_id == self.id)
        own_posts = Post.query.filter_by(user_id=self.id)
        return followed_posts.union(own_posts).order_by(Post.created_at.desc())
    
    def get_recent_conversations(self):
        """Get a list of users this user has messaged with, ordered by most recent message."""
        # Get all users we've sent messages to or received messages from
        sent_to = db.session.query(Message.receiver_id).filter_by(sender_id=self.id)
        received_from = db.session.query(Message.sender_id).filter_by(receiver_id=self.id)
        user_ids = sent_to.union(received_from).distinct().all()
        user_ids = [uid[0] for uid in user_ids]
        
        if not user_ids:
            return []
            
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        # Sort by most recent message with each user
        users.sort(key=lambda u: self.last_message_with(u).created_at if self.last_message_with(u) else datetime.min, reverse=True)
        return users

    def last_message_with(self, user):
        """Get the last message between this user and another user."""
        return Message.query.filter(
            ((Message.sender_id == self.id) & (Message.receiver_id == user.id)) |
            ((Message.sender_id == user.id) & (Message.receiver_id == self.id))
        ).order_by(Message.created_at.desc()).first()
    
    def unread_messages_from(self, user):
        """Count unread messages from a specific user."""
        return Message.query.filter_by(sender_id=user.id, receiver_id=self.id, is_read=False).count()

    def __repr__(self):
        return f'<User @{self.username}>'


# ============================================================
# Post Model
# ============================================================
class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_repost = db.Column(db.Boolean, default=False)
    original_post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    original_post = db.relationship('Post', remote_side=[id], backref='reposts')
    
    @property
    def likes_count(self):
        return self.liked_by.count()
    
    @property
    def comments_count(self):
        return self.comments.count()
    
    @property
    def reposts_count(self):
        return len(self.reposts)
    
    def __repr__(self):
        return f'<Post {self.id} by @{self.author.username}>'


# ============================================================
# Comment Model
# ============================================================
class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Comment {self.id} on Post {self.post_id}>'


# ============================================================
# Notification Model
# ============================================================
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 'like', 'comment', 'follow', 'repost'
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    actor = db.relationship('User', foreign_keys=[actor_id])
    post = db.relationship('Post', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.action} for User {self.user_id}>'
# ============================================================
# Message Model
# ============================================================
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy='dynamic'))
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_messages', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id} to {self.receiver_id}>'
