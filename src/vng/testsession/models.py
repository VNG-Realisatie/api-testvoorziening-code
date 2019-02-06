import json
import uuid
import re

from django.conf import settings
from django.core.files import File
from django.db import models
from django.utils import timezone
from django.urls import reverse

from ordered_model.models import OrderedModel

from vng.accounts.models import User

from ..utils import choices


class SessionType(models.Model):

    name = models.CharField(max_length=200, unique=True)
    standard = models.CharField(max_length=200, null=True)
    role = models.CharField(max_length=200, null=True)
    application = models.CharField(max_length=200, null=True)
    version = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name


class TestSession(models.Model):
    test_result = models.FileField(settings.MEDIA_FOLDER_FILES['testsession_log'], blank=True, null=True, default=None)
    json_result = models.TextField(blank=True, null=True, default=None)

    def save_test(self, file):
        name_file = str(uuid.uuid4())
        django_file = File(file)
        self.test_result.save(name_file, django_file)

    def save_test_json(self, file):
        text = file.read().replace('\n', '')
        self.json_result = text

    def display_test_result(self):
        if self.test_result:
            with open(self.test_result.path) as fp:
                return fp.read().replace('\n', '<br>')


class VNGEndpoint(models.Model):

    port = models.PositiveIntegerField(default=8080)
    url = models.URLField(max_length=200)
    name = models.CharField(max_length=200)
    docker_image = models.CharField(max_length=200, blank=True, null=True, default=None)
    session_type = models.ForeignKey(SessionType, on_delete=models.CASCADE)
    test_file = models.FileField(settings.MEDIA_FOLDER_FILES['test_session'], blank=True, null=True, default=None)

    def __str__(self):
        return self.name


class ScenarioCase(OrderedModel):

    url = models.CharField(max_length=200)
    http_method = models.CharField(max_length=20, choices=choices.HTTPMethodChoiches.choices, default=choices.HTTPMethodChoiches.GET)
    vng_endpoint = models.ForeignKey(VNGEndpoint, on_delete=models.CASCADE)

    def __str__(self):
        return '{} - {}'.format(self.http_method, self.url)


class Session(models.Model):

    name = models.CharField(max_length=30, unique=True, null=True)
    session_type = models.ForeignKey(SessionType, on_delete=models.CASCADE)
    started = models.DateTimeField(default=timezone.now)
    stopped = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=choices.StatusChoices.choices, default=choices.StatusChoices.starting)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    build_version = models.TextField(blank=True, null=True, default=None)

    def __str__(self):
        if self.user:
            return "{} - {} - #{}".format(self.session_type, self.user.username, str(self.id))
        else:
            return "{} - #{}".format(self.session_type, str(self.id))

    def get_absolute_request_url(self, request):
        test_session_url = 'https://{}{}'.format(request.get_host(),
                                                 reverse('testsession:session_log', args=[self.id]))
        return test_session_url

    def is_stopped(self):
        return self.status == choices.StatusChoices.stopped

    def is_running(self):
        return self.status == choices.StatusChoices.running

    def is_starting(self):
        return self.status == choices.StatusChoices.starting

    def is_shutting_down(self):
        return self.status == choices.StatusChoices.shutting_down


class ExposedUrl(models.Model):

    exposed_url = models.CharField(max_length=200, unique=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    vng_endpoint = models.ForeignKey(VNGEndpoint, on_delete=models.CASCADE)
    test_session = models.ForeignKey(TestSession, blank=True, null=True, default=None, on_delete=models.CASCADE)

    def get_uuid_url(self):
        return re.search('([^/]+)', self.exposed_url).group(1)

    def __str__(self):
        return '{} {}'.format(self.session, self.vng_endpoint)


class SessionLog(models.Model):

    date = models.DateTimeField(default=timezone.now)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True)
    request = models.TextField(blank=True, null=True, default=None)
    response = models.TextField(blank=True, null=True, default=None)
    response_status = models.PositiveIntegerField(blank=True, null=True, default=None)

    def __str__(self):
        return '{} - {} - {}'.format(str(self.date), str(self.session),
                                     str(self.response_status))

    def request_path(self):
        return json.loads(self.request)['request']['path']

    def request_headers(self):
        return json.loads(self.request)['request']['header']

    def request_body(self):
        try:
            return json.loads(self.request)['request']['body']
        except:
            return ""

    def response_body(self):
        try:
            return json.loads(self.response)['response']['body']
        except:
            return ""


class Report(models.Model):
    class Meta:
        unique_together = ('scenario_case', 'session_log')

    scenario_case = models.ForeignKey(ScenarioCase, on_delete=models.CASCADE)
    session_log = models.ForeignKey(SessionLog, on_delete=models.CASCADE)
    result = models.CharField(max_length=20, choices=choices.HTTPCallChoiches.choices, default=choices.HTTPCallChoiches.not_called)

    def is_success(self):
        return self.result == choices.HTTPCallChoiches.success

    def is_failed(self):
        return self.result == choices.HTTPCallChoiches.failed

    def is_not_called(self):
        return self.result == choices.HTTPCallChoiches.not_called

    def __str__(self):
        return 'Case: {} - Log: {} - Result: {}'.format(self.scenario_case, self.session_log, self.result)
