# Generated by Django 5.1.3 on 2024-12-29 07:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0014_directmessageroom_directmessage"),
    ]

    operations = [
        migrations.AddField(
            model_name="directmessage",
            name="image",
            field=models.ImageField(
                blank=True, null=True, upload_to="direct_messages/"
            ),
        ),
        migrations.AlterField(
            model_name="directmessage",
            name="content",
            field=models.TextField(blank=True),
        ),
    ]
