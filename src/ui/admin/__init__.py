# src/ui/admin/__init__.py
from src.ui.admin._common import es_admin_luis
from src.ui.admin.operaciones import mostrar_operaciones
from src.ui.admin.extra import mostrar_extra

__all__ = ['es_admin_luis', 'mostrar_operaciones', 'mostrar_extra']
