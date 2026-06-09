import pytest

from kmap import logging
from kmap.command.run_all import progress as run_all_progress_module


def test_run_all_progress_sets_and_restores_progress_state():
    previous_mode = logging.set_output_mode("lines")
    previous_progress = logging.set_active_progress(None)
    try:
        with run_all_progress_module.run_all_progress(enabled=True, total=3) as progress:
            assert logging.output_mode() == "progress"
            assert logging._ACTIVE_PROGRESS is progress
            assert progress.total == 3

        assert logging.output_mode() == "lines"
        assert logging._ACTIVE_PROGRESS is None
    finally:
        logging.set_active_progress(previous_progress)
        logging.set_output_mode(previous_mode)


def test_run_all_progress_restores_state_after_exception():
    previous_mode = logging.set_output_mode("lines")
    previous_progress = logging.set_active_progress(None)
    try:
        with pytest.raises(RuntimeError, match="boom"), run_all_progress_module.run_all_progress(enabled=True, total=1):
            raise RuntimeError("boom")

        assert logging.output_mode() == "lines"
        assert logging._ACTIVE_PROGRESS is None
    finally:
        logging.set_active_progress(previous_progress)
        logging.set_output_mode(previous_mode)


def test_run_all_progress_lines_mode_does_not_install_active_progress():
    previous_mode = logging.set_output_mode("progress")
    previous_progress = logging.set_active_progress(None)
    try:
        with run_all_progress_module.run_all_progress(enabled=False, total=2) as progress:
            assert logging.output_mode() == "lines"
            assert logging._ACTIVE_PROGRESS is None
            assert progress.enabled is False

        assert logging.output_mode() == "progress"
        assert logging._ACTIVE_PROGRESS is None
    finally:
        logging.set_active_progress(previous_progress)
        logging.set_output_mode(previous_mode)


def test_progress_update_rerenders_without_advancing(capsys):
    progress = logging.ProgressBar(total=2, enabled=True)

    progress.start("starting")
    progress.update("fetch workloads")

    assert progress.current == 0
    assert progress.last_message == "fetch workloads"
    assert "fetch workloads" in capsys.readouterr().err
