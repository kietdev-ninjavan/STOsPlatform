


from core.patterns import SingletonMeta
from google_wrapper.models import ServiceAccount
from google_wrapper.services import GoogleSheetService, GoogleChatService
from google_wrapper.utils import get_service_account
from google_wrapper.utils.card_builder import CardBuilder
from google_wrapper.utils.card_builder import widgets as W
from google_wrapper.utils.card_builder.elements import CardHeader, Section
from stos.utils import configs