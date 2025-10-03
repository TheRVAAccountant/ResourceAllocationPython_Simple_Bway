"""Email service for sending notifications."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Any
from pathlib import Path
import time
from loguru import logger

from src.core.base_service import BaseService, timer, error_handler
from src.models.email import (
    EmailMessage, EmailRecipient, EmailTemplate,
    EmailConfiguration, EmailStatus, EmailPriority
)
from src.models.allocation import AllocationResult


class EmailService(BaseService):
    """Service for sending email notifications.
    
    Handles email composition, template rendering, and SMTP delivery
    for allocation notifications and system alerts.
    """
    
    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize the email service.
        
        Args:
            config: Configuration dictionary.
        """
        super().__init__(config)
        
        # Email configuration
        self.email_config = EmailConfiguration(
            enabled=self.get_config("email_enabled", False),
            smtp_host=self.get_config("smtp_host", "smtp.gmail.com"),
            smtp_port=self.get_config("smtp_port", 587),
            use_tls=self.get_config("use_tls", True),
            username=self.get_config("email_username"),
            password=self.get_config("email_password"),
            from_email=self.get_config("from_email", "noreply@resourceallocation.com"),
            from_name=self.get_config("from_name", "Resource Management System"),
            default_recipients=self.get_config("default_recipients", []),
            max_retries=self.get_config("max_retries", 3),
            retry_delay=self.get_config("retry_delay", 60),
            timeout=self.get_config("timeout", 30)
        )
        
        self.smtp_connection = None
        self.templates: dict[str, EmailTemplate] = {}
        self.queue: list[EmailMessage] = []
        
        # Load default templates
        self._load_default_templates()
    
    def initialize(self) -> None:
        """Initialize the email service."""
        logger.info("Initializing Email Service")
        
        if self.email_config.enabled:
            # Test SMTP connection
            if self._test_connection():
                logger.info("Email service initialized successfully")
            else:
                logger.warning("Email service initialized but connection test failed")
        else:
            logger.info("Email service disabled in configuration")
        
        self._initialized = True
    
    def validate(self) -> bool:
        """Validate the service configuration.
        
        Returns:
            True if configuration is valid.
        """
        if not self.email_config.enabled:
            return True
        
        if not self.email_config.smtp_host:
            logger.error("SMTP host not configured")
            return False
        
        if not self.email_config.username or not self.email_config.password:
            logger.warning("SMTP credentials not configured")
        
        return True
    
    def cleanup(self) -> None:
        """Clean up email service resources."""
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
            except:
                pass
        
        super().cleanup()
    
    def _load_default_templates(self):
        """Load default email templates."""
        # Allocation success template
        self.templates["allocation_success"] = EmailTemplate(
            template_id="allocation_success",
            name="Allocation Success",
            description="Sent when allocation completes successfully",
            subject_template="Resource Allocation Completed - {{date}}",
            body_template="""Dear Team,

The resource allocation for {{date}} has been completed successfully.

Summary:
- Total Vehicles: {{total_vehicles}}
- Total Drivers: {{total_drivers}}
- Allocated Vehicles: {{allocated_vehicles}}
- Unallocated Vehicles: {{unallocated_vehicles}}
- Allocation Rate: {{allocation_rate}}%

Please find the detailed allocation report attached.

Best regards,
Resource Management System""",
            body_html_template="""<html>
<body>
<h2>Resource Allocation Completed</h2>
<p>Dear Team,</p>
<p>The resource allocation for <strong>{{date}}</strong> has been completed successfully.</p>
<h3>Summary:</h3>
<ul>
<li>Total Vehicles: {{total_vehicles}}</li>
<li>Total Drivers: {{total_drivers}}</li>
<li>Allocated Vehicles: {{allocated_vehicles}}</li>
<li>Unallocated Vehicles: {{unallocated_vehicles}}</li>
<li>Allocation Rate: {{allocation_rate}}%</li>
</ul>
<p>Please find the detailed allocation report attached.</p>
<p>Best regards,<br>Resource Management System</p>
</body>
</html>"""
        )
        
        # Allocation failure template
        self.templates["allocation_failure"] = EmailTemplate(
            template_id="allocation_failure",
            name="Allocation Failure",
            description="Sent when allocation fails",
            subject_template="Resource Allocation Failed - {{date}}",
            body_template="""Dear Team,

The resource allocation for {{date}} has failed.

Error: {{error_message}}

Please review the error and retry the allocation process.

Best regards,
Resource Management System"""
        )
        
        # Daily summary template
        self.templates["daily_summary"] = EmailTemplate(
            template_id="daily_summary",
            name="Daily Summary",
            description="Daily allocation summary",
            subject_template="Daily Allocation Summary - {{date}}",
            body_template="""Dear Team,

Here is today's allocation summary for {{date}}:

{{summary_content}}

Best regards,
Resource Management System"""
        )
    
    def _test_connection(self) -> bool:
        """Test SMTP connection.
        
        Returns:
            True if connection successful.
        """
        try:
            with smtplib.SMTP(self.email_config.smtp_host, self.email_config.smtp_port,
                             timeout=self.email_config.timeout) as smtp:
                if self.email_config.use_tls:
                    smtp.starttls()
                
                if self.email_config.username and self.email_config.password:
                    smtp.login(self.email_config.username, self.email_config.password)
                
                return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
    
    @timer
    @error_handler
    def send_email(self, message: EmailMessage) -> bool:
        """Send an email message.
        
        Args:
            message: Email message to send.
        
        Returns:
            True if sent successfully.
        """
        if not self.email_config.enabled:
            logger.warning("Email service is disabled")
            return False
        
        try:
            # Create MIME message
            mime_msg = self._create_mime_message(message)
            
            # Send email
            with smtplib.SMTP(self.email_config.smtp_host, self.email_config.smtp_port,
                             timeout=self.email_config.timeout) as smtp:
                if self.email_config.use_tls:
                    smtp.starttls()
                
                if self.email_config.username and self.email_config.password:
                    smtp.login(self.email_config.username, self.email_config.password)
                
                # Get recipient addresses
                to_addrs = [r.email for r in message.recipients]
                
                # Send message
                smtp.send_message(mime_msg)
                
                message.mark_as_sent()
                logger.info(f"Email sent successfully: {message.subject}")
                return True
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email: {error_msg}")
            message.mark_as_failed(error_msg)
            
            # Retry if allowed
            if message.can_retry():
                self.queue_email(message)
                logger.info(f"Email queued for retry (attempt {message.retry_count}/{message.max_retries})")
            
            return False
    
    def _create_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """Create MIME message from EmailMessage.
        
        Args:
            message: Email message.
        
        Returns:
            MIME message.
        """
        # Create multipart message
        mime_msg = MIMEMultipart("alternative")
        
        # Set headers
        mime_msg["Subject"] = message.subject
        mime_msg["From"] = f"{message.sender_name or self.email_config.from_name} <{message.sender}>"
        
        # Add recipients
        to_recipients = message.get_recipients_by_type("to")
        mime_msg["To"] = ", ".join([str(r) for r in to_recipients])
        
        cc_recipients = message.get_recipients_by_type("cc")
        if cc_recipients:
            mime_msg["Cc"] = ", ".join([str(r) for r in cc_recipients])
        
        # Add custom headers
        for key, value in message.headers.items():
            mime_msg[key] = value
        
        # Add priority header
        if message.priority == EmailPriority.HIGH or message.priority == EmailPriority.URGENT:
            mime_msg["X-Priority"] = "1"
            mime_msg["Importance"] = "high"
        
        # Add body
        text_part = MIMEText(message.body, "plain")
        mime_msg.attach(text_part)
        
        if message.body_html:
            html_part = MIMEText(message.body_html, "html")
            mime_msg.attach(html_part)
        
        # Add attachments
        for attachment in message.attachments:
            self._add_attachment(mime_msg, attachment)
        
        return mime_msg
    
    def _add_attachment(self, mime_msg: MIMEMultipart, attachment):
        """Add attachment to MIME message.
        
        Args:
            mime_msg: MIME message.
            attachment: Attachment to add.
        """
        try:
            # Load content
            content = attachment.load_content()
            
            # Create MIME attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(content)
            encoders.encode_base64(part)
            
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={attachment.filename}"
            )
            
            mime_msg.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.filename}: {e}")
    
    def queue_email(self, message: EmailMessage):
        """Queue email for sending.
        
        Args:
            message: Email message to queue.
        """
        message.status = EmailStatus.QUEUED
        self.queue.append(message)
        logger.info(f"Email queued: {message.subject}")
    
    def process_queue(self) -> tuple[int, int]:
        """Process email queue.
        
        Returns:
            Tuple of (sent_count, failed_count).
        """
        sent = 0
        failed = 0
        
        # Process queue
        while self.queue:
            message = self.queue.pop(0)
            
            # Check if retry delay has passed
            if message.retry_count > 0:
                time.sleep(self.email_config.retry_delay)
            
            if self.send_email(message):
                sent += 1
            else:
                failed += 1
        
        logger.info(f"Queue processed: {sent} sent, {failed} failed")
        return sent, failed
    
    def send_allocation_notification(
        self,
        result: AllocationResult,
        recipients: Optional[list[str]] = None,
        attach_report: bool = True
    ) -> bool:
        """Send allocation result notification.
        
        Args:
            result: Allocation result.
            recipients: Email recipients (uses defaults if not provided).
            attach_report: Whether to attach detailed report.
        
        Returns:
            True if sent successfully.
        """
        try:
            # Get template
            template = self.templates.get("allocation_success")
            if not template:
                logger.error("Allocation success template not found")
                return False
            
            # Prepare variables
            summary = result.get_allocation_summary()
            variables = {
                "date": summary["timestamp"].strftime("%Y-%m-%d"),
                "total_vehicles": summary["total_allocated_vehicles"] + summary["total_unallocated_vehicles"],
                "total_drivers": summary["total_drivers"],
                "allocated_vehicles": summary["total_allocated_vehicles"],
                "unallocated_vehicles": summary["total_unallocated_vehicles"],
                "allocation_rate": f"{summary['allocation_rate'] * 100:.1f}",
                "sender": self.email_config.from_email,
                "sender_name": self.email_config.from_name
            }
            
            # Render template
            message = template.render(variables)
            
            # Add recipients
            recipient_list = recipients or self.email_config.default_recipients
            for email in recipient_list:
                message.add_recipient(email)
            
            # Add CC recipients
            for email in self.email_config.cc_recipients:
                message.add_recipient(email, recipient_type="cc")
            
            # Send email
            return self.send_email(message)
            
        except Exception as e:
            logger.error(f"Failed to send allocation notification: {e}")
            return False
    
    def send_error_notification(
        self,
        error: str,
        context: Optional[dict[str, Any]] = None,
        recipients: Optional[list[str]] = None
    ) -> bool:
        """Send error notification.
        
        Args:
            error: Error message.
            context: Additional context.
            recipients: Email recipients.
        
        Returns:
            True if sent successfully.
        """
        try:
            message = EmailMessage(
                subject=f"Resource Allocation Error - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                body=f"""An error occurred in the Resource Management System:

Error: {error}

Context:
{context or 'No additional context available'}

Please review and take appropriate action.

Best regards,
Resource Management System""",
                sender=self.email_config.from_email,
                sender_name=self.email_config.from_name,
                recipients=[],
                priority=EmailPriority.HIGH
            )
            
            # Add recipients
            recipient_list = recipients or self.email_config.default_recipients
            for email in recipient_list:
                message.add_recipient(email)
            
            return self.send_email(message)
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
            return False
    
    def add_template(self, template: EmailTemplate):
        """Add email template.
        
        Args:
            template: Email template to add.
        """
        if template.validate_template():
            self.templates[template.template_id] = template
            logger.info(f"Email template added: {template.template_id}")
        else:
            logger.error(f"Invalid template: {template.template_id}")
    
    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get email template by ID.
        
        Args:
            template_id: Template ID.
        
        Returns:
            Email template or None.
        """
        return self.templates.get(template_id)