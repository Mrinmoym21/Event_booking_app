from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    datetime = models.DateTimeField()
    venue = models.CharField(max_length=200)
    registration_deadline = models.DateTimeField()
    is_free = models.BooleanField(default=True)
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_registration_open(self):
        return timezone.now() < self.registration_deadline
    
    def __str__(self):
        return self.title

class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=255, blank=True)
    seat_number = models.CharField(max_length=10)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True)
    unique_code = models.UUIDField(default=uuid.uuid4, editable=False)
    
    def generate_seat_number(self):
        # Simple seat numbering logic
        last_seat = Registration.objects.filter(event=self.event).count()
        self.seat_number = f"{self.event.id}-{last_seat + 1:03d}"

    def generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        data = f"""
        Event: {self.event.title}
        User: {self.user.get_full_name()}
        Seat: {self.seat_number}
        Code: {self.unique_code}
        """
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        self.qr_code.save(f'qr_{self.unique_code}.png', File(buffer), save=False)

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

    



@receiver(post_save, sender=Registration)
def send_registration_confirmation(sender, instance, created, **kwargs):
    if created:
        subject = f"Event Registration Confirmation: {instance.event.title}"
        message = f"""
        Thank you for registering!
        
        Event: {instance.event.title}
        Date: {instance.event.datetime}
        Venue: {instance.event.venue}
        Seat Number: {instance.seat_number}
        """
        send_mail(
            subject,
            message,
            'mrinmoymandal2000@gmail.com',
            [instance.user.email],
            fail_silently=False,
        )

# Add celery task for reminders 24 hours before event


