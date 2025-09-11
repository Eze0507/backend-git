from django import forms
from django.contrib.auth.models import Group, Permission

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
 

#from django import forms
#from django.contrib.auth.models import Group, Permission

#class GroupForm(forms.ModelForm):
   # permissions = forms.ModelMultipleChoiceField(
    #    queryset=Permission.objects.all(),
      #  required=False,
  #     #/* widget=forms.CheckboxSelectMultiple
# )

   # class Meta:
     #   model = Group
      #  fields = ['name', 'permissions']*\

