from django.contrib import admin

from .models import Profile, Post, LikePost, FollowersCount


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'bio_preview')
    search_fields = ('user__username', 'user__email', 'location')
    list_filter = ('location',)
    raw_id_fields = ('user',)

    @admin.display(description='Bio')
    def bio_preview(self, obj):
        return (obj.bio[:75] + '…') if len(obj.bio) > 75 else obj.bio


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'caption_preview', 'no_of_likes', 'created_at')
    search_fields = ('user__username', 'caption')
    list_filter = ('created_at',)
    readonly_fields = ('id', 'no_of_likes')
    raw_id_fields = ('user',)

    @admin.display(description='Caption')
    def caption_preview(self, obj):
        return (obj.caption[:75] + '…') if len(obj.caption) > 75 else obj.caption


@admin.register(LikePost)
class LikePostAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('created_at',)
    raw_id_fields = ('user', 'post')


@admin.register(FollowersCount)
class FollowersCountAdmin(admin.ModelAdmin):
    list_display = ('follower', 'user', 'created_at')
    search_fields = ('follower__username', 'user__username')
    list_filter = ('created_at',)
    raw_id_fields = ('user', 'follower')