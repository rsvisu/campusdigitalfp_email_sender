import argparse
import logging
import sys
from pathlib import Path
from typing import List, Tuple

from .config import load_config, DEFAULT_CONFIG_FILE, SmtpAccount
from .logger import setup_logger
from .mailer import send_email
from .utils import (
    add_email_to_csv,
    DEFAULT_MAILING_DIR,
    get_today_csv_filename,
    read_csv_tasks,
    write_csv_with_status,
    rename_after_process,
    is_processed,
    is_failed,
)

logger = logging.getLogger("campusdigitalfp-email-sender")


def build_parser() -> argparse.ArgumentParser:
    cfg = load_config()

    parser = argparse.ArgumentParser(
        description="Gestiona/envía correos vía SMTP (Campus Virtual FP)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--add",
        type=str,
        help='Añadir fila CSV: "email;asunto;contenido"',
    )
    group.add_argument(
        "--send",
        action="store_true",
        help="Enviar pendientes del CSV del día",
    )
    group.add_argument(
        "--retry-failed",
        type=str,
        metavar="PATH",
        help="Re-intentar fallidos de un fichero *-FALLIDO.csv",
    )

    # SMTP
    parser.add_argument(
        "--smtp-host",
        default=cfg.get("smtp_host") or "smtp.gmail.com",
    )
    parser.add_argument(
        "--smtp-port",
        type=int,
        default=cfg.get("smtp_port") or 465,
    )
    parser.add_argument(
        "--smtp-user",
        default=cfg.get("smtp_user"),
        help="Cuenta SMTP única (alternativa a --smtp-accounts)",
    )
    parser.add_argument(
        "--smtp-password",
        default=cfg.get("smtp_password"),
        help="Contraseña para --smtp-user",
    )
    parser.add_argument(
        "--smtp-accounts",
        type=str,
        default=None,
        metavar="user1:pass1,user2:pass2",
        help="Lista de cuentas SMTP separadas por coma para rotación automática",
    )
    parser.add_argument(
        "--from-name",
        default=cfg.get("from_name") or "",
    )

    # paths / logging
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_MAILING_DIR,
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="email_sender.log",
    )

    return parser


def resolve_accounts(args, cfg: dict) -> List[SmtpAccount]:
    """Construye la lista de cuentas SMTP desde CLI o config."""
    # --smtp-accounts tiene prioridad
    if args.smtp_accounts:
        accounts = []
        for pair in args.smtp_accounts.split(","):
            pair = pair.strip()
            if ":" in pair:
                user, pwd = pair.split(":", 1)
                accounts.append((user.strip(), pwd.strip()))
        if accounts:
            return accounts

    # Cuentas del fichero de config
    if cfg.get("smtp_accounts"):
        return cfg["smtp_accounts"]

    # Compatibilidad: --smtp-user / --smtp-password
    if args.smtp_user and args.smtp_password:
        return [(args.smtp_user, args.smtp_password)]

    return []


def send_emails(args, accounts: List[SmtpAccount]) -> None:
    if args.retry_failed:
        if not is_failed(args.retry_failed):
            logger.error("--retry-failed debe ser un fichero *-FALLIDO.csv")
            sys.exit(2)
        csv_path = Path(args.retry_failed)
    else:
        csv_path = Path(get_today_csv_filename(args.output_dir))

    if not csv_path.exists():
        logger.error("No se encontró %s", csv_path)
        sys.exit(1)
    if is_processed(csv_path):
        logger.error("El fichero ya está procesado completamente.")
        sys.exit(1)

    rows = read_csv_tasks(csv_path)
    if not rows:
        logger.warning("CSV vacío, nada que enviar.")
        return

    pending = (
        [r for r in rows if r.get("estado") not in {"ok", "fallido"}]
        if not args.retry_failed
        else [r for r in rows if r.get("estado") == "fallido"]
    )

    if not pending:
        logger.warning("No hay correos pendientes de envío.")
        return

    ok_count = 0
    fail_count = 0
    current_account_idx = 0
    for row in pending:
        res, current_account_idx = send_email(
            smtp_host=args.smtp_host,
            smtp_port=args.smtp_port,
            accounts=accounts,
            to=row["email"],
            subject=row["asunto"],
            html=row["contenido"],
            from_name=args.from_name,
            start_idx=current_account_idx,
        )
        row["estado"] = "ok" if res.ok else "fallido"
        if res.ok:
            ok_count += 1
        else:
            fail_count += 1

    write_csv_with_status(csv_path, rows)
    all_ok = all(r.get("estado") == "ok" for r in rows)
    nuevo_nombre = rename_after_process(csv_path, all_ok)

    logger.info("========== RESUMEN ==========")
    logger.info("Fichero: %s", nuevo_nombre.name)
    logger.info("Total  : %d", len(rows))
    logger.info("OK     : %d", ok_count)
    logger.info("Fallido: %d", fail_count)
    logger.info("=============================")


def main():
    cfg = load_config()
    parser = build_parser()
    args = parser.parse_args()

    logger = setup_logger(level=args.log_level, log_file=args.log_file)

    if args.add:
        try:
            email, subject, content = args.add.split(";", 2)
            add_email_to_csv(
                email.strip(),
                subject.strip(),
                content.strip(),
                mailing_dir=args.output_dir,
            )
            logger.info("Email añadido correctamente.")
        except ValueError:
            logger.error("Formato incorrecto. Usa: email;asunto;contenido")
            sys.exit(1)
    else:
        accounts = resolve_accounts(args, cfg)
        if not accounts:
            logger.error(
                "Faltan credenciales SMTP. Usa --smtp-accounts, --smtp-user/--smtp-password "
                "o configura %s",
                DEFAULT_CONFIG_FILE,
            )
            sys.exit(1)
        send_emails(args, accounts)


if __name__ == "__main__":
    main()