import datetime
from django.utils.translation import ugettext_lazy as _
from django import forms

class SplitTimeField(forms.MultiValueField):
    """
    Field written to accept two fields Hour Field and Time Field
    and combine them into TimeField.
    """
    default_error_messages = {
        'invalid_time': _(u'Enter a valid time.'),
    }    

    def __init__(self, *args, **kwargs):
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        fields = (
            forms.CharField(error_messages={'invalid': errors['invalid_time']}),
            forms.CharField(error_messages={'invalid': errors['invalid_time']}),
        )
        super(SplitTimeField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            # Raise a validation error if time or date is empty
            # (possible if SplitDateTimeField has required=False).
            if data_list[0] in (None, '') or data_list[1] in (None, ''):
                raise forms.ValidationError(self.error_messages['invalid_time'])

            if data_list[0] != "-" and data_list[1] != "-":
                return datetime.time(int(data_list[0]),int(data_list[1]))
        return None


