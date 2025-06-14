import subprocess
import os
import pytest
from pathlib import Path

SCRIPT = "./ensure_file.py"
TESTFILE = "/tmp/ensure_python_test.conf"

@pytest.fixture(autouse=True)
def clean_file():
    if os.path.exists(TESTFILE):
        os.remove(TESTFILE)
    yield
    if os.path.exists(TESTFILE):
        os.remove(TESTFILE)

def run(args, input=None):
    proc = subprocess.run(
        [SCRIPT] + args,
        input=input,
        text=True,
        capture_output=True
    )
    return proc

def readfile():
    return Path(TESTFILE).read_text(encoding="utf-8")

# -- LINE tests --

def test_ensure_line_on_empty_file():
    Path(TESTFILE).write_text("")
    result = run([TESTFILE, "--line", "new_line = 1", "-f", "-q"])
    assert result.returncode == 0
    assert readfile() == "new_line = 1\n"

def test_ensure_line_first_last_middle():
    Path(TESTFILE).write_text("original_top\nmiddle\noriginal_bottom\n")

    result = run([TESTFILE, "--line", "hello = world", "-f", "-q"])
    assert result.returncode == 0

    lines = readfile().splitlines()
    assert lines == [
        "original_top",
        "middle",
        "original_bottom",
        "hello = world"
    ]

def test_ensure_line_idempotent_and_I():
    Path(TESTFILE).write_text("alpha\n")
    result = run([TESTFILE, "--line", "alpha", "-q"])
    assert result.returncode == 4

    result2 = run([TESTFILE, "--line", "alpha", "-q", "-I"])
    assert result2.returncode == 0
    assert readfile() == "alpha\n"

# -- REPLACE exact line --

def test_replace_line_exact():
    Path(TESTFILE).write_text("loglevel = debug\n")
    result = run([TESTFILE, "--replace", "loglevel = debug", "loglevel = warning", "-f", "-q"])
    assert result.returncode == 0
    assert readfile() == "loglevel = warning\n"

def test_replace_line_already_correct():
    Path(TESTFILE).write_text("x = y\n")
    result = run([TESTFILE, "--replace", "x = y", "x = y", "-q"])
    assert result.returncode == 4

    result2 = run([TESTFILE, "--replace", "x = y", "x = y", "-q", "-I"])
    assert result2.returncode == 0
    assert readfile() == "x = y\n"

def test_replace_line_no_match():
    Path(TESTFILE).write_text("something else\n")
    result = run([TESTFILE, "--replace", "doesnot=exist", "new=val", "-q"])
    assert result.returncode == 3
    assert readfile() == "something else\n"

# -- REPLACE regex --

def test_replace_re_changes_line():
    Path(TESTFILE).write_text("vm.swappiness = 10\n")
    result = run([TESTFILE, "--replace-re", r"vm\.swappiness = \d+", "vm.swappiness = 11", "-f", "-q"])
    assert result.returncode == 0
    assert readfile() == "vm.swappiness = 11\n"

def test_replace_re_already_correct_and_I():
    Path(TESTFILE).write_text("vm.swappiness = 11\n")
    result = run([TESTFILE, "--replace-re", r"vm\.swappiness = \d+", "vm.swappiness = 11", "-q"])
    assert result.returncode == 4

    result2 = run([TESTFILE, "--replace-re", r"vm\.swappiness = \d+", "vm.swappiness = 11", "-q", "-I"])
    assert result2.returncode == 0
    assert readfile() == "vm.swappiness = 11\n"

def test_replace_re_no_match():
    Path(TESTFILE).write_text("foo=bar\n")
    result = run([TESTFILE, "--replace-re", r"nosuchpattern", "noop", "-q"])
    assert result.returncode == 3
    assert readfile() == "foo=bar\n"

def test_replace_re_with_context():
    Path(TESTFILE).write_text("prefix = true\nvm.swappiness = 42\nsuffix = yes\n")
    result = run([TESTFILE, "--replace-re", r"vm\.swappiness = \d+", "vm.swappiness = 13", "-f", "-q"])
    assert result.returncode == 0
    lines = readfile().splitlines()
    assert lines == [
        "prefix = true",
        "vm.swappiness = 13",
        "suffix = yes"
    ]

def test_replace_first_and_last_line():
    Path(TESTFILE).write_text("top=1\nmid=2\nbot=3\n")
    r1 = run([TESTFILE, "--replace", "top=1", "top=9", "-f", "-q"])
    r2 = run([TESTFILE, "--replace", "bot=3", "bot=9", "-f", "-q"])
    assert r1.returncode == 0
    assert r2.returncode == 0
    assert readfile() == "top=9\nmid=2\nbot=9\n"

# -- BLOCK tests --

def test_block_insert_from_empty():
    Path(TESTFILE).write_text("")
    result = run([
        TESTFILE,
        "--block", "one", "two", "--start", "# ST", "--end", "# EN", "-f", "-q"
    ])
    assert result.returncode == 0
    assert readfile() == "# ST\none\ntwo\n# EN\n"

def test_block_with_context():
    Path(TESTFILE).write_text("before\n# BEGIN\nA\nB\n# END\nafter\n")

    result = run([
        TESTFILE,
        "--block", "A", "B", "--start", "# BEGIN", "--end", "# END", "-q"
    ])
    assert result.returncode == 4

    result2 = run([
        TESTFILE,
        "--block", "A", "CHANGED", "--start", "# BEGIN", "--end", "# END", "-f", "-q"
    ])
    assert result2.returncode == 0

    lines = readfile().splitlines()
    assert lines == [
        "before",
        "# BEGIN",
        "A",
        "CHANGED",
        "# END",
        "after"
    ]

def test_insert_block_top_bottom_context():
    Path(TESTFILE).write_text("AAA\nBBB\nCCC\n")
    result = run([
        TESTFILE,
        "--block", "SET", "UP", "--start", "# START", "--end", "# STOP", "-f", "-q"
    ])
    assert result.returncode == 0
    lines = readfile().splitlines()
    assert lines[:3] == ["AAA", "BBB", "CCC"]
    assert lines[3:7] == ["# START", "SET", "UP", "# STOP"]

