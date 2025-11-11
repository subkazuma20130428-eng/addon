from django import forms
from .models import Addon


class AddonForm(forms.ModelForm):
    class Meta:
        model = Addon
        fields = [
            'name', 'slug', 'description', 'long_description', 'addon_type',
            'version', 'author', 'minecraft_version', 'thumbnail', 'download_file', 'published'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'long_description': forms.Textarea(attrs={'rows': 6}),
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
