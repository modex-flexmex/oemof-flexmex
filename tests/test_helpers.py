import os
import pytest

from oemof_flexmex.helpers import check_if_csv_dirs_equal

basepath = os.path.abspath(os.path.dirname(__file__))


def test_check_equal_dirs():
    r"""
    Compares two csv dirs and passes as they are equal.
    """
    dir_a = os.path.join(basepath, '_files/csv_dirs/dir_default')
    dir_b = os.path.join(basepath, '_files/csv_dirs/dir_same')

    check_if_csv_dirs_equal(dir_a, dir_b)


def test_check_dirs_with_different_files():
    r"""
    Compares two csv dirs and fails as the directories contain
    different files.
    """
    dir_a = os.path.join(basepath, '_files/csv_dirs/dir_default')
    dir_b = os.path.join(basepath, '_files/csv_dirs/dir_diff_files')

    with pytest.raises(AssertionError):
        check_if_csv_dirs_equal(dir_a, dir_b)


def test_check_dirs_with_different_file_contents():
    r"""
    Compares two csv dirs and fails as file contents differ.
    """
    dir_a = os.path.join(basepath, '_files/csv_dirs/dir_default')
    dir_b = os.path.join(basepath, '_files/csv_dirs/dir_diff_content')

    with pytest.raises(AssertionError):
        check_if_csv_dirs_equal(dir_a, dir_b)
