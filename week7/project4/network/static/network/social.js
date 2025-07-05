// DOMContentLoaded: Set up navigation and load initial posts

document.addEventListener("DOMContentLoaded", () => {
  bindNavEvents();
  loadPosts("all");
});

// Navigation event bindings
function bindNavEvents() {
  document
    .querySelector("#all")
    .addEventListener("click", () => loadPosts("all"));
  document
    .querySelector("#following")
    .addEventListener("click", () => loadPosts("following"));
  document
    .querySelector("#me")
    .addEventListener("click", () => loadPosts("me"));
}

// Main function to load posts based on filter (all, following, me, or user id)
function loadPosts(filter) {
  showElement("#new-post-container");
  hideElement("#profile-view");
  const url = getPostsUrl(filter);
  const postsContainer = document.querySelector("#posts-container");
  postsContainer.innerHTML = `<h3>Posts</h3>`;

  fetch(url)
    .then((response) => response.json())
    .then((posts) => {
      posts.forEach((post) =>
        postsContainer.appendChild(createPostElement(post, filter))
      );
    });
}

// Helper to determine the correct posts URL
function getPostsUrl(filter) {
  if (filter === "me") {
    return `/profile/${window.CURRENT_USER_ID}/posts/`;
  } else if (filter === "all" || filter === "following") {
    return `/posts/${filter}/`;
  } else {
    return `/profile/${filter}/posts/`;
  }
}

// Create a DOM element for a single post
function createPostElement(post, filter) {
  const postDiv = createDiv("post");
  postDiv.appendChild(createAvatar(post.user__username));
  postDiv.appendChild(createPostContent(post, filter));
  return postDiv;
}

function createAvatar(username) {
  const avatarDiv = createDiv("post-avatar");
  avatarDiv.textContent = username ? username.charAt(0).toUpperCase() : "?";
  return avatarDiv;
}

function createPostContent(post, filter) {
  const contentDiv = createDiv("post-content");
  contentDiv.appendChild(createPostHeader(post));
  contentDiv.appendChild(createPostBody(post.content));
  contentDiv.appendChild(createPostActions(post, filter));
  return contentDiv;
}

function createPostHeader(post) {
  const headerDiv = createDiv("post-header");
  const usernameSpan = document.createElement("span");
  usernameSpan.className = "post-username";
  usernameSpan.textContent = post.user__username || "Unknown";
  usernameSpan.style.cursor = "pointer";
  usernameSpan.addEventListener("click", (e) => {
    e.stopPropagation();
    loadProfile(post.user_id);
  });
  const timestampSpan = document.createElement("span");
  timestampSpan.className = "post-timestamp";
  timestampSpan.textContent = post.timestamp;
  headerDiv.append(usernameSpan, timestampSpan);
  return headerDiv;
}

function createPostBody(content) {
  const bodyDiv = createDiv("post-body");
  bodyDiv.innerHTML = content.replace(/\n/g, "<br>");
  return bodyDiv;
}

function createPostActions(post, filter) {
  const actionsDiv = createDiv("post-actions");

  // Like button
  const likeBtn = createButton("Like", "btn btn-primary btn-sm");
  // Like count
  const likeCountSpan = document.createElement("span");
  likeCountSpan.className = "like-count";
  likeCountSpan.textContent = post.likes_count == null ? 0 : post.likes_count;

  // Set initial like button state (optional: could be improved to show if user liked)
  // likeBtn.textContent = post.liked_by_user ? "Unlike" : "Like";

  likeBtn.addEventListener("click", () => {
    fetch("/like/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({ post_id: post.id }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.likes_count !== undefined) {
          likeCountSpan.textContent = data.likes_count;
          likeBtn.textContent = data.liked ? "Unlike" : "Like";
        }
      });
  });

  // Comment button
  const commentBtn = createButton(
    "Comment",
    "btn btn-outline-primary btn-sm ml-3"
  );
  // Show/Hide Comments button
  const toggleCommentsBtn = createButton(
    "Show Comments",
    "btn btn-link btn-sm ml-2"
  );

  // Comments state
  let commentsVisible = false;
  let commentsDiv = null;
  toggleCommentsBtn.addEventListener("click", () => {
    if (commentsVisible) {
      if (commentsDiv && commentsDiv.parentNode) commentsDiv.remove();
      toggleCommentsBtn.textContent = "Show Comments";
      commentsVisible = false;
      return;
    }
    commentsDiv = createDiv("comments-list");
    commentsDiv.style.marginTop = "0.5rem";
    commentsDiv.textContent = "Loading comments...";
    actionsDiv.appendChild(commentsDiv);
    fetch(`/posts/${post.id}/comments/`)
      .then((res) => res.json())
      .then((comments) => {
        commentsDiv.innerHTML = "";
        if (comments.length === 0) {
          commentsDiv.textContent = "No comments yet.";
        } else {
          comments.forEach((c) => {
            const cDiv = createDiv("comment-item");
            cDiv.innerHTML = `<strong>${c.user__username}</strong>: ${c.content} <span style='color:#888;font-size:0.9em;'>${c.timestamp}</span>`;
            commentsDiv.appendChild(cDiv);
          });
        }
      });
    toggleCommentsBtn.textContent = "Hide Comments";
    commentsVisible = true;
  });

  // Comment input
  let commentInputDiv = null;
  commentBtn.addEventListener("click", () => {
    if (commentInputDiv && commentInputDiv.parentNode) {
      commentInputDiv.remove();
      commentInputDiv = null;
      return;
    }
    commentInputDiv = createCommentInput(post.id, filter);
    actionsDiv.appendChild(commentInputDiv);
    commentInputDiv.querySelector("input").focus();
  });

  actionsDiv.append(likeBtn, likeCountSpan, commentBtn, toggleCommentsBtn);
  return actionsDiv;
}

function createCommentInput(postId, filter) {
  const inputDiv = document.createElement("div");
  inputDiv.style.marginTop = "0.5rem";
  inputDiv.style.display = "flex";
  inputDiv.style.gap = "0.5rem";

  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = "Write a comment...";
  input.className = "form-control";
  input.style.flex = "1";

  const submitBtn = createButton("Submit", "btn btn-primary btn-sm");
  submitBtn.addEventListener("click", () => {
    const commentText = input.value.trim();
    if (commentText) {
      sendComment(
        postId,
        commentText,
        () => {
          alert("Comment posted!");
          loadPosts(filter);
        },
        (err) => alert("Failed to post comment: " + err)
      );
    }
  });

  inputDiv.append(input, submitBtn);
  return inputDiv;
}

// Profile loading
function loadProfile(profileId) {
  fetch(`/profile/${profileId}`)
    .then((response) => response.text())
    .then((html) => {
      document.querySelector("#profile-view").innerHTML = html;
      bindFollowButton();
    });
  loadPosts(profileId);
  showElement("#profile-view");
  hideElement("#new-post-container");
}

function bindFollowButton() {
  const followBtn = document.getElementById("follow-btn");
  if (followBtn) {
    followBtn.addEventListener("click", function () {
      const profileId = this.getAttribute("data-profile-id");
      fetch("/follow_toggle/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ profile_id: profileId }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.error) {
            alert(data.error);
            return;
          }
          // Update button text
          this.textContent = data.following ? "Unfollow" : "Follow";
          // Update followers count
          document.getElementById("followers-count").textContent =
            data.followers_count;
        })
        .catch((error) => {
          alert("An error occurred: " + error);
        });
    });
  }
}

// Send comment to server
function sendComment(postId, commentText, onSuccess, onError) {
  fetch("/comment/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ post_id: postId, comment: commentText }),
  })
    .then((response) => {
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        return response.json();
      } else {
        return response.text().then((text) => {
          throw new Error(text);
        });
      }
    })
    .then((data) => {
      if (data.success) {
        if (onSuccess) onSuccess(data);
      } else {
        if (onError) onError(data.error || "Unknown error");
      }
    })
    .catch((error) => {
      if (onError) onError(error.message || error);
    });
}

// Utility: get CSRF token from cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    document.cookie.split(";").forEach((cookie) => {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
      }
    });
  }
  return cookieValue;
}

// Utility: show/hide elements
function showElement(selector) {
  document.querySelector(selector).style.display = "block";
}
function hideElement(selector) {
  document.querySelector(selector).style.display = "none";
}

// Utility: create div/button with class
function createDiv(className) {
  const div = document.createElement("div");
  div.className = className;
  return div;
}
function createButton(text, className) {
  const btn = document.createElement("button");
  btn.textContent = text;
  btn.className = className;
  return btn;
}
