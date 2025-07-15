from clean_python_template.cli.main import hello


def test_hello(capsys):
    hello()
    captured = capsys.readouterr()
    assert "Hello World\n" == captured.out
