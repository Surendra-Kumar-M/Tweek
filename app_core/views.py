import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PostForm, ProfileForm, SearchForm, SignupForm
from .models import FollowersCount, LikePost, Post, Profile

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feed / Index
# ---------------------------------------------------------------------------

@login_required(login_url='signin')
def index(request):
    """Home feed showing posts from followed users + follow suggestions."""
    user_profile = request.user.profile

    # IDs of users the current user follows — single query
    following_user_ids = FollowersCount.objects.filter(
        follower=request.user,
    ).values_list('user_id', flat=True)

    # Posts from followed users — single query with select_related
    feed_list = (
        Post.objects
        .filter(user_id__in=following_user_ids)
        .select_related('user', 'user__profile')
        .order_by('-created_at')
    )

    # Follow suggestions — users not yet followed, excluding self
    suggestions = (
        Profile.objects
        .select_related('user')
        .exclude(user_id__in=following_user_ids)
        .exclude(user=request.user)
    )[:4]

    return render(request, 'index.html', {
        'user_profile': user_profile,
        'posts': feed_list,
        'suggestions_username_profile_list': suggestions,
    })


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def signup(request):
    """User registration with form validation."""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            # Create profile for the new user
            Profile.objects.create(user=user)

            # Log in and redirect to settings
            login(request, user)
            return redirect('setting')
        # If form is invalid, errors are rendered in the template
    else:
        form = SignupForm()

    return render(request, 'signup.html', {'form': form})


def signin(request):
    """Login with username or email."""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = None
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        else:
            user = authenticate(request, username=username_or_email, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, 'Invalid credentials. Please try again.')
            return redirect('signin')

    return render(request, 'signin.html')


@login_required(login_url='signin')
def logout_view(request):
    """Log out the current user."""
    auth_logout(request)
    return redirect('signin')


# ---------------------------------------------------------------------------
# Profile & Settings
# ---------------------------------------------------------------------------

@login_required(login_url='signin')
def setting(request):
    """Edit profile settings (image, bio, location)."""
    user_profile = request.user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('setting')
    else:
        form = ProfileForm(instance=user_profile)

    return render(request, 'setting.html', {
        'user_profile': user_profile,
        'form': form,
    })


@login_required(login_url='signin')
def profile(request, pk):
    """View a user's profile page."""
    user_object = get_object_or_404(User, username=pk)
    user_profile = get_object_or_404(Profile, user=user_object)
    user_posts = Post.objects.filter(user=user_object)
    user_post_length = user_posts.count()

    follower_count = FollowersCount.objects.filter(user=user_object).count()
    following_count = FollowersCount.objects.filter(follower=user_object).count()

    is_following = FollowersCount.objects.filter(
        user=user_object,
        follower=request.user,
    ).exists()
    button_text = 'Unfollow' if is_following else 'Follow'

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'follower_count': follower_count,
        'following_count': following_count,
        'button_text': button_text,
    }
    return render(request, 'profile.html', context)


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------

@login_required(login_url='signin')
@require_POST
def upload(request):
    """Upload a new post (image + caption). POST only."""
    form = PostForm(request.POST, request.FILES)
    if form.is_valid():
        Post.objects.create(
            user=request.user,
            image=form.cleaned_data['image_upload'],
            caption=form.cleaned_data['caption'],
        )
        messages.success(request, 'Post uploaded!')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{error}')

    return redirect('/')


@login_required(login_url='signin')
@require_POST
def like_post(request):
    """Toggle like on a post. POST only to prevent CSRF via link."""
    post_id = request.POST.get('post_id')
    post = get_object_or_404(Post, id=post_id)

    try:
        # Try to create the like
        LikePost.objects.create(post=post, user=request.user)
        post.no_of_likes += 1
        post.save(update_fields=['no_of_likes'])
    except IntegrityError:
        # Already liked — unlike
        LikePost.objects.filter(post=post, user=request.user).delete()
        post.no_of_likes = max(0, post.no_of_likes - 1)
        post.save(update_fields=['no_of_likes'])

    return redirect('/')


# ---------------------------------------------------------------------------
# Follow
# ---------------------------------------------------------------------------

@login_required(login_url='signin')
@require_POST
def follow(request):
    """Toggle follow/unfollow on a user. POST only."""
    user_to_follow = get_object_or_404(User, username=request.POST.get('user', ''))

    # Prevent self-follow
    if user_to_follow == request.user:
        messages.warning(request, "You can't follow yourself.")
        return redirect('profile', pk=user_to_follow.username)

    existing = FollowersCount.objects.filter(
        follower=request.user,
        user=user_to_follow,
    ).first()

    if existing:
        existing.delete()
    else:
        try:
            FollowersCount.objects.create(
                follower=request.user,
                user=user_to_follow,
            )
        except IntegrityError:
            pass  # Race condition — already followed

    return redirect('profile', pk=user_to_follow.username)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@login_required(login_url='signin')
def search(request):
    """Search for users by username."""
    user_profile = request.user.profile
    username = ''
    username_profile_list = []

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        if username:
            # Single efficient query with select_related
            username_profile_list = list(
                Profile.objects
                .select_related('user')
                .filter(user__username__icontains=username)
            )

    return render(request, 'search.html', {
        'username': username,
        'user_profile': user_profile,
        'username_profile_list': username_profile_list,
    })
