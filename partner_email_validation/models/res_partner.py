import smtplib
import dns.resolver
import socket

from odoo import models, fields, api

ERROR_CODES = {
    250: "VALID_EMAIL",
    251: "FORWARDED_EMAIL",
    421: "SERVER_UNAVAILABLE",
    450: "MAILBOX_TEMP_UNAVAILABLE",
    451: "LOCAL_PROCESSING_ERROR",
    452: "INSUFFICIENT_SYSTEM_STORAGE",
    550: "MAILBOX_NOT_FOUND",
    551: "USER_NOT_LOCAL",
    552: "MAILBOX_FULL",
    553: "INVALID_MAILBOX_NAME",
    554: "TRANSACTION_FAILED",
}


class ResPartner(models.Model):
    _inherit = 'res.partner'

    email_valid = fields.Boolean(
        string='Email Valid',
        default=False,
        tracking=True
    )

    batch = fields.Char(
        string='Batch'
    )

    validation_msg = fields.Text(
        string='Validation Message'
    )

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            if vals.get('email'):
                vals['email_valid'] = False

        return super().create(vals_list)

    def write(self, vals):

        if 'email' in vals:
            vals['email_valid'] = False
            vals['validation_msg'] = False

        return super().write(vals)

    # ---------------------------------------------------------
    # SINGLE VALIDATION BUTTON
    # ---------------------------------------------------------

    def action_validate_email(self):

        for partner in self:

            if not partner.email:
                partner.validation_msg = "Email missing"
                continue

            result = self.smtp_check(partner.email)

            partner.write({
                'email_valid': result['success'],
                'validation_msg': (
                    f"{result['error_code']} | "
                    f"{result['message']}"
                )
            })

    # ---------------------------------------------------------
    # CRON JOB
    # ---------------------------------------------------------

    @api.model
    def cron_validate_partner_emails(self, limit=200):

        partners = self.search([
            ('email', '!=', False),
            ('email_valid', '=', False),
            ('batch', '=', 'Batch B'),
        ], limit=limit)

        for partner in partners:
            print(partner.email)
            try:

                result = self.smtp_check(
                    partner.email
                )

                print('result',result)

                partner.write({
                    'email_valid': result['success'],
                    'validation_msg': (
                        f"{result['error_code']} | "
                        f"{result['message']}"
                    )
                })

                self.env.cr.commit()

            except Exception as e:

                partner.validation_msg = str(e)

                self.env.cr.commit()

    # ---------------------------------------------------------
    # SMTP VALIDATION
    # ---------------------------------------------------------

    # def _smtp_check_advanced(self, email):
    #
    #     try:
    #
    #         if '@' not in email:
    #             return {
    #                 "success": False,
    #                 "error_code": "INVALID_FORMAT",
    #                 "smtp_code": None,
    #                 "message": "Invalid email format"
    #             }
    #
    #         domain = email.split('@')[1].strip().lower()
    #
    #         # MX Lookup
    #         try:
    #
    #             answers = dns.resolver.resolve(domain, 'MX')
    #
    #             mx_records = sorted([
    #                 (
    #                     r.preference,
    #                     str(r.exchange).rstrip('.').strip().lower()
    #                 )
    #                 for r in answers
    #             ])
    #             if not mx_records:
    #                 return {
    #                     "success": False,
    #                     "error_code": "NO_MX_RECORD",
    #                     "smtp_code": None,
    #                     "message": "No MX records found"
    #                 }
    #
    #             mx_host = mx_records[0][1]
    #
    #         except dns.resolver.NXDOMAIN:
    #             return {
    #                 "success": False,
    #                 "error_code": "DOMAIN_NOT_FOUND",
    #                 "smtp_code": None,
    #                 "message": "Domain does not exist"
    #             }
    #
    #         except Exception as e:
    #             return {
    #                 "success": False,
    #                 "error_code": "DNS_ERROR",
    #                 "smtp_code": None,
    #                 "message": str(e)
    #             }
    #
    #         # SMTP Check
    #         server = smtplib.SMTP(timeout=30)
    #
    #         server.connect(mx_host, 25)
    #
    #         server.helo("validator.local")
    #
    #         server.mail("verify@example.com")
    #
    #         code, message = server.rcpt(email)
    #
    #         server.quit()
    #
    #         message = (
    #             message.decode()
    #             if isinstance(message, bytes)
    #             else str(message)
    #         )
    #
    #         error_code = ERROR_CODES.get(
    #             code,
    #             "UNKNOWN_SMTP_RESPONSE"
    #         )
    #
    #         return {
    #             "success": code in [250, 251],
    #             "error_code": error_code,
    #             "smtp_code": code,
    #             "message": message
    #         }
    #
    #     except socket.timeout:
    #         return {
    #             "success": False,
    #             "error_code": "CONNECTION_TIMEOUT",
    #             "smtp_code": None,
    #             "message": "SMTP connection timeout"
    #         }
    #
    #     except OSError as e:
    #
    #         error_message = str(e).lower()
    #
    #         if "timed out" in error_message:
    #             error_code = "PORT_BLOCKED_OR_TIMEOUT"
    #
    #         elif "network is unreachable" in error_message:
    #             error_code = "NETWORK_UNREACHABLE"
    #
    #         elif "getaddrinfo failed" in error_message:
    #             error_code = "INVALID_HOSTNAME"
    #
    #         else:
    #             error_code = "OS_ERROR"
    #
    #         return {
    #             "success": False,
    #             "error_code": error_code,
    #             "smtp_code": None,
    #             "message": str(e)
    #         }
    #
    #     except Exception as e:
    #         return {
    #             "success": False,
    #             "error_code": "UNKNOWN_ERROR",
    #             "smtp_code": None,
    #             "message": str(e)
    #         }

        ERROR_CODES = {
            # Success
            250: "VALID_EMAIL",
            251: "FORWARDED_EMAIL",

            # Temporary failures
            421: "SERVER_UNAVAILABLE",
            450: "MAILBOX_TEMP_UNAVAILABLE",
            451: "LOCAL_PROCESSING_ERROR",
            452: "INSUFFICIENT_SYSTEM_STORAGE",

            # Permanent failures
            550: "MAILBOX_NOT_FOUND",
            551: "USER_NOT_LOCAL",
            552: "MAILBOX_FULL",
            553: "INVALID_MAILBOX_NAME",
            554: "TRANSACTION_FAILED",
        }

    # ---------------------------------------------------------
    # SMTP VALIDATION
    # ---------------------------------------------------------

    def smtp_check(self, email):

        try:

            # -------------------------------------------------
            # EMAIL FORMAT VALIDATION
            # -------------------------------------------------

            if '@' not in email:
                return {
                    "success": False,
                    "error_code": "INVALID_FORMAT",
                    "smtp_code": None,
                    "message": "Invalid email format"
                }

            # -------------------------------------------------
            # DOMAIN EXTRACTION
            # -------------------------------------------------

            domain = email.split('@')[1].strip().lower()

            # -------------------------------------------------
            # MX LOOKUP
            # -------------------------------------------------

            try:

                answers = dns.resolver.resolve(domain, 'MX')

                mx_records = sorted([
                    (r.preference, str(r.exchange).rstrip('.'))
                    for r in answers
                ])

                if not mx_records:
                    return {
                        "success": False,
                        "error_code": "NO_MX_RECORD",
                        "smtp_code": None,
                        "message": "No MX records found"
                    }

                mx_host = mx_records[0][1]

            except dns.resolver.NXDOMAIN:
                return {
                    "success": False,
                    "error_code": "DOMAIN_NOT_FOUND",
                    "smtp_code": None,
                    "message": f"Domain does not exist: {domain}"
                }

            except dns.resolver.NoAnswer:
                return {
                    "success": False,
                    "error_code": "NO_MX_RECORD",
                    "smtp_code": None,
                    "message": f"No MX record found for {domain}"
                }

            except Exception as e:
                return {
                    "success": False,
                    "error_code": "DNS_ERROR",
                    "smtp_code": None,
                    "message": str(e)
                }

            # -------------------------------------------------
            # SMTP CONNECTION
            # -------------------------------------------------

            server = smtplib.SMTP(timeout=45)

            server.connect(mx_host, 25)

            server.helo("validator.local")

            server.mail("career@technians.com")

            code, message = server.rcpt(email)

            server.quit()

            message = (
                message.decode()
                if isinstance(message, bytes)
                else str(message)
            )

            # -------------------------------------------------
            # SMTP RESPONSE HANDLING
            # -------------------------------------------------

            error_code = ERROR_CODES.get(
                code,
                "UNKNOWN_SMTP_RESPONSE"
            )

            return {
                "success": code in [250, 251],
                "error_code": error_code,
                "smtp_code": code,
                "message": message,
                "mx_host": mx_host
            }

        # -------------------------------------------------
        # NETWORK ERRORS
        # -------------------------------------------------

        except socket.timeout:
            return {
                "success": False,
                "error_code": "CONNECTION_TIMEOUT",
                "smtp_code": None,
                "message": "SMTP connection timed out"
            }

        except socket.gaierror as e:
            return {
                "success": False,
                "error_code": "DNS_RESOLUTION_FAILED",
                "smtp_code": None,
                "message": str(e)
            }

        except ConnectionRefusedError:
            return {
                "success": False,
                "error_code": "CONNECTION_REFUSED",
                "smtp_code": None,
                "message": "SMTP connection refused"
            }

        except smtplib.SMTPServerDisconnected:
            return {
                "success": False,
                "error_code": "SERVER_DISCONNECTED",
                "smtp_code": None,
                "message": "SMTP server disconnected unexpectedly"
            }

        except smtplib.SMTPConnectError as e:
            return {
                "success": False,
                "error_code": "SMTP_CONNECT_ERROR",
                "smtp_code": None,
                "message": str(e)
            }

        except smtplib.SMTPRecipientsRefused:
            return {
                "success": False,
                "error_code": "RECIPIENT_REFUSED",
                "smtp_code": None,
                "message": "Recipient refused"
            }

        except smtplib.SMTPException as e:
            return {
                "success": False,
                "error_code": "SMTP_EXCEPTION",
                "smtp_code": None,
                "message": str(e)
            }

        except OSError as e:

            error_message = str(e).lower()

            if "timed out" in error_message:
                error_code = "PORT_BLOCKED_OR_TIMEOUT"

            elif "network is unreachable" in error_message:
                error_code = "NETWORK_UNREACHABLE"

            elif "getaddrinfo failed" in error_message:
                error_code = "INVALID_HOSTNAME"

            else:
                error_code = "OS_ERROR"

            return {
                "success": False,
                "error_code": error_code,
                "smtp_code": None,
                "message": str(e)
            }

        except Exception as e:
            return {
                "success": False,
                "error_code": "UNKNOWN_ERROR",
                "smtp_code": None,
                "message": str(e)
            }

    # ---------------------------------------------------------
    # EXAMPLE
    # ---------------------------------------------------------

    # result = smtp_check("shaikhzoha2266@anjumanbskschool.edu.in")

    # print(result)
