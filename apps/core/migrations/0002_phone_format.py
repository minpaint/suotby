# apps/core/migrations/0002_phone_format.py — телефоны в формате старого сайта: «+375 (29) 35-70-911»
from typing import Any

from django.db import migrations, models

# Старый формат по умолчанию → новый; номера, заданные вручную в админке, не трогаем
_REFORMAT = {
    "+375 29 357-09-11": "+375 (29) 35-70-911",
    "+375 33 357-09-11": "+375 (33) 35-70-911",
}


def reformat_phones(apps: Any, schema_editor: Any) -> None:
    """Переводит телефоны из прежнего формата по умолчанию в формат старого сайта."""
    SiteSettings = apps.get_model("core", "SiteSettings")
    for field in ("phone_1", "phone_2"):
        for old, new in _REFORMAT.items():
            SiteSettings.objects.filter(**{field: old}).update(**{field: new})


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="phone_1",
            field=models.CharField(
                default="+375 (29) 35-70-911", max_length=30, verbose_name="Телефон 1"
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="phone_2",
            field=models.CharField(
                blank=True, default="+375 (33) 35-70-911", max_length=30, verbose_name="Телефон 2"
            ),
        ),
        migrations.RunPython(reformat_phones, migrations.RunPython.noop),
    ]
