import os
import configparser
from typing import Dict, Any, List, Tuple

DEFAULT_CONFIG_FILE = "campusdigitalfp_email_sender.cfg"

SmtpAccount = Tuple[str, str]  # (user, password)


def load_config(cfg_file: str = DEFAULT_CONFIG_FILE) -> Dict[str, Any]:
    """Devuelve dict con valores del .cfg o vacío si no existe."""
    cfg = configparser.ConfigParser()
    if os.path.isfile(cfg_file):
        cfg.read(cfg_file)

    accounts: List[SmtpAccount] = []
    accounts_raw = cfg.get("smtp", "accounts", fallback=None)
    if accounts_raw:
        for line in accounts_raw.strip().splitlines():
            line = line.strip()
            if ":" in line:
                user, pwd = line.split(":", 1)
                accounts.append((user.strip(), pwd.strip()))

    # Compatibilidad con config de cuenta única (user/password)
    single_user = cfg.get("smtp", "user", fallback=None)
    single_pass = cfg.get("smtp", "password", fallback=None)
    if single_user and single_pass and not accounts:
        accounts = [(single_user, single_pass)]

    return {
        "smtp_host": cfg.get("smtp", "host", fallback=None),
        "smtp_port": cfg.getint("smtp", "port", fallback=None),
        "smtp_user": single_user,
        "smtp_password": single_pass,
        "smtp_accounts": accounts,
        "from_name": cfg.get("defaults", "from_name", fallback=None),
    }