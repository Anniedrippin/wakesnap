from django.urls import path
from . import views

urlpatterns = [
    path("alarms/", views.AlarmListCreateView.as_view(),name="alarm-list"),
    path("alarms/<uuid:pk>/", views.AlarmDetailView.as_view(),name="alarm-detail"),
    path("room-objects/", views.RoomObjectListView.as_view(),name="room-object"),
    path("sessions/", views.SessionListView.as_view(),name="session"), 
]