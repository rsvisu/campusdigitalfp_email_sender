import pytest
from campusdigitalfp_email_sender.cli import build_parser
from unittest.mock import patch, MagicMock


def test_parser_add():
    parser = build_parser()
    args = parser.parse_args(["--add", "a@b.com;Sub;<h1>Hi</h1>"])
    assert args.add == "a@b.com;Sub;<h1>Hi</h1>"


@patch("campusdigitalfp_email_sender.cli.add_email_to_csv")
def test_cli_add(mock_add):
    from campusdigitalfp_email_sender.cli import main
    with patch("sys.argv", ["campusdigitalfp_email_sender",
                            "--smtp-user", "test@mail.com",
                            "--smtp-password", "testpass",
                            "--add", "a@b.com;Sub;<h1>Hi</h1>"]):
        main()
    mock_add.assert_called_once_with("a@b.com", "Sub", "<h1>Hi</h1>", mailing_dir="mailing")