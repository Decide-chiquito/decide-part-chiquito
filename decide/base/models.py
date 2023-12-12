from django.db import models

from auditlog.registry import AuditlogModelRegistry

class CustomLogEntry(AuditlogModelRegistry):
    entity_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Audits'

    def save(self, *args, **kwargs):
        # Asigna automáticamente el nombre de la entidad si aún no se ha establecido
        if not self.entity_name:
            self.entity_name = self.get_entity_name()  # Implementa get_entity_name() según tus necesidades
        super().save(*args, **kwargs)

    def get_entity_name(self):
        # Implementa lógica para obtener el nombre de la entidad aquí
        # Puede ser, por ejemplo, self.instance._meta.verbose_name
        return self.entity_name


class BigBigField(models.TextField):
    def to_python(self, value):
        if isinstance(value, str):
            return int(value)
        if value is None:
            return 0
        return int(str(value))

    def get_prep_value(self, value):
        if value is None:
            return 0
        return str(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return 0
        return int(value)


class Auth(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField()
    me = models.BooleanField(default=False)

    def __str__(self):
        return self.url


class Key(models.Model):
    p = BigBigField()
    g = BigBigField()
    y = BigBigField()
    x = BigBigField(blank=True, null=True)

    def __str__(self):
        if self.x:
            return "{},{},{},{}".format(self.p, self.g, self.y, self.x)
        else:
            return "{},{},{}".format(self.p, self.g, self.y)
