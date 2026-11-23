import unittest
from typing import Optional

from playwright.sync_api import sync_playwright

from tests.integration.common import import_test_cases, TestedBackend


class TestNoskeUI(unittest.TestCase):

    def setUp(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch()
        self.page = self.browser.new_page()

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()

    def test_application_is_healthy(self):
        for port, application in (
            (10070, 'NoSketch Engine'),
            (31495, 'CQP Tree'),
        ):
            response = self.page.goto(
                f'http://localhost:{port}',
                timeout=5000,
                wait_until='domcontentloaded',
            )

            self.assertIsNotNone(response, f'{application} did not start correctly.')
            self.assertTrue(response.ok, f'{application} did not start correctly.')

    def do_query(self, query: str, translator: Optional[str] = None) -> int:
        self.page.goto(f'http://localhost:31495', wait_until='domcontentloaded')
        self.page.locator('#query-input-field').fill(query)
        if translator:
            self.page.locator('#query-language-selection').select_option(value=translator)
        self.page.locator('#submit-query').click()

        with self.page.context.expect_page() as expected_query_result_page:
            self.page.locator('#run-on-korp-link').click()

        query_result_page = expected_query_result_page.value

        while True:
            result = query_result_page.locator(
                'span.size[data-tooltip="Number of hits"]'
            ).inner_text()
            result = result.strip()
            if not result.endswith('.'):
                result = result.replace(',', '')
                return int(result)


import_test_cases(TestNoskeUI, TestedBackend.NO_SKETCH_ENGINE)
