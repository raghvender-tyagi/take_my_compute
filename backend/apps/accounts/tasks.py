from celery import shared_task
import time

@shared_task
def send_welcome_email(user_email):
    print(f"Starting to send welcome email to {user_email}...")
    time.sleep(2)  # Simulate sending email asynchronously
    print(f"Welcome email successfully sent to {user_email}!")
    return f"Success: Sent to {user_email}"
