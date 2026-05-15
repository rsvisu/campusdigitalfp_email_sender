import pytest
from campusdigitalfp_email_sender.mailer import send_email, SendResult
from unittest.mock import patch, MagicMock


ACCOUNTS = [("user@gmail.com", "pass")]


@patch("campusdigitalfp_email_sender.mailer.smtplib.SMTP_SSL")
def test_send_email_ok(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    res, idx = send_email("smtp.gmail.com", 465, ACCOUNTS, "to@example.com", "Test", "<h1>Hi</h1>")
    assert res.ok is True
    assert res.error == ""
    assert idx == 0
    mock_server.login.assert_called_once_with("user@gmail.com", "pass")
    mock_server.send_message.assert_called_once()


@patch("campusdigitalfp_email_sender.mailer.smtplib.SMTP_SSL")
def test_send_email_auth_fail(mock_smtp):
    from smtplib import SMTPAuthenticationError
    mock_smtp.return_value.__enter__.return_value.login.side_effect = SMTPAuthenticationError(535, "Auth error")
    res, idx = send_email("smtp.gmail.com", 465, ACCOUNTS, "to@example.com", "Test", "<h1>Hi</h1>")
    assert res.ok is False
    assert "Todas las cuentas" in res.error


@patch("campusdigitalfp_email_sender.mailer.smtplib.SMTP_SSL")
def test_send_email_rotates_to_second_account(mock_smtp):
    """Primera cuenta falla por auth, segunda funciona."""
    from smtplib import SMTPAuthenticationError
    accounts = [("bad@gmail.com", "wrong"), ("good@gmail.com", "correct")]

    mock_smtp.return_value.__enter__.return_value.login.side_effect = [
        SMTPAuthenticationError(535, "bad creds"),
        None,
    ]
    mock_smtp.return_value.__enter__.return_value.send_message = MagicMock()

    res, idx = send_email("smtp.gmail.com", 465, accounts, "to@example.com", "Test", "<h1>Hi</h1>")
    assert res.ok is True
    assert idx == 1
