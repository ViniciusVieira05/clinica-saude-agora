from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations


class Migration(migrations.Migration):
    """Ativa a extensão btree_gist, usada pela regra que impede consultas sobrepostas."""

    dependencies = []

    operations = [BtreeGistExtension()]
