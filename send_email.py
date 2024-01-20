from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, Email, FileContent, FileName, FileType, Disposition, Personalization
from python_http_client.exceptions import BadRequestsError
import base64
import mimetypes

import settings


def send_email(sendgrid_api_key, from_email, to_emails, subject, content, files):
    # Read the HTML template
    with open(settings.template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()

    # Replace the {{logo_url}} tag with the actual URL
    html_content = html_template.replace('{{logo_url}}', settings.logo_url)

    # Handle line breaks and escaped sequences
    content = content.replace('\\\\n', 'TEMP_PLACEHOLDER')  # Replace \\n with a placeholder
    content = content.replace('\\n', '<br>')  # Replace newline with <br>
    content = content.replace('TEMP_PLACEHOLDER', '\\\\n')  # Replace placeholder back with \\n

    # Replace the {{content}} tag with the processed content
    html_content = html_content.replace('{{content}}', content)
    
    mail = Mail(
        from_email=from_email,
        subject=subject,
        html_content=html_content  # Using the modified HTML content
    )
    
    # Create a separate Personalization object for each recipient
    for to_email in to_emails:
        personalization = Personalization()

        # Ensure to_email is an instance of Email
        if isinstance(to_email, str):
            to_email = Email(to_email)
        personalization.add_to(to_email)

        # Add the Personalization object to the Mail object
        mail.add_personalization(personalization)
    
    # Handle multiple attachments
    for file in files:
        with open(file, "rb") as f:
            encoded_file = base64.b64encode(f.read()).decode()

        # Dynamically determine the file_type based on the file extension
        file_type = mimetypes.guess_type(file)[0] or 'application/octet-stream'

        attachment = Attachment(
            file_content=FileContent(encoded_file),
            file_type=FileType(file_type),  # Set the file_type dynamically
            file_name=FileName(file),
            disposition=Disposition("attachment")
        )

        mail.add_attachment(attachment)
    
    client = SendGridAPIClient(sendgrid_api_key)
    try:
        response = client.send(mail)
        # Print success status
        print(f"Email sent successfully to {len(to_emails)} recipient(s).")
    except BadRequestsError as e:
        # Print failure status
        print(f"Email send failed.")
        print(e.body)
        raise

    return response