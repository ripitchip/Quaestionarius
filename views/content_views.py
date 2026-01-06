from .main_view import MainView
from .forms_view import FormsView
from .settings_view import SettingsView

class Views:
    @staticmethod
    def get_view(name):
        # Map names to the CLASS (don't call () yet)
        views_map = {
            "Main": MainView,
            "Form": FormsView,
            "Settings": SettingsView,
        }
        
        # Get the class from the map, default to MainView
        view_class = views_map.get(name, MainView)
        
        # Initialize and return only the requested view
        return view_class()