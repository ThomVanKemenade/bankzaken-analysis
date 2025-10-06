# Import the functions from each page module
try:
    from .data_loader import data_loader
    from .category_management import category_management
except ImportError:
    # Fallback imports if relative imports don't work
    from data_loader import data_loader
    from category_management import category_management

__all__ = ['data_loader', 'category_management']