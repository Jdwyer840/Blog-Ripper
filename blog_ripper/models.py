import datetime
import json
from typing import Any

from croniter import croniter
from django.db import models
from cron_descriptor import get_description
from django.forms import model_to_dict

from utilities.common import CoreUtilities
from utilities.model_helpers import ModelMixins


class CronJob(ModelMixins.BaseModelWithoutBy):
    default_now = datetime.datetime.now()
    schedule = models.CharField(max_length=512, null=False)
    schedule_description = models.TextField(null=True, blank=True)
    next_run_time = models.DateTimeField(null=True, blank=True)
    command = models.TextField(null=False)
    job_name = models.CharField(max_length=255, null=False, blank=False)
    optional_description = models.CharField(max_length=255, null=True, blank=True)
    active = models.BooleanField(null=False, blank=False)

    class Meta:
        db_table = 'cron_job'
        verbose_name_plural = 'Cron Jobs'

    target_tz = CoreUtilities.datetime_zoneinfo('America/Chicago')

    @classmethod
    def get_cronjob_list_as_str_format(cls: Any, active_only: bool = True) -> list:
        filters = {}
        if active_only:
            filters['active'] = True
        return [f'{cron.schedule} {cron.command}' for cron in cls.objects.filter(**filters)]

    @classmethod
    def get_cron_job_by_id(cls: Any, cron_job_id: int) -> 'CronJob':
        return cls.objects.get(id=cron_job_id)

    @classmethod
    def get_cronjobs_as_list(cls: Any, active_only: bool = False) -> list:
        filters = {}
        if active_only:
            filters['active'] = True
        return list(cls.objects.filter(**filters).values())

    @classmethod
    def get_cronjob_by_command_as_dict(cls: Any, command_with_args: str) -> dict:
        try:
            cronjob_dict = list(cls.objects.filter(command__iendswith=command_with_args).values())[0]
        except Exception:  # noqa
            cronjob_dict = {}
        return cronjob_dict

    @classmethod
    def trigger_save_actions_on_all_objects(cls: Any) -> None:
        for cron in cls.objects.all():
            cron.save()

    @classmethod
    def get_next_run_time(cls: Any, cron_expression: str) -> datetime.datetime:
        cron = croniter(cron_expression, datetime.datetime.now(tz=CronJob.target_tz))
        next_run_time = cron.get_next(datetime.datetime)
        return next_run_time.astimezone(CronJob.target_tz)

    def _update_schedule_description(self) -> None:
        try:
            schedule = get_description(self.schedule)
        except Exception:  # noqa
            schedule = 'Invalid Syntax'

        if self.schedule_description == schedule:
            return

        self.schedule_description = schedule

    def _update_next_run_time(self) -> None:
        next_run_time = None

        try:
            if self.active:
                next_run_time = self.get_next_run_time(self.schedule)
        except Exception:  # noqa
            pass

        if self.next_run_time == next_run_time:
            return

        self.next_run_time = next_run_time

    def save(self, *args, **kwargs) -> None:
        self._update_schedule_description()
        self._update_next_run_time()
        super().save(*args, **kwargs)


class CronJobHistory(ModelMixins.PKID):

    def __str__(self) -> str:
        return self.job_name

    cron_job = models.ForeignKey('CronJob', on_delete=models.CASCADE, null=True, blank=True)
    job_name = models.CharField(max_length=255)
    success = models.BooleanField(default=False)
    runtime = models.FloatField(null=True, blank=True)
    errors = models.TextField(null=True, blank=True)
    last_runtime = models.DateTimeField(null=True, blank=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if isinstance(self.errors, dict) or isinstance(self.errors, list):
            self.errors = json.dumps(self.errors, indent=4)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'cron_job_history'
        verbose_name_plural = 'Cron Job History'

    @classmethod
    def create_cron_job_history(cls: Any, cron_job: CronJob, last_run: datetime, runtime: float, success: bool) -> 'CronJobHistory':
        return cls.objects.create(
            cron_job=cron_job,
            last_runtime=last_run,
            runtime=runtime,
            success=success,
            job_name=cron_job.job_name
        )

    @classmethod
    def set_last_run_time(cls: Any, history_id: int, last_run: datetime) -> None:
        cron_history = cls.objects.get(id=history_id)
        cron_history.last_runtime = last_run
        cron_history.save()

    @classmethod
    def set_runtime(cls: Any, history_id: int, runtime: int) -> None:
        cron_history = cls.objects.get(id=history_id)
        cron_history.runtime = runtime
        cron_history.save()

    @classmethod
    def set_status(cls: Any, history_id: int, status: str) -> None:
        cron_history = cls.objects.get(id=history_id)
        cron_history.status = status
        cron_history.save()


class COOPBlogPost(ModelMixins.BaseModelWithoutBy):
    class BlogTypes(models.TextChoices):
        RAB = 'RAB', 'RAB'
        MGO = 'MGO', 'MGO'

    plan_url = models.URLField(max_length=255, null=True, blank=True)
    wordpress_post_id = models.BigIntegerField(null=False, blank=False)
    brand = models.CharField(max_length=255, null=False, blank=False)
    print_url = models.URLField(max_length=255, null=True, blank=True)
    post_date = models.DateField(null=False, blank=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    plan_image = models.URLField(max_length=255, null=True, blank=True)
    paragraph1 = models.TextField(null=True, blank=True)
    paragraph2 = models.TextField(null=True, blank=True)
    paragraph3 = models.TextField(null=True, blank=True)
    paragraph4 = models.TextField(null=True, blank=True)
    # is_success = models.BooleanField(default=False, null=False)
    blog_type = models.CharField(null=False, blank=False, choices=BlogTypes.choices, max_length=5)

    class Meta:
        # todo the post id should be enough to determine uniqueness.
        db_table = "blog_post"
        verbose_name_plural = "Blog Posts"
        constraints = [
            models.UniqueConstraint(fields=['brand', 'title', 'post_date'], name='unique_post_constraint')
        ]

    def __str__(self) -> str:
        return self.title or "WordPressPost"

    def to_dict(self) -> dict:
        return model_to_dict(self)


class COOPBlogRipJobHistory(ModelMixins.BaseModelWithoutBy):
    job_start = models.DateTimeField(auto_now_add=True)
    job_end = models.DateTimeField(auto_now_add=True)
    errors = models.TextField()
    # Many-to-many field to store blog posts processed by this job
    blog_posts = models.ManyToManyField(COOPBlogPost, related_name="blog_rip_job_posts_processed")

    class Meta:
        db_table = "blog_rip_job_history"
        verbose_name_plural = "Blog Rip Job History"

    def __str__(self):
        return f"Job {self.id} at {self.timestamp}"

    def count_processed_posts(self) -> int:
        return self.blog_posts.count()

    def time_elapsed(self):
        if not self.job_start:
            return "No start time."
        if self.job_end:
            delta = self.job_end - self.job_start
            return str(delta)
        return "In progress."
