from .main_view import MainView
from .forms_view import FormsView
from .settings_view import SettingsView

class Views:
    _page = None
    
    @classmethod
    def set_page(cls, page):
        """Set the page reference for views that need it."""
        cls._page = page
    
    @classmethod
    def get_view(cls, name):
        # Map names to the CLASS (don't call () yet)
        views_map = {
            "Main": MainView,
            "Form": FormsView,
            "Settings": SettingsView,
        }
        
        # Get the class from the map, default to MainView
        view_class = views_map.get(name, MainView)
        
        # Initialize and return only the requested view
        if name == "Settings" and cls._page:
            return view_class(cls._page)
        return view_class()