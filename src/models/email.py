"""Email-related data models."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, EmailStr, Field, validator


class EmailPriority(str, Enum):
    """Email priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailStatus(str, Enum):
    """Email status."""

    DRAFT = "draft"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class EmailRecipient(BaseModel):
    """Represents an email recipient."""

    email: EmailStr
    name: str | None = None
    recipient_type: str = "to"  # "to", "cc", "bcc"

    @validator("recipient_type")
    def validate_recipient_type(cls, v: str) -> str:
        """Validate recipient type."""
        if v not in ["to", "cc", "bcc"]:
            raise ValueError("Recipient type must be 'to', 'cc', or 'bcc'")
        return v

    def __str__(self) -> str:
        """String representation."""
        if self.name:
            return f'"{self.name}" <{self.email}>'
        return str(self.email)


class EmailAttachment(BaseModel):
    """Represents an email attachment."""

    filename: str
    content: bytes | None = None
    content_type: str = "application/octet-stream"
    file_path: Path | None = None
    size: int | None = None

    @validator("file_path")
    def validate_file_path(cls, v: Path | None) -> Path | None:
        """Validate file path exists."""
        if v and not v.exists():
            raise ValueError(f"File not found: {v}")
        return v

    def load_content(self) -> bytes:
        """Load content from file if not already loaded.

        Returns:
            File content as bytes.
        """
        if self.content:
            return self.content

        if self.file_path and self.file_path.exists():
            with open(self.file_path, "rb") as f:
                self.content = f.read()
                self.size = len(self.content)
            return self.content

        raise ValueError("No content or file path available")


class EmailMessage(BaseModel):
    """Represents an email message."""

    subject: str
    body: str
    body_html: str | None = None
    sender: EmailStr
    sender_name: str | None = None
    recipients: list[EmailRecipient]
    attachments: list[EmailAttachment] = Field(default_factory=list)
    priority: EmailPriority = EmailPriority.NORMAL
    status: EmailStatus = EmailStatus.DRAFT
    headers: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    sent_at: datetime | None = None
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3

    @validator("recipients")
    def validate_recipients(cls, v: list[EmailRecipient]) -> list[EmailRecipient]:
        """Validate at least one recipient exists."""
        if not v:
            raise ValueError("At least one recipient is required")

        # Ensure at least one "to" recipient
        if not any(r.recipient_type == "to" for r in v):
            raise ValueError("At least one 'to' recipient is required")

        return v

    @validator("subject")
    def validate_subject(cls, v: str) -> str:
        """Validate subject is not empty."""
        if not v or not v.strip():
            raise ValueError("Subject cannot be empty")
        return v.strip()

    def get_recipients_by_type(self, recipient_type: str) -> list[EmailRecipient]:
        """Get recipients by type.

        Args:
            recipient_type: Type of recipients ("to", "cc", "bcc").

        Returns:
            List of recipients of specified type.
        """
        return [r for r in self.recipients if r.recipient_type == recipient_type]

    def add_recipient(
        self, email: str, name: str | None = None, recipient_type: str = "to"
    ) -> None:
        """Add a recipient.

        Args:
            email: Email address.
            name: Recipient name.
            recipient_type: Type of recipient.
        """
        recipient = EmailRecipient(email=email, name=name, recipient_type=recipient_type)
        self.recipients.append(recipient)

    def add_attachment(self, file_path: Path, filename: str | None = None) -> None:
        """Add an attachment from file.

        Args:
            file_path: Path to file.
            filename: Optional filename override.
        """
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        attachment = EmailAttachment(filename=filename or file_path.name, file_path=file_path)
        self.attachments.append(attachment)

    def mark_as_sent(self) -> None:
        """Mark email as sent."""
        self.status = EmailStatus.SENT
        self.sent_at = datetime.now()

    def mark_as_failed(self, error: str) -> None:
        """Mark email as failed.

        Args:
            error: Error message.
        """
        self.status = EmailStatus.FAILED
        self.error_message = error
        self.retry_count += 1

    def can_retry(self) -> bool:
        """Check if email can be retried.

        Returns:
            True if retry is allowed.
        """
        return self.retry_count < self.max_retries

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v),
        }


class EmailTemplate(BaseModel):
    """Represents an email template."""

    template_id: str
    name: str
    description: str | None = None
    subject_template: str
    body_template: str
    body_html_template: str | None = None
    variables: list[str] = Field(default_factory=list)
    category: str | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @validator("template_id")
    def validate_template_id(cls, v: str) -> str:
        """Validate template ID format."""
        if not v or not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Template ID must be alphanumeric with underscores or hyphens")
        return v

    @validator("variables")
    def extract_variables(cls, _value: list[str] | None, values: dict[str, Any]) -> list[str]:
        """Extract variables from templates."""
        import re

        variables = set()

        # Extract from subject template
        if "subject_template" in values:
            subject_vars = re.findall(r"\{\{(\w+)\}\}", values["subject_template"])
            variables.update(subject_vars)

        # Extract from body template
        if "body_template" in values:
            body_vars = re.findall(r"\{\{(\w+)\}\}", values["body_template"])
            variables.update(body_vars)

        # Extract from HTML template
        if "body_html_template" in values and values["body_html_template"]:
            html_vars = re.findall(r"\{\{(\w+)\}\}", values["body_html_template"])
            variables.update(html_vars)

        return list(variables)

    def render(self, variables: dict[str, Any]) -> EmailMessage:
        """Render template with variables.

        Args:
            variables: Dictionary of template variables.

        Returns:
            Rendered EmailMessage.
        """
        # Check all required variables are provided
        missing = set(self.variables) - set(variables.keys())
        if missing:
            raise ValueError(f"Missing template variables: {missing}")

        # Simple template rendering (in production, use Jinja2)
        subject = self.subject_template
        body = self.body_template
        body_html = self.body_html_template

        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
            if body_html:
                body_html = body_html.replace(placeholder, str(value))

        # Create email message
        return EmailMessage(
            subject=subject,
            body=body,
            body_html=body_html,
            sender=variables.get("sender", "noreply@resourceallocation.com"),
            sender_name=variables.get("sender_name"),
            recipients=[],  # Recipients should be added separately
            metadata={"template_id": self.template_id, "template_name": self.name},
        )

    def validate_template(self) -> bool:
        """Validate template syntax.

        Returns:
            True if template is valid.
        """
        import re

        for template in [self.subject_template, self.body_template, self.body_html_template]:
            if template:
                # Check for unclosed variables
                if template.count("{{") != template.count("}}"):
                    return False

                # Check variable format
                matches = re.findall(r"\{\{[^}]*\}\}", template)
                for match in matches:
                    if not re.match(r"\{\{\w+\}\}", match):
                        return False

        return True

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class EmailConfiguration(BaseModel):
    """Email service configuration."""

    enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    use_tls: bool = True
    use_ssl: bool = False
    username: str | None = None
    password: str | None = None
    from_email: EmailStr = "noreply@resourceallocation.com"
    from_name: str = "Resource Management System"
    reply_to: EmailStr | None = None
    default_recipients: list[EmailStr] = Field(default_factory=list)
    cc_recipients: list[EmailStr] = Field(default_factory=list)
    bcc_recipients: list[EmailStr] = Field(default_factory=list)
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    timeout: int = 30  # seconds
    debug: bool = False

    @validator("smtp_port")
    def validate_port(cls, v: int) -> int:
        """Validate SMTP port."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @validator("use_tls", "use_ssl")
    def validate_encryption(cls, v: bool, values: dict[str, Any]) -> bool:
        """Validate encryption settings."""
        # Can't use both TLS and SSL
        if "use_tls" in values and "use_ssl" in values and values["use_tls"] and values["use_ssl"]:
            raise ValueError("Cannot use both TLS and SSL")
        return v
