from django.test import TestCase

from vng.design_rules.tasks.api_20 import run_api_20_test_rules

from ..factories import DesignRuleResultFactory, DesignRuleSessionFactory
from ...choices import DesignRuleChoices
from ...models import DesignRuleResult


class Api20Tests(TestCase):
    def test_design_rule_already_exists(self):
        session = DesignRuleSessionFactory(test_suite__api_endpoint="https://maykinmedia.nl/")
        pre_result = DesignRuleResultFactory(design_rule=session, rule_type=DesignRuleChoices.api_20)

        result = run_api_20_test_rules(session, "https://maykinmedia.nl/")
        self.assertEqual(DesignRuleResult.objects.count(), 1)
        self.assertEqual(pre_result.pk, result.pk)

    def test_no_version(self):
        session = DesignRuleSessionFactory(test_suite__api_endpoint="https://maykinmedia.nl/")

        result = run_api_20_test_rules(session, "https://maykinmedia.nl/")
        self.assertEqual(DesignRuleResult.objects.count(), 1)
        self.assertFalse(result.success)
        self.assertEqual(result.errors, "The api endpoint does not contain a 'v*' in the url")

    def test_version_at_the_end(self):
        session = DesignRuleSessionFactory(test_suite__api_endpoint="https://maykinmedia.nl/")

        result = run_api_20_test_rules(session, "https://maykinmedia.nl/v1")
        self.assertEqual(DesignRuleResult.objects.count(), 1)
        self.assertTrue(result.success)
        self.assertEqual(result.errors, "")

    def test_version_in_the_path(self):
        session = DesignRuleSessionFactory(test_suite__api_endpoint="https://maykinmedia.nl/")

        result = run_api_20_test_rules(session, "https://maykinmedia.nl/v1/something")
        self.assertEqual(DesignRuleResult.objects.count(), 1)
        self.assertTrue(result.success)
        self.assertEqual(result.errors, "")

    def test_version_in_the_url(self):
        session = DesignRuleSessionFactory(test_suite__api_endpoint="https://maykinmedia.nl/")

        result = run_api_20_test_rules(session, "https://maykinmediav1.nl/something")
        self.assertEqual(DesignRuleResult.objects.count(), 1)
        self.assertFalse(result.success)
        self.assertEqual(result.errors, "The api endpoint does not contain a 'v*' in the url")

    def test_version_with_minor_version(self):
        session = DesignRuleSessionFactory(test_suite__api_endpoint="https://maykinmedia.nl/")

        result = run_api_20_test_rules(session, "https://maykinmedia.nl/v1.1")
        self.assertEqual(DesignRuleResult.objects.count(), 1)
        self.assertFalse(result.success)
        self.assertEqual(result.errors, "The api endpoint contains more than the major version number in the URI")

    def test_version_with_trailing_text(self):
        session = DesignRuleSessionFactory(test_suite__api_endpoint="https://maykinmedia.nl/")

        result = run_api_20_test_rules(session, "https://maykinmedia.nl/v1test")
        self.assertEqual(DesignRuleResult.objects.count(), 1)
        self.assertFalse(result.success)
        self.assertEqual(result.errors, "The api endpoint does not contain a 'v*' in the url")
