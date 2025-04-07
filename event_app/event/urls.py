from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('contact-us/', views.contact_us, name='contact_us'),

    # Event-related URLs
    path('', views.EventListView.as_view(), name='home'),  # Home page with all events
    path('my-events/', views.MyEventsView.as_view(), name='my_events'),  # User's registered events
    path('events/<int:event_id>/pay/', views.initiate_payment, name='initiate_payment'),  # Payment initiation
    path('registration-success/<int:pk>/', views.registration_success, name='registration_success'),  # Success page for registration

    # Reminder-related URL (optional)
    path('events/<int:event_id>/reminder/', views.send_reminder, name='send_reminder'),
]