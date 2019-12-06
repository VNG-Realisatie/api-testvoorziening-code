import json
import array
import itertools
import uuid

from datetime import datetime

from tinymce.models import HTMLField

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ordered_model.models import OrderedModel
from django.core.files.base import ContentFile
from filer.fields.file import FilerFileField

from vng.accounts.models import User
import vng.postman.utils as postman
from vng.postman.choices import ResultChoices

from ..utils import choices


class API(models.Model):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        permissions = (
            ('list_scenario_for_api', _('View the list of test scenarios for this API')),
            ('create_scenario_for_api', _('Create a test scenario for this API')),
            ('update_scenario_for_api', _('Update a test scenario for this API')),
            ('delete_scenario_for_api', _('Delete a test scenario for this API')),
            ('update_environment_for_api', _('Update an environment for this API')),
        )

class TestScenario(models.Model):

    name = models.CharField(_('name'), max_length=200, unique=True, help_text=_(
        "The name of the test scenario"
    ))
    authorization = models.CharField(_('Authorization'), max_length=20, choices=choices.AuthenticationChoices.choices, default=choices.AuthenticationChoices.jwt)
    description = HTMLField(help_text=_("The description of this test scenario"))
    active = models.BooleanField(blank=True, default=True, help_text=_(
        "Indicates whether this test scenario can be used via the web interface and the API"
    ))
    public_logs = models.BooleanField(blank=True, default=True, help_text=_(
        "When enabled, the HTML and JSON logs generated by Newman for this TestScenario will be publicly available."
    ))
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, help_text=_(
        "The universally unique identifier of this test scenario"
    ))
    api = models.ForeignKey(API, on_delete=models.PROTECT, null=True, blank=True, help_text=_(
        "The API to which this test scenario belongs"
    ))

    def __str__(self):
        return self.name

    def jwt_enabled(self):
        return self.authorization == choices.AuthenticationChoices.jwt

    def no_auth(self):
        return self.authorization == choices.AuthenticationChoices.no_auth

    def custom_header(self):
        return self.authorization == choices.AuthenticationChoices.header

    class Meta:
        ordering = ('name',)


class TestScenarioUrl(models.Model):

    name = models.CharField(_('name'), max_length=200, help_text=_(
        "The name of the variable"
    ))
    test_scenario = models.ForeignKey(TestScenario, on_delete=models.CASCADE, help_text=_(
        "The test scenario to which this variable is linked"
    ))
    url = models.BooleanField(default=True, help_text=_('''When enabled a single-line field is shown to the user
    when starting a session. When disabled a multi-line field is shown.'''))
    hidden = models.BooleanField(default=False, help_text=_(
        "When enabled, the value of this field will not be shown on detail pages"
    ))
    placeholder = models.TextField(blank=True, default='https://www.example.com', help_text=_(
        "The default value that will be used for this variable"
    ))

    def __str__(self):
        return '{} {}'.format(self.name, self.test_scenario)


class PostmanTest(OrderedModel):

    order_with_respect_to = 'test_scenario'
    name = models.CharField(max_length=150, help_text=_(
        "The name of the Postman test suite"
    ))
    version = models.CharField(max_length=20, default='1.0.0', help_text=_(
        """Indicates the version of the Postman test suite, allowing for different
        versions under the same name
        """
    ))
    test_scenario = models.ForeignKey(TestScenario, on_delete=models.CASCADE, help_text=_(
        "The name of the test scenario to which this Postman test is linked"
    ))
    # validation_file = FilerFileField(null=True, blank=True, default=None, on_delete=models.SET_NULL, help_text=_(
    #     "The actual file containing the Postman collection"
    # ))
    validation_file = models.FileField(null=True, blank=True, default=None, help_text=_(
        "The actual file containing the Postman collection"
    ))
    published_url = models.URLField(null=True, blank=True, help_text=_(
        "The URL pointing to the published collection on the Postman website"
    ))

    class Meta(OrderedModel.Meta):
        unique_together = ('name', 'version',)

    @property
    def valid_file(self):
        if hasattr(self, 'valid_file_cache'):
            return self.valid_file_cached
        else:
            with open(self.validation_file.path) as infile:
                cache = json.load(infile)
                self.valid_file_cached = cache
            return cache

    @property
    def filename(self):
        if self.validation_file:
            return self.validation_file.name.split('/')[-1]
        return ''

    def __str__(self):
        return '{} {}'.format(self.test_scenario, self.validation_file)

class Environment(models.Model):
    name = models.CharField(max_length=100, help_text=_("The name of this environment"))
    test_scenario = models.ForeignKey(TestScenario, on_delete=models.CASCADE, help_text=_(
        ""
    ))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, help_text=_(
        "The user that created this environment"
    ))
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, help_text=_(
        "The universally unique identifier of this environment"
    ))
    supplier_name = models.CharField(max_length=100, blank=True, default="", help_text=_(
        "Name of the supplier of the software product"
    ))
    software_product = models.CharField(max_length=100, blank=True, default="", help_text=_(
        "Name of the software tested by tests for this environment"
    ))
    product_role = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        unique_together = ('name', 'test_scenario', 'user',)

    def __str__(self):
        return '{} - {}'.format(self.test_scenario.name, self.name)

    @property
    def last_run(self):
        latest = self.serverrun_set.exclude(stopped=None).order_by('-stopped').first()
        return getattr(latest, 'stopped', None)

    @property
    def last_started_at(self):
        last_started = self.serverrun_set.order_by('-started').first()
        return getattr(last_started, 'started', None)


class ScheduledTestScenario(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, help_text=_(
        "The universally unique identifier of this scheduled test scenario, needed to retrieve the badge"
    ))
    environment = models.OneToOneField(Environment, null=True, blank=True, on_delete=models.CASCADE, help_text=_(
        "The environment that will be used for provider runs of this scheduled scenario"
    ))
    active = models.BooleanField(default=True, help_text=_(
        "Indicates whether this schedule is still active or not"
    ))

    def __str__(self):
        return '{} - {}'.format(self.environment.test_scenario, self.environment.name)

    @property
    def last_run(self):
        server_runs = self.serverrun_set.order_by('-id')
        if server_runs:
            return server_runs.first().stopped
        return None

class ServerRun(models.Model):

    test_scenario = models.ForeignKey(TestScenario, on_delete=models.CASCADE, help_text=_(
        "The test scenario for which this provider run was executed"
    ))
    scheduled_scenario = models.ForeignKey(
        ScheduledTestScenario, on_delete=models.CASCADE,
        null=True, blank=True, help_text=_("The scheduled test scenario for which this provider run was executed")
    )
    environment = models.ForeignKey(Environment, null=True, blank=True, on_delete=models.CASCADE, help_text=_(
        "The environment that will be used for this provider run"
    ))
    started = models.DateTimeField(_('Started at'), default=timezone.now, help_text=_(
        "The time at which the provider run was started"
    ))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, help_text=_(
        "The user that started this provider run"
    ))
    stopped = models.DateTimeField(_('Stopped at'), null=True, default=None, blank=True, help_text=_(
        "The time at which the provider run was stopped"
    ))
    status = models.CharField(
        max_length=20,
        choices=choices.StatusWithScheduledChoices.choices,
        default=choices.StatusWithScheduledChoices.starting,
        help_text=_("Indicates the status of this provider run")
    )
    client_id = models.TextField(default=None, null=True, blank=True, help_text=_(
        "If the test scenario requires JWT authentication, this field will be used to construct a JWT"
    ))
    secret = models.TextField(default=None, null=True, blank=True, help_text=_(
        "If the test scenario requires JWT authentication, this field will be used to construct a JWT"
    ))
    percentage_exec = models.IntegerField(default=None, null=True, blank=True, help_text=_(
        "Indicates what percentage of the provider run has been executed"
    ))
    status_exec = models.TextField(default=None, null=True, blank=True, help_text=_(
        "Indicates the status of execution of the provider run"
    ))
    scheduled = models.BooleanField(default=False, help_text=_(
        "If enabled, this provider run will be executed every day at midnight"
    ))
    build_version = models.CharField(max_length=100, blank=True, default="")
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, help_text=_(
        "The universally unique identifier of this provider run, needed to retrieve the badge"
    ))

    def __str__(self):
        return "{} - {}".format(self.started, self.status)

    def is_stopped(self):
        return self.status == choices.StatusChoices.stopped

    def is_running(self):
        return self.status == choices.StatusChoices.running

    def is_error(self):
        return self.status == choices.StatusChoices.error_deploy

    def get_execution_result(self):
        ptr_set = self.postmantestresult_set.all()
        if len(ptr_set) == 0:
            success = None
        else:
            success = True
            for ptr in ptr_set:
                if ptr.is_success() == 0:
                    success = None
                elif ptr.is_success() == -1 and success is not None:
                    success = False
        return success

    def get_all_call_results(self):
        success = 0
        failure = 0
        for test_result in self.postmantestresult_set.all():
            positive, negative = test_result.get_call_results()
            success += positive
            failure += negative
        return success, failure


class PostmanTestResult(models.Model):

    postman_test = models.ForeignKey(PostmanTest, on_delete=models.CASCADE, help_text=_(
        "The Postman test which this result belongs to"
    ))
    log = models.FileField(settings.MEDIA_FOLDER_FILES['servervalidation_log'], blank=True, null=True, default=None, help_text=_(
        "The HTML log generated by Newman"
    ))
    log_json = models.FileField(settings.MEDIA_FOLDER_FILES['servervalidation_log'], blank=True, null=True, default=None, help_text=_(
        "The JSON log generated by Newman"
    ))
    server_run = models.ForeignKey(ServerRun, on_delete=models.CASCADE, help_text=_(
        "The provider run which this result belongs to"
    ))
    status = models.CharField(max_length=10, choices=ResultChoices.choices, default=None, null=True, help_text=_(
        "Indicates whether all test passed or not"
    ))

    def __str__(self):
        if self.status is None:
            return '{}'.format(self.__dict__)
        else:
            return '{} - {}'.format(self.pk, self.status)

    def is_success(self):
        _, negative = self.get_call_results()
        status = ResultChoices.success if not negative else ResultChoices.failed
        if status == ResultChoices.success:
            return 1
        if status == ResultChoices.failed:
            return -1
        else:
            return 0

    def display_log(self):
        if self.log:
            with open(self.log.path) as fp:
                return fp.read().replace('\n', '<br>')

    def display_log_json(self):
        if self.log:
            with open(self.log_json.path) as fp:
                return fp.read()

    def get_json_obj_info(self):
        if hasattr(self, 'status_saved'):
            return self.status_saved

        with open(self.log_json.path) as jfile:
            f = json.load(jfile)
            del f['run']['executions']
            a = int(f['run']['timings']['started'])
            f['run']['timings']['started'] = (datetime.utcfromtimestamp(int(f['run']['timings']['started']) / 1000)
                                              .strftime('%I:%M %p'))

            self.status_saved = f
            return f

    def get_json_obj(self):
        return postman.get_json_obj_file(self.log_json.path) if self.log_json else []

    def save_json(self, filename, file):
        content = json.load(file)
        for execution in content['run']['executions']:
            try:
                buffer = execution['response']['stream']['data']
                del execution['response']['stream']
                execution['response']['body'] = json.loads(array.array('B', buffer).tostring())
            except:
                pass
        self.log_json.save(filename, ContentFile(json.dumps(content)))

    def get_outcome_html(self):
        with open(self.log.path) as f:
            for line in f:
                if 'Total failed tests' in line:
                    if '0' in line:
                        return ResultChoices.success
        return ResultChoices.failed

    def get_outcome_json(self):
        with open(self.log_json.path) as jfile:
            return postman.get_outcome_json(jfile, file=True)

    def get_call_results(self):
        positive, negative = 0, 0
        for call in self.get_json_obj():
            # Count the failed and successful assertions
            if 'assertions' in call:
                for assertion in call['assertions']:
                    if 'error' in assertion:
                        negative += 1
                    else:
                        positive += 1
        return positive, negative

    def get_aggregate_results(self):
        passed, error = 0, 0
        positive, negative = 0, 0
        for call in self.get_json_obj():
            success = True
            if not postman.get_call_result(call):
                success = False
            if 'assertions' in call:
                for assertion in call['assertions']:
                    if 'error' in assertion:
                        error += 1
                        success = False
                    else:
                        passed += 1
            if success:
                positive += 1
            else:
                negative += 1
        return {
            'assertions': {
                'passed': passed,
                'failed': error,
                'total': error + passed
            },
            'calls': {
                'success': positive,
                'failed': negative,
                'total': negative + positive
            }
        }

    def get_assertions_details(self):
        passed, error = 0, 0
        for call in self.get_json_obj():
            if 'assertions' in call:
                for assertion in call['assertions']:
                    if 'error' in assertion:
                        error += 1
                    else:
                        passed += 1
        return passed, error

    def positive_call_result(self):
        return self.get_call_results()[0]

    def negative_call_result(self):
        return self.get_call_results()[1]

    def get_call_results_list(self):
        return [postman.get_call_result(call) for call in self.get_json_obj()]


class Endpoint(models.Model):

    test_scenario_url = models.ForeignKey(TestScenarioUrl, on_delete=models.CASCADE, help_text=_(
        "The test scenario variable to which this endpoint belongs"
    ))
    url = models.TextField(help_text=_("The value of the variable"))
    jwt = models.TextField(null=True, default=None, blank=True)
    server_run = models.ForeignKey(ServerRun, null=True, blank=True, on_delete=models.CASCADE, help_text=_(
        "The provider run to which this endpoint belongs"
    ))
    environment = models.ForeignKey(Environment, null=True, blank=True, on_delete=models.CASCADE, help_text=_(
        "The environment to which this endpoint belongs"
    ))


class ServerHeader(models.Model):

    server_run = models.ForeignKey(ServerRun, null=True, blank=True, on_delete=models.CASCADE, help_text=_(
        "The provider run for which this header was used"
    ))
    environment = models.ForeignKey(Environment, null=True, blank=True, on_delete=models.CASCADE, help_text=_(
        "The environment to which this header belongs"
    ))
    header_key = models.TextField(help_text=_("The name of the HTTP header"))
    header_value = models.TextField(help_text=_("The value of the HTTP header"))
