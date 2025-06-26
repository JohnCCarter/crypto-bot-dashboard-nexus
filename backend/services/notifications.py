import os
import smtplib
from email.mime.text import MIMEText
from typing import Optional


class Notifier:
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        sender: str,
        receiver: str,
        password: Optional[str] = None,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender = sender
        self.receiver = receiver
        self.password = password or os.getenv("SMTP_PASSWORD")
        if not self.password:
            raise ValueError(
                "SMTP-lösenord måste anges som argument eller miljövariabel (SMTP_PASSWORD)"
            )

    def send(self, message: str, subject: str = "Trading Bot Notification"):
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = self.receiver
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, str(self.password))
                server.sendmail(self.sender, [self.receiver], msg.as_string())
        except Exception as e:
            print(f"Notifieringsfel: {e}")
