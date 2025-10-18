# social/admin.py
from django.contrib import admin
from .models import Follow, Post, Comment, PostLike, CommentLike


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']
    date_hierarchy = 'created_at'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'content_preview', 'likes_count', 'comments_count', 'allow_comments', 'created_at']
    list_filter = ['allow_comments', 'created_at']
    search_fields = ['author__username', 'content']
    date_hierarchy = 'created_at'
    readonly_fields = ['likes_count', 'comments_count', 'created_at', 'updated_at']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'post', 'parent_comment', 'content_preview', 'likes_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['author__username', 'content']
    date_hierarchy = 'created_at'
    readonly_fields = ['likes_count', 'created_at', 'updated_at']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__author__username']
    date_hierarchy = 'created_at'


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment', 'amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'comment__author__username']
    date_hierarchy = 'created_at'
