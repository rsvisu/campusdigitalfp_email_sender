import pytest
import tempfile
from pathlib import Path
from campusdigitalfp_email_sender.cli import build_parser
from unittest.mock import patch, MagicMock, call


def test_parser_add():
    parser = build_parser()
    args = parser.parse_args(["--add", "a@b.com;Sub;<h1>Hi</h1>"])
    assert args.add == "a@b.com;Sub;<h1>Hi</h1>"


def test_parser_retry_defaults():
    parser = build_parser()
    args = parser.parse_args(["--send"])
    assert args.max_retries == 3
    assert args.retry_delay == 5.0


@patch("campusdigitalfp_email_sender.cli.add_email_to_csv")
def test_cli_add(mock_add):
    from campusdigitalfp_email_sender.cli import main
    with patch("sys.argv", ["campusdigitalfp_email_sender",
                            "--smtp-user", "test@mail.com",
                            "--smtp-password", "testpass",
                            "--add", "a@b.com;Sub;<h1>Hi</h1>"]):
        main()
    mock_add.assert_called_once_with("a@b.com", "Sub", "<h1>Hi</h1>", mailing_dir="mailing")


@patch("campusdigitalfp_email_sender.cli.time.sleep")
@patch("campusdigitalfp_email_sender.cli.send_email")
def test_auto_retry_on_failure(mock_send_email, mock_sleep):
    """Si el envío falla, reintenta max_retries veces antes de marcar como fallido."""
    from campusdigitalfp_email_sender.mailer import SendResult
    from campusdigitalfp_email_sender.cli import send_emails

    mock_send_email.return_value = (SendResult(ok=False, error="timeout"), 0)

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / "id_emails_01-01-2025.csv"
        csv_path.write_text("email;asunto;contenido\na@b.com;Sub;<h1>Hi</h1>\n", encoding="utf-8")

        args = MagicMock()
        args.retry_failed = None
        args.output_dir = tmp
        args.smtp_host = "smtp.gmail.com"
        args.smtp_port = 465
        args.from_name = ""
        args.max_retries = 3
        args.retry_delay = 0  # sin espera en tests

        send_emails(args, [("u@g.com", "p")])

    assert mock_send_email.call_count == 3  # 3 intentos
    assert mock_sleep.call_count == 2       # espera entre intentos 1→2 y 2→3