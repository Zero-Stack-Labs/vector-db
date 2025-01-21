import os
import importlib
import pkgutil

# Importa automáticamente todos los módulos en el directorio app
__all__ = []

# Obtener el path del directorio app
app_path = os.path.join(os.path.dirname(__file__), 'app')

# Importar todos los módulos recursivamente
for loader, module_name, is_pkg in pkgutil.walk_packages([app_path]):
    __all__.append(module_name)
    _module = loader.find_module(module_name).load_module(module_name)
    globals().update({name: getattr(_module, name) for name in dir(_module)
                     if not name.startswith('_')}) 