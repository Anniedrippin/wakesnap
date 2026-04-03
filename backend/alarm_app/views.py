from rest_framework import generics
from .models import RoomObjects, Alarm, AlarmSession
from .serializers import RoomObjectSerializer, AlarmSerializer, AlarmSessionSerializer

class AlarmListCreateView(generics.ListCreateAPIView):
    queryset = Alarm.objects.all().order_by("time")  
    serializer_class = AlarmSerializer

class AlarmDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Alarm.objects.all()
    serializer_class = AlarmSerializer

class RoomObjectListView(generics.ListAPIView):
    queryset = RoomObjects.objects.filter(is_active=True)
    serializer_class = RoomObjectSerializer

class SessionListView(generics.ListAPIView):
    queryset = AlarmSession.objects.all().order_by("-triggered_at")[:50]
    serializer_class = AlarmSessionSerializer   