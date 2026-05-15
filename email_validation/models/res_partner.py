import re
import smtplib
import dns.resolver
import socket

from concurrent.futures import ThreadPoolExecutor, as_completed

from odoo import models, fields, api

# ---------------------------------------------------------
# EMAIL REGEX
# ---------------------------------------------------------

EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

# ---------------------------------------------------------
# MX CACHE
# ---------------------------------------------------------

MX_CACHE = {}

# ---------------------------------------------------------
# SMTP ERROR CODES
# ---------------------------------------------------------

ERROR_CODES = {

    # SUCCESS
    250: "VALID_EMAIL",
    251: "FORWARDED_EMAIL",

    # TEMPORARY
    421: "SERVER_UNAVAILABLE",
    450: "MAILBOX_TEMP_UNAVAILABLE",
    451: "LOCAL_PROCESSING_ERROR",
    452: "INSUFFICIENT_SYSTEM_STORAGE",

    # PERMANENT
    550: "MAILBOX_NOT_FOUND",
    551: "USER_NOT_LOCAL",
    552: "MAILBOX_FULL",
    553: "INVALID_MAILBOX_NAME",
    554: "TRANSACTION_FAILED",
}


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ---------------------------------------------------------
    # FIELDS
    # ---------------------------------------------------------

    email_valid = fields.Boolean(
        string='Email Valid',
        default=False
    )

    batch = fields.Char(
        string='Batch'
    )

    validation_msg = fields.Text(
        string='Validation Message'
    )

    validation_state = fields.Selection([
        ('pending', 'Pending'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ('error', 'Error')
    ], default='pending')

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if vals.get('email'):

                vals['email_valid'] = False
                vals['validation_msg'] = False
                vals['validation_state'] = 'pending'

        return super().create(vals_list)

    # ---------------------------------------------------------
    # WRITE
    # ---------------------------------------------------------

    def write(self, vals):

        if 'email' in vals:

            vals['email_valid'] = False
            vals['validation_msg'] = False
            vals['validation_state'] = 'pending'

        return super().write(vals)

    # ---------------------------------------------------------
    # GET MX HOST
    # ---------------------------------------------------------

    def _get_mx_host(self, domain):

        domain = domain.strip().lower()

        # CACHE

        if domain in MX_CACHE:
            return MX_CACHE[domain]

        resolver = dns.resolver.Resolver()

        resolver.timeout = 5
        resolver.lifetime = 5

        answers = resolver.resolve(domain, 'MX')

        mx_records = sorted([
            (
                r.preference,
                str(r.exchange).rstrip('.').lower()
            )
            for r in answers
        ])

        if not mx_records:
            return False

        mx_host = mx_records[0][1]

        # SAVE CACHE

        MX_CACHE[domain] = mx_host

        return mx_host

    # ---------------------------------------------------------
    # SMTP VALIDATION
    # ---------------------------------------------------------

    def smtp_check(self, email):

        try:

            # -------------------------------------------------
            # CLEAN EMAIL
            # -------------------------------------------------

            email = (email or '').strip().lower()

            # -------------------------------------------------
            # FORMAT VALIDATION
            # -------------------------------------------------

            if not EMAIL_REGEX.match(email):

                return {
                    "success": False,
                    "state": "invalid",
                    "error_code": "INVALID_FORMAT",
                    "smtp_code": None,
                    "message": "Invalid email format"
                }

            # -------------------------------------------------
            # DOMAIN
            # -------------------------------------------------

            domain = email.split('@')[1]

            # -------------------------------------------------
            # MX LOOKUP
            # -------------------------------------------------

            try:

                mx_host = self._get_mx_host(domain)

                if not mx_host:

                    return {
                        "success": False,
                        "state": "invalid",
                        "error_code": "NO_MX_RECORD",
                        "smtp_code": None,
                        "message": "No MX records found"
                    }

            except dns.resolver.NXDOMAIN:

                return {
                    "success": False,
                    "state": "invalid",
                    "error_code": "DOMAIN_NOT_FOUND",
                    "smtp_code": None,
                    "message": "Domain does not exist"
                }

            except Exception as e:

                return {
                    "success": False,
                    "state": "error",
                    "error_code": "DNS_ERROR",
                    "smtp_code": None,
                    "message": str(e)
                }

            # -------------------------------------------------
            # SMTP CONNECTION
            # -------------------------------------------------

            server = None

            try:

                server = smtplib.SMTP(timeout=45)

                server.connect(mx_host, 25)

                # EHLO

                ehlo_code, ehlo_message = server.ehlo(
                    "technians.com"
                )

                if ehlo_code != 250:

                    return {
                        "success": False,
                        "state": "error",
                        "error_code": "EHLO_FAILED",
                        "smtp_code": ehlo_code,
                        "message": str(ehlo_message)
                    }

                # MAIL FROM

                mail_code, mail_message = server.mail(
                    "career@technians.com"
                )

                if mail_code != 250:

                    return {
                        "success": False,
                        "state": "error",
                        "error_code": "MAIL_FROM_FAILED",
                        "smtp_code": mail_code,
                        "message": str(mail_message)
                    }

                # RCPT TO

                code, message = server.rcpt(email)

            finally:

                if server:

                    try:
                        server.quit()

                    except Exception:
                        pass

            # -------------------------------------------------
            # DECODE MESSAGE
            # -------------------------------------------------

            message = (
                message.decode()
                if isinstance(message, bytes)
                else str(message)
            )

            error_code = ERROR_CODES.get(
                code,
                "UNKNOWN_SMTP_RESPONSE"
            )

            # -------------------------------------------------
            # VALID / INVALID / ERROR
            # -------------------------------------------------

            valid_codes = [250, 251]

            invalid_codes = [550, 551, 553]

            if code in valid_codes:

                success = True
                state = 'valid'

            elif code in invalid_codes:

                success = False
                state = 'invalid'

            else:

                success = False
                state = 'error'

            return {

                "success": success,

                "state": state,

                "error_code": error_code,

                "smtp_code": code,

                "message": message
            }

        # -----------------------------------------------------
        # SOCKET TIMEOUT
        # -----------------------------------------------------

        except socket.timeout:

            return {

                "success": False,

                "state": "error",

                "error_code": "CONNECTION_TIMEOUT",

                "smtp_code": None,

                "message": "SMTP connection timeout"
            }

        # -----------------------------------------------------
        # OS ERRORS
        # -----------------------------------------------------

        except OSError as e:

            error_message = str(e).lower()

            if "timed out" in error_message:

                error_code = "PORT_BLOCKED_OR_TIMEOUT"

            elif "network is unreachable" in error_message:

                error_code = "NETWORK_UNREACHABLE"

            elif "10054" in error_message:

                error_code = "REMOTE_SERVER_CLOSED_CONNECTION"

            elif "getaddrinfo failed" in error_message:

                error_code = "INVALID_HOSTNAME"

            else:

                error_code = "OS_ERROR"

            return {

                "success": False,

                "state": "error",

                "error_code": error_code,

                "smtp_code": None,

                "message": str(e)
            }

        # -----------------------------------------------------
        # UNKNOWN ERROR
        # -----------------------------------------------------

        except Exception as e:

            return {

                "success": False,

                "state": "error",

                "error_code": "UNKNOWN_ERROR",

                "smtp_code": None,

                "message": str(e)
            }

    # ---------------------------------------------------------
    # SINGLE BUTTON VALIDATION
    # ---------------------------------------------------------

    def action_validate_email(self):

        for partner in self:

            if not partner.email:

                partner.sudo().write({

                    'email_valid': False,

                    'validation_state': 'invalid',

                    'validation_msg': 'Email missing'
                })

                continue

            result = self.smtp_check(partner.email)

            partner.sudo().write({

                'email_valid': result['success'],

                'validation_state': result['state'],

                'validation_msg': (
                    f"{result['error_code']} | "
                    f"{result['message']}"
                )
            })

    # ---------------------------------------------------------
    # THREAD VALIDATION
    # ---------------------------------------------------------

    def _validate_partner_email_thread(self, email, partner_id):

        try:

            result = self.smtp_check(email)

            return {

                'partner_id': partner_id,

                'success': result['success'],

                'message': (
                    f"{result['error_code']} | "
                    f"{result['message']}"
                ),

                'state': result['state']
            }

        except Exception as e:

            return {

                'partner_id': partner_id,

                'success': False,

                'message': str(e),

                'state': 'error'
            }

    # ---------------------------------------------------------
    # CRON VALIDATION
    # ---------------------------------------------------------

    @api.model
    def cron_validate_partner_emails(self, limit=500):

        partners = self.sudo().search([
            ('email', '!=', False),
            ('validation_state', 'in', ['pending','invalid','error']),
            ('batch', '=', 'Batch A'),
        ], limit=limit)

        if not partners:
            return

        # -------------------------------------------------
        # MULTI THREADING
        # -------------------------------------------------

        with ThreadPoolExecutor(max_workers=3) as executor:

            futures = {

                executor.submit(
                    self._validate_partner_email_thread,
                    partner.email,
                    partner.id
                ): partner.id

                for partner in partners
            }

            # -------------------------------------------------
            # LIVE UPDATE
            # -------------------------------------------------

            for future in as_completed(futures):

                try:

                    result = future.result()

                    partner = self.env[
                        'res.partner'
                    ].sudo().browse(
                        result['partner_id']
                    ).exists()

                    if not partner:
                        continue

                    partner.sudo().write({

                        'email_valid': result['success'],

                        'validation_msg': result['message'],

                        'validation_state': result['state']
                    })

                    # LIVE COMMIT

                    self.env.cr.commit()

                except Exception:
                    pass