from django import forms
from django.contrib import admin
from .models import Configuration


class ConfigurationAdminForm(forms.ModelForm):
    class Meta:
        model = Configuration
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['value'].widget = forms.TextInput()


class ConfigurationAdmin(admin.ModelAdmin):
    form = ConfigurationAdminForm
    list_display = ('namespace', 'name', 'value_type', 'value')
    search_fields = ('namespace', 'name', 'value')
    list_filter = ('value_type', 'namespace')

    # Add JavaScript to dynamically update the value field based on value_type
    class Media:
        js = ('admin/js/configuration_type.js',)


admin.site.register(Configuration, ConfigurationAdmin)
