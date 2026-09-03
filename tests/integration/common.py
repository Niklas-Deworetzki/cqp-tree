from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel


class TestedBackend(StrEnum):
    NO_SKETCH_ENGINE = 'noske'
    CORPUS_WORKBENCH = 'cwb'


class TestCase(BaseModel):
    description: str
    input: str
    noske: list[int] | int | None = None
    cwb: list[int] | int | None = None
    translator: str | None = None


def _make_test_case(case: TestCase, backend: TestedBackend):
    expected_results = None
    match backend:
        case TestedBackend.NO_SKETCH_ENGINE:
            expected_results = case.noske
        case TestedBackend.CORPUS_WORKBENCH:
            expected_results = case.cwb

    if expected_results is None:
        return None

    def generated_test_case(self):
        actual_results = self.do_query(case.input, case.translator)

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

    return generated_test_case


def import_test_cases(dst_class: type, backend: TestedBackend):
    """
    Generate test cases from the test case definition file and inject them into a unittest class.
    """
    definition_file = Path(__file__).parent / 'test-cases.yml'

    cases = []
    with definition_file.open('r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        cases = [TestCase.model_validate(definition) for definition in data]

    for case_number, case in enumerate(cases, start=1):
        test_name = case.description.replace(' ', '_')
        if test_case := _make_test_case(case, backend):
            setattr(dst_class, f'test_{case_number}_{test_name}', test_case)
