import pytest


def pytest_addoption(parser):
    parser.addoption("--url", dest="url", help="PyLink url connection.")

def pytest_generate_tests(metafunc):
    if 'url' in metafunc.funcargnames:
        if not metafunc.config.option.url:
            pytest.skip("test requires url connection")
        else:
            metafunc.parametrize("url", [metafunc.config.option.url])
