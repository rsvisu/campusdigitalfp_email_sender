# CampusDigitalFP Email Sender
Aplicación Python para la automatización del envío de emails en el CampusDigitalFP que permite gestionar y enviar correos electrónicos vía SMTP (Gmail u otro proveedor) a partir de un fichero CSV.  
Totalmente funcional desde línea de comandos y sin necesidad de tocar código.

## ¿Qué hace?

1. **Añade** nuevos destinatarios a un CSV diario:
   ```
   id_emails_DD-MM-YYYY.csv  (campos: email;asunto;contenido)
   ```
2. **Envía** los e-mails línea a línea:
   - Añade columna `estado` con valor `ok` / `fallido`.
   - Renombra el CSV:
     - `-PROCESADO` → si **todos** los envíos salieron bien.
     - `-FALLIDO` → si **alguno** falló.
3. **Re-intenta** solo los fallidos de un fichero `-FALLIDO.csv` con `--retry-failed`.
4. Credenciales y parámetros por **archivo de config** (`email_sender.cfg`) o por **CLI**.


## Instalación

Desde la ruta del proyecto:

```bash
poetry build                      # genera wheel en dist/
pip install dist/email_sender-*.whl
```

El comando quedará disponible como:

```bash
python email_sender.py <opciones>
```

## Archivo de configuración (opcional)

Fichero `campusdigitalfp_email_sender.cfg` en el directorio donde lances el comando:

```ini
[smtp]
host = smtp.gmail.com
port = 465
# Una sola cuenta:
user = micuenta@gmail.com
password = miapppassword

# O varias cuentas para rotación automática (si una falla, pasa a la siguiente):
# accounts =
#     cuenta1@gmail.com:apppassword1
#     cuenta2@gmail.com:apppassword2
#     cuenta3@gmail.com:apppassword3

[defaults]
from_name = Mi Empresa
```

Si no existe el archivo debes proporcionar credenciales vía CLI (ver comandos).

---

## Comandos

### 1. Añadir un nuevo e-mail al CSV del día

```bash
python email_sender.py \
        --add "cliente@example.com;Oferta especial;<h1>50 % dto</h1><p>¡Solo hoy!</p>"
```

Se crea (o amplía) `./mailing/id_emails_DD-MM-YYYY.csv`.


### 2. Enviar todos los pendientes del CSV del día

```bash
# Cuenta única
python email_sender.py \
        --smtp-user micuenta@gmail.com \
        --smtp-password miapppassword \
        --send

# Varias cuentas con rotación automática
python email_sender.py \
        --smtp-accounts "cuenta1@gmail.com:pass1,cuenta2@gmail.com:pass2" \
        --send
```

Salida posible:

```
cliente@example.com ... OK
otro@example.com ... FALLIDO
Renombrado -> id_emails_DD-MM-YYYY-FALLIDO.csv
```


### 3. Re-intentar solo los fallidos de cualquier CSV `-FALLIDO`

```bash
python email_sender.py \
        --smtp-user micuenta@gmail.com \
        --smtp-password miapppassword \
        --retry-failed mailing/id_emails_10-12-2025-FALLIDO.csv
```

Tras el re-intento el fichero se renombra de nuevo:
- `-PROCESADO` → si **ahora** todos están `ok`.  
- `-FALLIDO` → si **aún** queda algún `fallido`.

---

### 4. Sobrescribir puerto o carpeta de trabajo

```bash
python email_sender.py \
        --smtp-host smtp.gmail.com \
        --smtp-port 587 \
        --output-dir /tmp/correos \
        --send
```

## Notas rápidas

- Los CSV y el fichero de configuración residen **siempre** en el directorio desde el que ejecutas el comando; nada se escribe dentro del paquete instalado.  
- Un fichero `-PROCESADO` **no** puede volver a procesarse (salvo renombrarlo).  
- `--retry-failed` **solo** acepta ficheros cuyo nombre termine en `-FALLIDO.csv`.

---

## Ejemplo completo de flujo

```bash
# 1. Añadir dos filas
python email_sender.py --add "ana@example.com;Oferta;<b>50 %</b>"
python email_sender.py --add "luis@example.com;Newsletter;<i>Resumen</i>"

# 2. Enviar (suponemos que uno falla)
python email_sender.py --smtp-user yo@gmail.com --smtp-password xxx --send
# -> genera id_emails_DD-MM-YYYY-FALLIDO.csv

# 3. Revisar fallos y re-intentar
python email_sender.py --smtp-user yo@gmail.com --smtp-password xxx \
        --retry-failed mailing/id_emails_DD-MM-YYYY-FALLIDO.csv
# Si ahora todos OK -> id_emails_DD-MM-YYYY-PROCESADO.csv
```


## Licencia

Este proyecto es código abierto con licencia GNU 3.0 - úsalo/modifícalo bajo los términos de la licencia que hayas incluido en tu repositorio.