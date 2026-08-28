import unittest
from pathlib import Path
from typing import Optional

import yaml
from playwright.sync_api import sync_playwright
from pydantic import BaseModel


class TestCase(BaseModel):
    description: str
    input: str
    expected: list[int] | int
    language: str | None = None


class TestNoskeUI(unittest.TestCase):

    def setUp(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch()
        self.page = self.browser.new_page()

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()

    def test_is_up(self):
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

    def test_query_results(self):
        definition_file = Path(__file__).parent / 'test-cases.yml'

        cases = []
        with definition_file.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            cases = [TestCase.model_validate(definition) for definition in data]

        for case_number, case in enumerate(cases, start=1):
            print(case)
            with self.subTest(msg=f'{case_number}: {case.description}'):
                actual_results = self.do_query(case.input, case.language)
                expected_results = case.expected

                if isinstance(expected_results, list):
                    self.assertIn(
                        actual_results,
                        expected_results,
                        f'Query expected to produce one of {expected_results} but got {actual_results} instead.',
                    )
                else:
                    self.assertEqual(
                        actual_results,
                        expected_results,
                        f'Query expected to produce {expected_results} but got {actual_results} instead.',
                    )

    def do_query(self, query: str, language: Optional[str] = None) -> int:
        self.page.goto(f'http://localhost:31495', wait_until='domcontentloaded')
        self.page.locator('#query-input-field').fill(query)
        if language:
            self.page.locator('#query-language-selection').select_option(value=language)
        self.page.locator('#submit-query').click()

        with self.page.context.expect_page() as expected_query_result_page:
            self.page.locator('#run-on-korp-link').click()

        query_result_page = expected_query_result_page.value

        while True:
            result = query_result_page.locator('span.size[data-tooltip="Number of hits"]').inner_text()
            result = result.strip()
            if not result.endswith('.'):
                result = result.replace(',', '')
                return int(result)
