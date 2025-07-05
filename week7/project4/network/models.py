from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    followers = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='following')

    def serialize(self, user):
        return {
            "id": self.id,
            "username": self.username,
            "followers": [follower.username for follower in self.followers.all()],
            "following": [following.username for following in self.following.all()],
            "is_following": user in self.followers.all(),
        }

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)

    def __str__(self):
        return f"{self.user} posted {self.content}"

    def serialize(self, user):
        return {
            "id": self.id,
            "user": self.user.username,
            "user_id": self.user.id,
            "content": self.content,
            "timestamp": self.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "likes": [like.username for like in self.likes.all()],
            "comments": [comment.serialize() for comment in self.comments.all()],
            "is_liked": user in self.likes.all(),
        }

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} commented on {self.post}"

    def serialize(self):
        return {
            "id": self.id,
            "user": self.user.username,
            "content": self.content,
            "timestamp": self.timestamp.strftime("%b %d %Y, %I:%M %p"),
        }

class LikeLog(models.Model):
    ACTION_CHOICES = (
        ("like", "Like"),
        ("unlike", "Unlike"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="like_logs")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="like_logs")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.action}d post {self.post.id} at {self.timestamp}"