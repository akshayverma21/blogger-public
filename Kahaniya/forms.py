from . models import Author,Blogpost,ReaderProfile, Comment
from django import forms
from django.contrib.auth.models import User

class Authorform(forms.ModelForm):
    class Meta:
        model= Author
        fields= ['name','bio', 'profile_photo', 'email','email_notifications']
        exludes=['user', 'join_date','is_ban', 'has_applied_for_author','is_approved']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'bg-[#2a2a2a] text-white border border-gray-600 rounded-md p-2 w-full',
                'placeholder': 'Enter title here'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'bg-[#2a2a2a] text-white border border-gray-600 rounded-md p-2 w-full',
                'placeholder': 'Write your blog content here...',
                'rows': 8
            }),
            'profile_photo': forms.ClearableFileInput(attrs={
                'class': 'text-white'
            }),

            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-checkbox bg-black'
            }),
            'email': forms.TextInput(attrs={
                'class': 'bg-[#2a2a2a] text-white border border-gray-600 rounded-md p-2 w-full',
                'placeholder': 'Enter your email here'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email

    def clean_email(self):
        email = self.cleaned_data['email']
        user= self.request.user if hasattr(self,'request') else None
        if user and email == user.email:
            return email
        if Author.objects.filter(email=email).exclude(user=user).exists():
            raise forms.ValidationError("This email is already in use by another author.")
        return email

class Blogform(forms.ModelForm):
    class Meta:
        model = Blogpost
        fields = ['title', 'category_choices', 'content', 'blog_image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'bg-[#2a2a2a] text-white border border-gray-600 rounded-md p-2 w-full',
                'placeholder': 'Enter title here'
            }),
            'content': forms.Textarea(attrs={
                'class': 'bg-[#2a2a2a] text-white border border-gray-600 rounded-md p-2 w-full',
                'placeholder': 'Write your blog content here...',
                'rows': 8
            }),
            'blog_image': forms.ClearableFileInput(attrs={
                'class': 'text-white'
            }),
             'category_choices': forms.Select(attrs={
                'class': 'bg-[#2a2a2a] text-white border border-gray-600 rounded-md p-2 w-full'
            }),
            
        }



class ReaderProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False) 
    class Meta:
        model = ReaderProfile
        fields = ['name','bio', 'profile_photo', 'dob', 'gender']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'bg-[#2a2a2a] text-white border border-gray-600 rounded-md p-2 w-full',
                'placeholder': 'Enter title here'
            }),

            'bio': forms.Textarea(attrs={
                'class': 'bg-[#2a2a2a] text-white border border-gray-600 rounded-md p-2 w-full',
                'placeholder': 'Write your blog content here...',
                'rows': 8
            }),
            'profile_photo': forms.ClearableFileInput(attrs={
                'class': 'text-white'
            }),

            'dob': forms.DateInput(attrs={
                'type': 'date',  # Enables the calendar picker
                'class': 'bg-[#2a2a2a] text-white border border-gray-600 rounded-md p-2 w-full'
            }),
            'gender': forms.Select(attrs={
                'class': 'bg-[#2a2a2a] text-white border border-gray-600 rounded-md p-2 w-full'
            }),
        }


class Commentform(forms.ModelForm):
    class Meta:
        model=Comment
        fields=['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'placeholder': 'Write your comment...',
                'class': 'w-full p-2 rounded bg-gray-900 text-white border border-gray-700',
                'rows': 3,
            })
        }

    def clean_body(self):
        body=self.cleaned_data.get('body', '').strip()
        if not body:
            raise forms.ValidationError('cannot be empty')
        return body