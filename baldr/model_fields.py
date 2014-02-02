# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.db import models
import odin
from odin import exceptions as odin_exceptions
from odin.codecs import json_codec
import six


class ResourceField(six.with_metaclass(models.SubfieldBase, models.TextField)):
    """Field that serializes/de-serializes a Odin resource to the
    database seamlessly."""

    def __init__(self, resource, *args, **kwargs):
        assert isinstance(self.resource, odin.Resource)
        self.resource = resource
        super(ResourceField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value is None or value == '':
            return self.resource()
        elif isinstance(value, basestring):
            try:
                return json_codec.loads(value, self.resource, False)
            except odin_exceptions.ValidationError as ve:
                raise ValidationError(message=ve.message_dict)
        else:
            return value

    def validate(self, value, model_instance):
        super(ResourceField, self).validate(value, model_instance)

        if value in self.empty_values:
            return

        try:
            value.full_clean()
        except odin_exceptions.ValidationError as ve:
            raise ValidationError(message=ve.message_dict)

    def get_db_prep_save(self, value, connection):
        # Convert our JSON object to a string before we save
        if not isinstance(value, self.resource):
            return super(ResourceField, self).get_db_prep_save("", connection=connection)
        else:
            return super(ResourceField, self).get_db_prep_save(json_codec.dumps(value), connection=connection)

# Register field with south.
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^baldr\.model_fields\.ResourceField"])
except ImportError:
    pass
