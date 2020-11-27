from __future__ import print_function
import base64
import os.path
import pickle
import yaml
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
CURR_DIR = os.path.dirname(__file__)


def get_creds():
    """Returns service credentials from oauth2
    Args:

    Returns:
    An object representing the authorized service
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_path = os.path.join(CURR_DIR, "token.pickle")
    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(CURR_DIR, "credentials.json"), SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)


def create_message(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

    Returns:
    An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    b64_bytes = base64.urlsafe_b64encode(message.as_bytes())
    b64_string = b64_bytes.decode()
    return {"raw": b64_string}


def send_message(service, user_id, message):
    """Send an email message.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

    Returns:
    Sent Message.
    """
    try:
        message = (
            service.users().messages().send(userId=user_id, body=message).execute()
        )
        print("Message Id: %s" % message["id"])
        return message
    except HttpError as error:
        print("An error occurred: %s" % error)


def main():
    """Reads and sends message from config file"""
    service = get_creds()
    meta_path = os.path.join(CURR_DIR, "meta.yml")
    with open(meta_path, "r") as stream:
        try:
            config = yaml.safe_load(stream)
            msg_data = config["message"]
            message = create_message(
                msg_data["sender"],
                msg_data["recipient"],
                msg_data["subject"],
                msg_data["body"],
            )
            send_message(service, "me", message)
        except yaml.YAMLError as exc:
            print(exc)


if __name__ == "__main__":
    main()
