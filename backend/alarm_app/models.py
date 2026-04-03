from django.db import models
import uuid

class RoomObjects(models.Model):
    CATEGORY_CHOICES = [
    ("furniture", "Furniture"),
    ("electronics", "Electronics"),
    ("kitchen", "Kitchen"),
    ("decor", "Decor"), 
    ("other", "Other"),
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    hint = models.CharField(max_length=200, help_text="Hint shown to user when challened")
    emoji = models.CharField(max_length=10, default="📦")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.emoji} {self.name}"
    
class Alarm(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=100, default="Wake Up!")
    time = models.TimeField()
    days = models.JSONField(default=list, help_text="List of weekday ints 0=Mon..6=Sun")
    is_active = models.BooleanField(default=True)
    snooze_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label} @ {self.time}"

class AlarmSession(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("triggered", "Triggered"),
        ("solved", "Solved"),
        ("snoozed", "Snoozed"),
        ("dismissed", "Dismissed"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alarm = models.ForeignKey(Alarm, on_delete=models.CASCADE, related_name="sessions" )
    assigned_object = models.ForeignKey(RoomObjects, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    triggered_at = models.DateTimeField(null=True, blank=True)
    solved_at = models.DateTimeField(null=True, blank=True)
    photo_path = models.CharField(max_length=500, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)
    ai_detected_label = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Session {self.id} - {self.status}"