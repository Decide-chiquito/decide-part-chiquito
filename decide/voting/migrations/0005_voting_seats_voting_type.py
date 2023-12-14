# Generated by Django 4.1 on 2023-11-05 12:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0004_alter_voting_postproc_alter_voting_tally'),
    ]

    operations = [
        migrations.AddField(
            model_name='voting',
            name='seats',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='voting',
            name='type',
            field=models.CharField(choices=[('IDENTITY', 'Identity'), ('DHONDT', "D'Hondt"), ('WEBSTER, "Webster"')], default='IDENTITY', max_length=8),
        ),
    ]