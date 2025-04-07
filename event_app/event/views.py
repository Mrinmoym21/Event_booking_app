from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'auth/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')

def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        messages.success(request, "Your message has been sent successfully.")
        return redirect('home')
    
    return render(request, 'events/contact_us.html')

from django.views.generic import ListView, DetailView
from .models import Event, Registration
import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone


class EventListView(ListView):
    model = Event
    template_name = 'events/home.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        return Event.objects.filter(
            registration_deadline__gte=timezone.now()
        ).order_by('-datetime')

class MyEventsView(ListView):
    model = Registration
    template_name = 'events/my_events.html'
    context_object_name = 'registrations'
    
    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user)

def initiate_payment(request, event_id):
    event = Event.objects.get(id=event_id)
    existing_registration = Registration.objects.filter(event=event, user=request.user).exists()
    if existing_registration:
        # Display a message and redirect back to the home page or event details page
        messages.error(request, "You have already registered for this event.")
        return redirect('home')
    
    if event.is_free:
        # Handle free registration
        registration = Registration.objects.create(
            user=request.user,
            event=event
        )
        registration.generate_seat_number()
        registration.generate_qr_code()
        registration.save()
        return redirect('registration_success', pk=registration.id)
    
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    payment_data = {
        "amount": int(event.fee * 100),
        "currency": "INR",
        "receipt": f"event_{event.id}",
        "notes": {
            "user_id": request.user.id,
            "event_id": event.id
        }
    }
    
    order = client.order.create(data=payment_data)
    return JsonResponse({'order_id': order['id'], 'amount': order['amount']})

def registration_success(request, pk):
    registration = Registration.objects.get(pk=pk)
    return render(request, 'events/registration_success.html', {'registration': registration})


def my_events(request):
    registrations = Registration.objects.filter(user=request.user)
    return render(request, 'events/my_events.html', {'registrations': registrations})


from django.core.mail import send_mail

def send_reminder(request, event_id):
    if request.method == 'POST':
        event = Event.objects.get(id=event_id)
        send_mail(
            subject=f'Reminder: {event.title}',
            message=f'Dear {request.user.first_name},\n\nThis is a reminder for the event "{event.title}" happening on {event.datetime} at {event.venue}.',
            from_email='mrinmoymandal2000@gmail.com',
            recipient_list=[request.user.email],
            fail_silently=False,
        )
        return redirect('my_events')