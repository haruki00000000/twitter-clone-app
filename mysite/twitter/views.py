from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.views import generic
from django.views.generic.edit import FormView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import TweetForm
from .models import Tweet, FriendShip, Like
from .helpers import get_current_user


class IndexView(generic.TemplateView):
    template_name = "twitter/signup.html"

# Create your views here.


class UserInputView(generic.FormView):
    form_class = UserCreationForm
    template_name = 'twitter/input.html'

    def form_valid(self, form):
        return render(self.request, 'twitter/input.html', {'form': form})


class UserConfirmView(generic.FormView):
    form_class = UserCreationForm

    def form_valid(self, form):
        return render(self.request, 'twitter/confirm.html', {'form': form})

    def form_invalid(self, form):
        return render(self.request, 'twitter/input.html', {'form': form})


class UserCreateView(generic.FormView):
    form_class = UserCreationForm
    success_url = reverse_lazy('twitter:home')

    def form_valid(self, form):
        # 認証
        user = form.save()
        # ログイン
        login(self.request, user)
        return super().form_valid(form)

    def form_invalid(self, form):
        return render(self.request, 'twitter/input.html', {'form': form})


class HomeView(LoginRequiredMixin, generic.FormView):
    template_name = "twitter/home.html"
    form_class = TweetForm
    login_url = '/'

    def get_context_data(self, **kwargs):
        initial_dict = {'user': self.request.user}
        form_class = TweetForm(self.request.POST or None, initial=initial_dict)
        # TemplateViewにあるcontextを取得
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        # contextにformというキーでformという変数を追加
        context["form"] = form_class
        # contextにtweetsというキーでツイート一覧を追加
        context["tweets"] = Tweet.objects.all()
        context['my_likes_ids'] = Like.objects.filter(
            user=self.request.user).values_list('tweet_id', flat=True)
        return context
    def get_success_url(self):
        return reverse('twitter:profile', kwargs={'pk': self.user.id})


class CreateTweet(generic.FormView):
    success_url = reverse_lazy('twitter:home')
    form_class = TweetForm

    def form_valid(self, form):
        form_class = TweetForm(self.request.POST)
        post = form_class.save(commit=False)
        post.user = self.request.user
        post = form.save()
        return redirect('twitter:home')

    def form_invalid(self, form):
        return render(self.request, 'twitter/home.html', {'form': form})


class ProfileView(generic.DetailView):
    model = User
    template_name = "twitter/profile.html"

    def get_context_data(self, **kwargs):
        follower = User.objects.get(username=self.request.user)
        followee = User.objects.get(id=self.kwargs['pk'])
        context = super(ProfileView, self).get_context_data(**kwargs)
        user_id = self.kwargs['pk']
        context['user_id'] = user_id
        context['current_user'] = get_current_user(self.request)
        context['followee'] = FriendShip.objects.filter(
            followee=followee).count()
        context['follower'] = FriendShip.objects.filter(
            follower=followee).count()
        context['followees'] = FriendShip.objects.filter(followee=followee)
        context['followers'] = FriendShip.objects.filter(follower=followee)
        if user_id is not context['current_user'].username:
            result = FriendShip.objects.filter(
                follower=follower).filter(followee=followee)
            context['connected'] = True if result else False
        return context

def like(request, tweet_id):
    tweet = Tweet.objects.get(pk=tweet_id)
    like_num = Like.objects.filter(
        user=request.user).filter(tweet=tweet).count()
    if like_num > 0:
        return redirect('twitter:home')
    tweet.like += 1
    tweet.save()
    like = Like()
    like.user = request.user
    like.tweet = tweet
    like.save()
    return redirect('twitter:home')

def unlike(request, tweet_id):
    tweet = Tweet.objects.get(pk=tweet_id)
    like_num = Like.objects.filter(
        user=request.user).filter(tweet=tweet).count()
    if like_num == 0:
        return redirect('twitter:home')
    liking = Like.objects.get(tweet_id=tweet_id, user=request.user)
    liking.delete()
    tweet.like -= 1
    tweet.save()
    return redirect('twitter:home')

def follow_view(request, *args, **kwargs):
    follower = User.objects.get(username=request.user)
    followee = User.objects.get(id=kwargs['pk'])
    if follower == followee:
        messages.warning(request, '自分自身はフォローできません')
        return redirect('twitter:profile', pk=followee.id)
    created = FriendShip.objects.get_or_create(
        follower=follower, followee=followee)
    if (created):
        messages.success(request, '{}をフォローしました'.format(followee.username))
    else:
        messages.warning(
            request, 'あなたはすでに{}をフォローしています'.format(followee.username))
    return redirect('twitter:profile', pk=followee.id)


def unfollow_view(request, *args, **kwargs):
    follower = User.objects.get(username=request.user)
    followee = User.objects.get(id=kwargs['pk'])
    if follower == followee:
        messages.warning(request, '自分自身のフォローを外せません')
    else:
        unfollow = FriendShip.objects.get(follower=follower, followee=followee)
        unfollow.delete()
        messages.success(
            request, 'あなたは{}のフォローを外しました'.format(followee.username))
    return redirect('twitter:profile', pk=followee.id)
