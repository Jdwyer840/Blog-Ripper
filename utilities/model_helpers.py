import datetime
from typing import Any, Union, Type, List, Dict
from django.apps import apps
from django.db import models, transaction
from django.db.models import Q
from rest_framework import serializers


from utilities.common import CoreUtilities


class ModelHelpers:

    @staticmethod
    def _prep_field_index(table: str, field: Union[list, str]) -> dict:
        fields = field if isinstance(field, list) else [field]
        # The index name cannot be longer than 30 characters but must be unique and recreatable.
        index_long_name = table + '_' + '_'.join(fields)
        index_name = 'idx_' + CoreUtilities.configurable_hex_digest(output_size=20, data=str.encode(index_long_name))
        return {'fields': fields, 'name': index_name}

    @staticmethod
    def index(table: str, field: Union[list, str]) -> models.Index:
        return models.Index(**ModelHelpers._prep_field_index(table, field))

    @staticmethod
    def indexes(table: str, fields_list: list) -> list:
        ret = []
        for field_list in fields_list:
            ret.append(ModelHelpers.index(table, field_list))
        return ret

    @staticmethod
    def unique_constraint(table: str, field: Union[list, str]) -> models.UniqueConstraint:
        return models.UniqueConstraint(**ModelHelpers._prep_field_index(table, field))

    @classmethod
    def datetime_now_utc(cls: Any) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    @staticmethod
    def datetime_tz_aware(value: str, tz: Any = datetime.timezone.utc) -> datetime.datetime | None:
        return CoreUtilities.datetime_tz_aware(value=value, tz=tz) if value is not None and len(value) else None

    @staticmethod
    def get_all_app_models() -> dict:
        all_models = {}
        for m in apps.get_models():
            if m._meta.app_label not in all_models:
                all_models[m._meta.app_label] = {}
            all_models[m._meta.app_label][m._meta.db_table] = m
        return all_models

    @staticmethod
    def get_field_name(field: Any) -> str:
        return getattr(field, 'field').name

    @staticmethod
    def get_field_db_column(field: Any) -> str:
        return getattr(field, 'field').db_column

    class UpsertResult:
        model = None
        created = None
        updated = None
        updated_fields = None

        def __init__(self, model_: models.Model, created_: bool, updated_: bool, updated_fields_: list):
            self.model = model_
            self.created = created_
            self.updated = updated_
            self.updated_fields = updated_fields_

    @staticmethod
    def simple_serialize(instance: [models.Model]) -> dict:
        class GenericModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = instance.__class__
                fields = '__all__'
        return GenericModelSerializer(instance).data



class ModelMixins:

    """Fields"""
    class PKID(models.Model):
        id = models.BigAutoField(primary_key=True)

        class Meta:
            abstract = True

    class CreatedAt(models.Model):
        default_now = ModelHelpers.datetime_now_utc

        created_at = models.DateTimeField()

        def save(self, *args, **kwargs) -> None:
            if self._state.adding:
                self.created_at = self.default_now()
            super(ModelMixins.CreatedAt, self).save(*args, **kwargs)

        class Meta:
            abstract = True

        optional_index_created_at = ['created_at']

    class CreatedBy(models.Model):
        created_by = models.CharField(max_length=255, blank=True, null=True)

        def save(self, *args, **kwargs) -> None:
            if self._state.adding:
                if hasattr(self, 'created_by_name'):
                    self.created_by = self.created_by_name  # inheritors of CreatedBy must specify created_by_name (instance level) # noqa
            super(ModelMixins.CreatedBy, self).save(*args, **kwargs)

        class Meta:
            abstract = True

        optional_index_created_by = ['created_by']

    class Created(CreatedAt, CreatedBy):

        class Meta:
            abstract = True

    class UpdatedAt(models.Model):
        default_now = ModelHelpers.datetime_now_utc

        # https://code.djangoproject.com/ticket/22981

        updated_at = models.DateTimeField(null=True)

        def save(self, *args, **kwargs) -> None:
            if not self._state.adding:
                self.updated_at = self.default_now()
            super(ModelMixins.UpdatedAt, self).save(*args, **kwargs)

        class Meta:
            abstract = True

        optional_index_updated_at = ['updated_at']

    class UpdatedBy(models.Model):
        updated_by = models.CharField(max_length=255, blank=True, null=True)

        def save(self, *args, **kwargs) -> None:
            if not self._state.adding:
                if hasattr(self, 'updated_by_name'):
                    self.updated_by = self.updated_by_name  # inheritors of UpdatedAt must specify updated_by_name (instance level) # noqa
            super(ModelMixins.UpdatedBy, self).save(*args, **kwargs)

        class Meta:
            abstract = True

        optional_index_updated_by = ['updated_by']

    class Updated(UpdatedAt, UpdatedBy):

        class Meta:
            abstract = True

    class CreatedAtUpdatedAt(CreatedAt, UpdatedAt):

        class Meta:
            abstract = True

        optional_at_indexes = ['created_at', 'updated_at']

    class Clearable(models.Model):
        """Useful because Model.objects.all().delete() may fail on large sqlite tables"""

        @classmethod
        def clear(cls: Any) -> None:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM "{0}"'.format(cls._meta.db_table))  # noqa
                connection.commit()

        class Meta:
            abstract = True


    class Upsertable(Clearable, models.Model):
        """Will only call save() if the row doesn't exist or some field has changed"""

        class Meta:
            abstract = True

        @classmethod
        def upsert(cls: Any, get_fields: Union[dict, models.Model], set_fields: dict = None) -> ModelHelpers.UpsertResult:
            set_fields = set_fields if set_fields else {}
            already_exists = False
            some_field_updated = False
            updated_fields = []

            row_obj = None
            if isinstance(get_fields, dict):
                try:
                    if len(get_fields):
                        row_obj = cls.objects.get(**get_fields)
                        already_exists = True
                    else:
                        row_obj = cls()
                except cls.DoesNotExist:
                    row_obj = cls(**get_fields)
            else:
                row_obj = get_fields
                if not row_obj._state.adding:
                    already_exists = True

            if issubclass(cls, ModelMixins.CreatedBy):
                row_obj.created_by_name = set_fields.pop('created_by', None)
            if issubclass(cls, ModelMixins.UpdatedBy):
                row_obj.updated_by_name = set_fields.pop('updated_by', None)

            should_set_updated_at = already_exists and hasattr(row_obj, 'updated_at')

            # Callers of upsert() need to take care to make sure
            # the types in set_fields match the model (e.g. setting string vs. datetime)
            for key, value in set_fields.items():
                if not hasattr(row_obj, key) or getattr(row_obj, key) != value:
                    setattr(row_obj, key, value)
                    updated_fields.append(key)
                    some_field_updated = True

            if not should_set_updated_at:
                row_obj.updated_at = None

            if not already_exists or some_field_updated:
                row_obj.save()

            return ModelHelpers.UpsertResult(row_obj, not already_exists, some_field_updated, updated_fields)

        @staticmethod
        @transaction.atomic
        def bulk_upsert(cls: Type[models.Model], data: List[Dict[str, Any]], unique_fields: List[str], update_fields: List[str] = None) -> None:
            """
            Perform a bulk upsert operation. If a record exists with matching unique fields, it is updated;
            otherwise, a new record is created.

            Args:
                cls (Type[models.Model]): The model class to perform the upsert on.
                data (List[Dict[str, Any]]): List of dictionaries, each representing a record to upsert.
                unique_fields (List[str]): List of field names that uniquely identify a record.
                update_fields (List[str], optional): List of fields to update if a matching record is found.
            """
            # Ensure update_fields are provided if not given (all fields except unique ones)
            if update_fields is None:
                update_fields = [field for field in data[0].keys() if field not in unique_fields]

            # Generate unique key tuples from unique fields in the data
            unique_tuples = [(tuple(record[field] for field in unique_fields), record) for record in data]

            # Query to find existing records matching the unique constraints
            query = Q()
            for field in unique_fields:
                query &= Q(**{f"{field}__in": [record[field] for record in data]})

            existing_records = cls.objects.filter(query)

            # Map existing records based on their unique field values
            existing_map = {
                tuple(getattr(record, field) for field in unique_fields): record
                for record in existing_records
            }

            # Separate data into records to create and records to update
            to_create = []
            to_update = []

            for unique_key, record_data in unique_tuples:
                if unique_key in existing_map:
                    # Update the fields for the existing record
                    existing_record = existing_map[unique_key]
                    for field in update_fields:
                        setattr(existing_record, field, record_data[field])
                    to_update.append(existing_record)
                else:
                    # Create a new record
                    to_create.append(cls(**record_data))

            # Perform bulk create and bulk update
            if to_create:
                cls.objects.bulk_create(to_create)
            if to_update:
                cls.objects.bulk_update(to_update, update_fields)


    @staticmethod
    @transaction.atomic
    def bulk_upsert(cls: Type[models.Model], data: List[Dict[str, Any]], unique_fields: List[str], update_fields: List[str] = None) -> None:
        """
        Perform a bulk upsert operation. If a record exists with matching unique fields, it is updated;
        otherwise, a new record is created.

        Args:
            cls (Type[models.Model]): The model class to perform the upsert on.
            data (List[Dict[str, Any]]): List of dictionaries, each representing a record to upsert.
            unique_fields (List[str]): List of field names that uniquely identify a record.
            update_fields (List[str], optional): List of fields to update if a matching record is found.
        """
        # Ensure update_fields are provided if not given (all fields except unique ones)
        if update_fields is None:
            update_fields = [field for field in data[0].keys() if field not in unique_fields]

        # Generate unique key tuples from unique fields in the data
        unique_tuples = [(tuple(record[field] for field in unique_fields), record) for record in data]

        # Query to find existing records matching the unique constraints
        query = Q()
        for field in unique_fields:
            query &= Q(**{f"{field}__in": [record[field] for record in data]})

        existing_records = cls.objects.filter(query)

        # Map existing records based on their unique field values
        existing_map = {
            tuple(getattr(record, field) for field in unique_fields): record
            for record in existing_records
        }

        # Separate data into records to create and records to update
        to_create = []
        to_update = []

        for unique_key, record_data in unique_tuples:
            if unique_key in existing_map:
                # Update the fields for the existing record
                existing_record = existing_map[unique_key]
                for field in update_fields:
                    setattr(existing_record, field, record_data[field])
                to_update.append(existing_record)
            else:
                # Create a new record
                to_create.append(cls(**record_data))

        # Perform bulk create and bulk update
        if to_create:
            cls.objects.bulk_create(to_create)
        if to_update:
            cls.objects.bulk_update(to_update, update_fields)

        class Meta:
            abstract = True

    class CreatedUpdated(Created, Updated):

        class Meta:
            abstract = True

        optional_at_indexes = ['created_at', 'updated_at']
        optional_by_indexes = ['created_by', 'updated_by']
        optional_all_indexes = optional_at_indexes + optional_by_indexes

    class CreatedAtUpdatedAt(CreatedAt, UpdatedAt):

        class Meta:
            abstract = True

        optional_at_indexes = ['created_at', 'updated_at']

    class BaseModel(PKID, CreatedUpdated, Upsertable):
        default_now = ModelHelpers.datetime_now_utc
        datetime_tz = CoreUtilities.datetime_zoneinfo('UTC')

        class Meta:
            abstract = True

    class BaseModelWithoutBy(PKID, CreatedAtUpdatedAt, Upsertable):
        default_now = ModelHelpers.datetime_now_utc
        datetime_tz = CoreUtilities.datetime_zoneinfo('UTC')

        class Meta:
            abstract = True


class ConfigDict(dict):
    namespace = "unknown"

    class MissingConfigurationField(Exception):
        def __init__(self, namespace: str, key: Any):
            super().__init__(f'Configuration {namespace}.{key} not found.')

    def __getitem__(self, key: Any) -> Any:
        try:
            return super().__getitem__(key)
        except KeyError:
            raise ConfigDict.MissingConfigurationField(namespace=self.namespace, key=key)