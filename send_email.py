import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# Define the email sender and recipient
sender_email = "your email number"
# receiver_email = 'mulugetateamrat9@gmail.com'
password = "google generated password"  # App password if using Gmail



def send_email(receiver_email, message_to_be_sent, subject):
    try:

# Create the email message
        message = MIMEMultipart()

        # start simple mail transfer protocol server 
        server = smtplib.SMTP('smtp.gmail.com', 587)

        message['From'] = 'Fike-Online-Banking'
        message['To'] = receiver_email
        message['Subject'] = subject

        # Email body
        body = message_to_be_sent

        # Attach the body with the email
        message.attach(MIMEText(body, 'plain'))

        # Set up the SMTP server (this example uses Gmail's server)

        server.starttls()  # Secure connection

        # Log in to the server
        server.login(sender_email, password)

        # Send the email
        server.sendmail(sender_email, receiver_email, message.as_string())

        # Close the server connection
        server.quit()

    except Exception:
        return False


