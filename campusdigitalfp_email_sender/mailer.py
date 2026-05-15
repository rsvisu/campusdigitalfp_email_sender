import logging
import smtplib
import ssl
from email.message import EmailMessage
from smtplib import SMTPAuthenticationError, SMTPConnectError, SMTPServerDisconnected
from typing import List, NamedTuple, Tuple

logger = logging.getLogger("campusdigitalfp_email_sender")

SmtpAccount = Tuple[str, str]  # (user, password)


class SendResult(NamedTuple):
    ok: bool
    error: str = ""


def send_email(
    smtp_host: str,
    smtp_port: int,
    accounts: List[SmtpAccount],
    to: str,
    subject: str,
    html: str,
    from_name: str = "",
    start_idx: int = 0,
) -> Tuple[SendResult, int]:
    """Envía el e-mail rotando cuentas desde start_idx si alguna falla.

    Devuelve (SendResult, idx_cuenta_usada).
    Rota en SMTPAuthenticationError, SMTPConnectError, SMTPServerDisconnected y OSError.
    Cualquier otro error se considera fallo del mensaje, no de la cuenta.
    """
    for i in range(len(accounts)):
        idx = (start_idx + i) % len(accounts)
        user, password = accounts[idx]

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{user}>" if from_name else user
        msg["To"] = to
        msg.set_content("Tu cliente de correo no soporta HTML.")
        msg.add_alternative(html, subtype="html")

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                server.login(user, password)
                server.send_message(msg)
            logger.info("Envío OK -> %s (cuenta: %s)", to, user)
            return SendResult(ok=True), idx
        except (SMTPAuthenticationError, SMTPConnectError, SMTPServerDisconnected, OSError) as exc:
            logger.warning("Cuenta %s no disponible, rotando: %s", user, exc)
            continue
        except Exception as exc:
            logger.error("Envío FALLIDO -> %s : %s", to, exc)
            return SendResult(ok=False, error=str(exc)), idx

    logger.error("Todas las cuentas SMTP fallaron para %s", to)
    return SendResult(ok=False, error="Todas las cuentas SMTP fallaron"), start_idx
