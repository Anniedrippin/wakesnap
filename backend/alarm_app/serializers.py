from rest_framework import serializers
from .models import RoomObjects, Alarm, AlarmSession

class RoomObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomObjects
        fields = "__all__"

class AlarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alarm
        fields = "__all__"

class AlarmSessionSerializer(serializers.ModelSerializer):
    assigned_object = RoomObjectSerializer(read_only=True)
    alarm = AlarmSerializer(read_only=True)

    class Meta:
        model = AlarmSession
        fields= "__all__"
        
