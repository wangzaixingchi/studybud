# Generated by Django 5.1.4 on 2024-12-28 08:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0011_message_encrypted_body_room_encryption_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="room",
            name="is_encrypted",
            field=models.BooleanField(default=False),
        ),
    ]
