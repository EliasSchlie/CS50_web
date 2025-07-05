document.addEventListener("DOMContentLoaded", () => {
  const app = new App();
  app.init();
});

class App {
  constructor() {
    this.postsContainer = document.querySelector("#posts-container");
    this.profileContainer = document.querySelector("#profile-view");
    this.newPostContainer = document.querySelector("#new-post-container");
    this.paginationContainer = document.querySelector("#pagination-container");
    this.currentUser = null;
  }

  async init() {
    await this.fetchCurrentUser();
    this.bindNavEvents();
    this.handleRouting();
    window.onpopstate = (event) => {
      this.handleRouting(event.state);
    };
  }

  bindNavEvents() {
    document.querySelector("#all").addEventListener("click", () => this.navigateTo("/"));
    document.querySelector("#following").addEventListener("click", () => this.navigateTo("/following"));
    if (this.currentUser) {
        document.querySelector("#me").addEventListener("click", () => this.navigateTo(`/u/${this.currentUser.username}`)
        );
    }
    document.querySelector("#new-post-form").addEventListener("submit", (e) => {
      e.preventDefault();
      this.createNewPost();
    });
  }

  navigateTo(path, page = 1) {
    const url = new URL(window.location.origin + path);
    url.searchParams.set('page', page);
    history.pushState({ path, page }, "", url);
    this.handleRouting({ path, page });
  }

  handleRouting(state = null) {
    const path = state ? state.path : window.location.pathname;
    const page = state ? state.page : new URLSearchParams(window.location.search).get('page') || 1;
    if (path === "/following") {
      this.loadPosts("following", page);
    } else if (path.startsWith("/u/")) {
      const username = path.split("/")[2];
      this.loadProfile(username, page);
    } else {
      this.loadPosts(null, page);
    }
  }

  async createNewPost() {
    const content = document.querySelector("#new-post-content").value;
    const response = await fetch("/api/posts", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: JSON.stringify({ content }),
    });
    if (response.ok) {
      this.loadPosts();
      document.querySelector("#new-post-content").value = "";
    }
    else {
      console.error("Failed to create post");
    }
  }

  async loadPosts(filter = null, page = 1) {
    if (!filter || filter === 'following') {
        this.show(this.newPostContainer);
        this.hide(this.profileContainer);
    }
    this.postsContainer.innerHTML = "<h3>Posts</h3>";
    const url = new URL(window.location.origin + (filter ? `/api/posts/${filter}` : "/api/posts"));
    url.searchParams.set('page', page);
    const response = await fetch(url);
    const data = await response.json();
    data.posts.forEach((post) => {
      this.postsContainer.appendChild(this.createPostElement(post));
    });
    this.renderPagination(data);
  }

  async loadProfile(username, page = 1) {
    this.hide(this.newPostContainer);
    this.show(this.profileContainer);
    const response = await fetch(`/api/users/${username}`);
    const user = await response.json();
    this.profileContainer.innerHTML = this.createProfileElement(user);
    this.bindFollowButton(user);
    this.loadPosts(username, page);
  }

  renderPagination(data) {
    this.paginationContainer.innerHTML = '';
    const path = window.location.pathname;
    if (data.has_previous) {
        const prevButton = this.createButton('Previous', () => this.navigateTo(path, data.previous_page_number));
        this.paginationContainer.appendChild(prevButton);
    }
    if (data.has_next) {
        const nextButton = this.createButton('Next', () => this.navigateTo(path, data.next_page_number));
        this.paginationContainer.appendChild(nextButton);
    }
  }

  createButton(text, onClick) {
      const button = document.createElement('button');
      button.textContent = text;
      button.className = 'btn btn-secondary mr-2';
      button.addEventListener('click', onClick);
      return button;
  }

  createPostElement(post) {
    const postDiv = this.createDiv("post");
    postDiv.innerHTML = `
      <div class="post-avatar">${post.user.charAt(0).toUpperCase()}</div>
      <div class="post-content">
        <div class="post-header">
          <span class="post-username" data-username="${post.user}">${post.user}</span>
          <span class="post-timestamp">${post.timestamp}</span>
        </div>
        <div class="post-body">${post.content.replace(/\n/g, "<br>")}</div>
        <div class="post-actions">
          <button class="btn btn-primary btn-sm like-btn" data-post-id="${post.id}">${post.is_liked ? "Unlike" : "Like"}</button>
          <span class="like-count">${post.likes.length}</span>
          <button class="btn btn-outline-primary btn-sm ml-3 comment-btn" data-post-id="${post.id}">Comment</button>
          ${this.currentUser && this.currentUser.id === post.user_id ? `<button class="btn btn-outline-secondary btn-sm ml-3 edit-btn" data-post-id="${post.id}">Edit</button>` : ''}
        </div>
        <div class="comments-section" id="comments-section-${post.id}" style="display:none;">
            <div class="comments-list"></div>
            <div class="comment-input-area mt-2">
                <textarea class="form-control comment-textarea" placeholder="Write a comment..."></textarea>
                <button class="btn btn-primary btn-sm mt-2 submit-comment-btn">Submit Comment</button>
            </div>
        </div>
      </div>
    `;
    postDiv.querySelector(".post-username").addEventListener("click", (e) => {
      this.navigateTo(`/u/${e.target.dataset.username}`);
    });
    postDiv.querySelector(".like-btn").addEventListener("click", (e) => {
      this.toggleLike(e.target.dataset.postId);
    });
    const editBtn = postDiv.querySelector(".edit-btn");
    if (editBtn) {
        editBtn.addEventListener("click", (e) => {
            this.editPost(e.target.dataset.postId, postDiv);
        });
    }
    const commentBtn = postDiv.querySelector(".comment-btn");
    if (commentBtn) {
        commentBtn.addEventListener("click", (e) => {
            this.toggleComments(post.id, postDiv);
        });
    }
    return postDiv;
  }

  async toggleComments(postId, postDiv) {
    const commentsSection = postDiv.querySelector(`#comments-section-${postId}`);
    if (commentsSection.style.display === "none") {
        commentsSection.style.display = "block";
        await this.loadComments(postId, commentsSection);
        const submitCommentBtn = commentsSection.querySelector(".submit-comment-btn");
        submitCommentBtn.addEventListener("click", () => {
            const commentContent = commentsSection.querySelector(".comment-textarea").value;
            this.submitComment(postId, commentContent, commentsSection);
        });
    } else {
        commentsSection.style.display = "none";
    }
  }

  async loadComments(postId, commentsSection) {
    const commentsList = commentsSection.querySelector(".comments-list");
    commentsList.innerHTML = "Loading comments...";
    const response = await fetch(`/api/posts/${postId}/comments`);
    const comments = await response.json();
    commentsList.innerHTML = "";
    if (comments.length === 0) {
        commentsList.innerHTML = "No comments yet.";
    } else {
        comments.forEach(comment => {
            const commentDiv = this.createDiv("comment-item");
            commentDiv.innerHTML = `<strong>${comment.user}</strong>: ${comment.content} <span style='color:#888;font-size:0.9em;'>${comment.timestamp}</span>`;
            commentsList.appendChild(commentDiv);
        });
    }
  }

  async submitComment(postId, content, commentsSection) {
    const response = await fetch("/api/comments", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": this.getCookie("csrftoken"),
        },
        body: JSON.stringify({ post_id: postId, content: content })
    });
    if (response.ok) {
        commentsSection.querySelector(".comment-textarea").value = "";
        await this.loadComments(postId, commentsSection);
    } else {
        console.error("Failed to submit comment");
    }
  }

  editPost(postId, postDiv) {
    const postBody = postDiv.querySelector(".post-body");
    const originalContent = postBody.innerHTML.replace(/<br>/g, "\n");
    postBody.innerHTML = `
        <textarea class="form-control">${originalContent}</textarea>
        <button class="btn btn-primary btn-sm mt-2 save-btn">Save</button>
    `;
    postDiv.querySelector(".save-btn").addEventListener("click", () => {
        const newContent = postDiv.querySelector("textarea").value;
        this.savePost(postId, newContent, postDiv);
    });
  }

  async savePost(postId, content, postDiv) {
    const response = await fetch(`/api/posts/${postId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": this.getCookie("csrftoken"),
        },
        body: JSON.stringify({ content })
    });
    if (response.ok) {
        const post = await response.json();
        const postBody = postDiv.querySelector(".post-body");
        postBody.innerHTML = post.content.replace(/\n/g, "<br>");
    } else {
        console.error("Failed to save post");
    }
  }

  createProfileElement(user) {
    return `
      <div class="profile-header">
        <div class="profile-avatar">${user.username.charAt(0).toUpperCase()}</div>
        <div class="profile-info">
          <h3 class="profile-username">${user.username}</h3>
          <div class="profile-stats">
            <div class="profile-stat">
              <span class="stat-count">${user.followers.length}</span>
              <span class="stat-label">Followers</span>
            </div>
            <div class="profile-stat">
              <span class="stat-count">${user.following.length}</span>
              <span class="stat-label">Following</span>
            </div>
          </div>
          ${this.currentUser && this.currentUser.id !== user.id ? `<button id="follow-btn" class="btn btn-primary" data-username="${user.username}">${user.is_following ? "Unfollow" : "Follow"}</button>` : ""}
        </div>
      </div>
    `;
  }

  bindFollowButton(user) {
    const followBtn = document.querySelector("#follow-btn");
    if (followBtn) {
      followBtn.addEventListener("click", async (e) => {
        const username = e.target.dataset.username;
        const response = await fetch(`/api/users/${username}/follow`, {
          method: "POST",
          headers: {
            "X-CSRFToken": this.getCookie("csrftoken"),
          },
        });
        const data = await response.json();
        if (response.ok) {
          this.loadProfile(username);
        } else {
          console.error(data.error);
        }
      });
    }
  }

  async toggleLike(postId) {
    const response = await fetch(`/api/posts/${postId}`,
        {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": this.getCookie("csrftoken"),
            },
            body: JSON.stringify({ like: true })
        });
    if (response.ok) {
        const post = await response.json();
        const likeBtn = document.querySelector(`.like-btn[data-post-id="${postId}"]`);
        const likeCount = likeBtn.nextElementSibling;
        likeBtn.textContent = post.is_liked ? "Unlike" : "Like";
        likeCount.textContent = post.likes.length;
    } else {
        console.error("Failed to like post");
    }
}

  show(element) {
    element.style.display = "block";
  }

  hide(element) {
    element.style.display = "none";
  }

  createDiv(className) {
    const div = document.createElement("div");
    div.className = className;
    return div;
  }

  getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + "=")) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  async fetchCurrentUser() {
    try {
        const response = await fetch("/api/users/me");
        if (response.ok) {
            this.currentUser = await response.json();
        } else {
            this.currentUser = null;
        }
    } catch (error) {
        console.error("Error fetching current user:", error);
        this.currentUser = null;
    }
  }
}
