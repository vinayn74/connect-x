// ============================================
// Connect-X — Main JavaScript
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initComposer();
    initPostActions();
    initComments();
    initFollowButtons();
    initNotificationPolling();
    initMessagePolling();
    initImagePreview();
});

// ---- Post Composer ----
function initComposer() {
    const textarea = document.querySelector('.composer textarea');
    const charCount = document.querySelector('.char-count');
    if (!textarea || !charCount) return;

    textarea.addEventListener('input', () => {
        const len = textarea.value.length;
        charCount.textContent = `${len}/500`;
        charCount.className = 'char-count' + (len > 450 ? (len > 500 ? ' danger' : ' warn') : '');
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    });
}

// ---- Like / Bookmark / Repost ----
function initPostActions() {
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const postId = btn.dataset.postId;
            const res = await fetch(`/posts/${postId}/like`, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await res.json();
            const icon = btn.querySelector('.icon');
            const count = btn.querySelector('.count');
            btn.classList.toggle('liked', data.liked);
            icon.textContent = data.liked ? '❤️' : '🤍';
            count.textContent = data.likes_count || '';
            if (data.liked) btn.classList.add('like-anim');
            setTimeout(() => btn.classList.remove('like-anim'), 300);
        });
    });

    document.querySelectorAll('.bookmark-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const postId = btn.dataset.postId;
            const res = await fetch(`/posts/${postId}/bookmark`, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await res.json();
            const icon = btn.querySelector('.icon');
            btn.classList.toggle('bookmarked', data.bookmarked);
            icon.textContent = data.bookmarked ? '🔖' : '🏷️';
        });
    });

    document.querySelectorAll('.repost-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const postId = btn.dataset.postId;
            const res = await fetch(`/posts/${postId}/repost`, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await res.json();
            const count = btn.querySelector('.count');
            btn.classList.toggle('reposted', data.reposted);
            count.textContent = data.reposts_count || '';
        });
    });
}

// ---- Comments ----
function initComments() {
    document.querySelectorAll('.comment-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const postId = btn.dataset.postId;
            const section = document.querySelector(`.comments-section[data-post-id="${postId}"]`);
            if (!section) return;

            section.classList.toggle('open');
            if (section.classList.contains('open') && !section.dataset.loaded) {
                loadComments(postId, section);
            }
        });
    });

    document.querySelectorAll('.comment-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const postId = form.dataset.postId;
            const input = form.querySelector('input');
            const content = input.value.trim();
            if (!content) return;

            const formData = new FormData();
            formData.append('content', content);

            const res = await fetch(`/posts/${postId}/comment`, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                const list = form.previousElementSibling;
                const c = data.comment;
                const avatarSrc = c.avatar === 'default-avatar.png'
                    ? '/static/images/default-avatar.png'
                    : `/static/images/uploads/${c.avatar}`;
                list.innerHTML += `
                    <div class="comment-item">
                        <img src="${avatarSrc}" alt="">
                        <div class="comment-body">
                            <span class="name">${c.author}</span>
                            <span class="handle">@${c.username}</span>
                            <p>${c.content}</p>
                        </div>
                    </div>`;
                input.value = '';
                const countEl = document.querySelector(`.comment-btn[data-post-id="${postId}"] .count`);
                if (countEl) countEl.textContent = data.comments_count;
            }
        });
    });
}

async function loadComments(postId, section) {
    const res = await fetch(`/posts/${postId}/comments`);
    const data = await res.json();
    const list = section.querySelector('.comments-list');
    list.innerHTML = '';
    data.comments.forEach(c => {
        const avatarSrc = c.avatar === 'default-avatar.png'
            ? '/static/images/default-avatar.png'
            : `/static/images/uploads/${c.avatar}`;
        list.innerHTML += `
            <div class="comment-item">
                <img src="${avatarSrc}" alt="">
                <div class="comment-body">
                    <span class="name">${c.author}</span>
                    <span class="handle">@${c.username}</span>
                    <p>${c.content}</p>
                </div>
            </div>`;
    });
    section.dataset.loaded = 'true';
}

// ---- Follow Buttons ----
function initFollowButtons() {
    document.querySelectorAll('.follow-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const username = btn.dataset.username;
            const res = await fetch(`/follow/${username}`, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await res.json();
            btn.textContent = data.following ? 'Following' : 'Follow';
            btn.classList.toggle('btn-primary', !data.following);
            btn.classList.toggle('btn-outline', data.following);
            const fc = document.querySelector('.followers-count');
            if (fc) fc.textContent = data.followers_count;
        });
    });
}

// ---- Notification Polling ----
function initNotificationPolling() {
    const badge = document.querySelector('.notif-badge');
    if (!badge) return;

    async function poll() {
        try {
            const res = await fetch('/api/unread-notifications');
            const data = await res.json();
            badge.textContent = data.count;
            badge.style.display = data.count > 0 ? 'flex' : 'none';
        } catch (e) {}
    }
    poll();
    setInterval(poll, 30000);
}

// ---- Image Preview ----
function initImagePreview() {
    const fileInput = document.querySelector('#image-upload');
    if (!fileInput) return;

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (!file) return;
        let preview = document.querySelector('.image-preview');
        if (!preview) {
            preview = document.createElement('div');
            preview.className = 'image-preview';
            preview.style.cssText = 'margin:8px 0;position:relative;';
            fileInput.parentElement.parentElement.insertBefore(preview, fileInput.parentElement.nextSibling);
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.innerHTML = `
                <img src="${e.target.result}" style="max-width:100%;max-height:200px;border-radius:12px;border:1px solid var(--border);">
                <button type="button" onclick="this.parentElement.remove();document.querySelector('#image-upload').value=''"
                    style="position:absolute;top:8px;right:8px;background:rgba(0,0,0,0.7);color:#fff;border:none;border-radius:50%;width:28px;height:28px;cursor:pointer;font-size:14px;">✕</button>`;
        };
        reader.readAsDataURL(file);
    });
}

// ---- Delete Post ----
function deletePost(postId) {
    if (!confirm('Delete this post?')) return;
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/posts/${postId}/delete`;
    document.body.appendChild(form);
    form.submit();
}

// ---- Message Polling ----
function initMessagePolling() {
    const badge = document.querySelector('.msg-badge');
    if (!badge) return;

    async function poll() {
        try {
            const res = await fetch('/api/messages/unread-count');
            const data = await res.json();
            badge.textContent = data.count;
            badge.style.display = data.count > 0 ? 'flex' : 'none';
        } catch (e) {}
    }
    poll();
    setInterval(poll, 30000); // Check every 30 seconds
}
