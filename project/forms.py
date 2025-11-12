from django import forms
from .models import Addon
from tinymce.widgets import TinyMCE


class AddonForm(forms.ModelForm):
    class Meta:
        model = Addon
        fields = [
            'name', 'slug', 'description', 'long_description', 'addon_type',
            'version', 'author', 'minecraft_version', 'thumbnail', 'download_file', 'published'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'long_description': TinyMCE(attrs={'cols': 80, 'rows': 10}),
        }

    def clean_slug(self):
        # slug が空文字列の場合は None にして自動生成させる
        slug = self.cleaned_data.get('slug')
        if slug == '':
            return None
        return slug


class CommentForm(forms.ModelForm):
    class Meta:
        from .models import Comment
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows':3, 'placeholder':'コメントを入力してください（日本語可）'}),
        }


class ContactForm(forms.Form):
    name = forms.CharField(label='お名前', max_length=100)
    email = forms.EmailField(label='メールアドレス')
    subject = forms.CharField(label='件名', max_length=200, required=False)
    message = forms.CharField(label='メッセージ', widget=forms.Textarea(attrs={'rows':6}))
    image = forms.ImageField(label='画像添付', required=False)


class ReportForm(forms.ModelForm):
    class Meta:
        from .models import Report
        model = Report
        fields = ['addon', 'url', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows':6}),
        }


class WikiForm(forms.ModelForm):
    class Meta:
        from .models import Wiki
        model = Wiki
        fields = ['title', 'slug', 'image', 'video_url', 'content']
        widgets = {
            'content': TinyMCE(attrs={'cols': 80, 'rows': 10}),
            'video_url': forms.URLInput(attrs={'placeholder':'YouTubeまたは動画URL（例：https://www.youtube.com/watch?v=xxxxx）'}),
        }

    def clean_slug(self):
        # slug が空文字列の場合は None にして自動生成させる
        slug = self.cleaned_data.get('slug')
        if slug == '':
            return None
        return slug
