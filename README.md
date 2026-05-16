# Connect-X 🚀

A modern social media platform built with Flask, MySQL, and vanilla HTML/CSS/JavaScript.

## ✨ Features

- **User Authentication** — Register, Login, Logout with secure password hashing
- **Posts** — Create, delete posts with text and image support (500 char limit)
- **Like & Bookmark** — Like and save posts for later
- **Comments** — Reply to posts with real-time AJAX updates
- **Repost** — Share posts with your followers
- **Follow System** — Follow/unfollow users to curate your feed
- **Feed** — Personalized feed showing posts from people you follow
- **Explore** — Discover all posts and suggested users
- **Search** — Find users and posts by keyword
- **Notifications** — Get notified for likes, comments, follows, reposts
- **Profile** — Customizable profiles with avatar, bio, location, website
- **Responsive** — Works on desktop, tablet, and mobile

## 📁 Project Structure

```
connect-x/
├── app/
│   ├── __init__.py            # App factory (Flask + extensions)
│   ├── config.py              # Configuration (DB connection, secrets)
│   ├── models.py              # SQLAlchemy models (User, Post, Comment, etc.)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py            # Login, Register, Logout
│   │   ├── main.py            # Feed, Explore, Search, Notifications
│   │   ├── posts.py           # Create, Like, Comment, Repost, Delete
│   │   └── profile.py         # Profile, Settings, Follow/Unfollow
│   ├── static/
│   │   ├── css/style.css      # Premium dark theme CSS
│   │   ├── js/app.js          # Client-side interactions (AJAX)
│   │   └── images/            # Avatars, uploads
│   └── templates/
│       ├── base.html           # Base layout with sidebar navigation
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       ├── main/
│       │   ├── landing.html
│       │   ├── feed.html
│       │   ├── explore.html
│       │   ├── search.html
│       │   ├── notifications.html
│       │   └── bookmarks.html
│       ├── posts/
│       │   └── post_card.html  # Reusable post component
│       └── profile/
│           ├── profile.html
│           ├── settings.html
│           └── followers.html
├── run.py                      # Entry point
├── requirements.txt
└── README.md
```

## 🛠️ Tech Stack

| Layer     | Technology                         |
|-----------|------------------------------------|
| Backend   | Flask (Python)                     |
| Database  | MySQL + SQLAlchemy + mysql-connector-python |
| Frontend  | HTML5, CSS3, Vanilla JavaScript    |
| Auth      | Flask-Login + Werkzeug             |

## ⚡ Setup Instructions

### 1. Install Dependencies
```bash
cd connect-x
pip install -r requirements.txt
```

### 2. Configure MySQL Database
1. Create a MySQL database:
   ```sql
   CREATE DATABASE connect_x_db;
   ```
2. Edit `app/config.py` and update the connection string:
   ```python
   SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://YOUR_USER:YOUR_PASSWORD@localhost:3306/connect_x_db'
   ```

### 3. Run the Application
```bash
python run.py
```
The app will be available at **http://localhost:5000**

## 🎨 Design

- Premium dark theme with purple-teal accent gradients
- Responsive 3-column layout (sidebar + feed + widgets)
- Smooth animations and hover effects
- AJAX-powered interactions (no page reload for likes, comments, etc.)

## 📝 Notes

- Database tables are auto-created on first run via `db.create_all()`
- Default avatar is provided — users can upload custom avatars
- Image uploads are stored in `app/static/images/uploads/`
- Dummy trending data is hardcoded in the sidebar (customize as needed)
