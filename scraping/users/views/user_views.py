import logging

from rest_framework.generics import CreateAPIView, ListAPIView

from ...models import Bicycle
from ..serializers import UserSerializer, BicycleSerializer, SigninSerializer

logger = logging.getLogger(__name__)

class SignupView(CreateAPIView):
    serializer_class = UserSerializer

class SearchBicycleView(ListAPIView):
    serializer_class = BicycleSerializer

    def get_queryset(self):
        max_results = 50
        qs = Bicycle.objects.all()
        query = (self.request.query_params.get("q") or "").strip()
        
        if not query:
            return qs[:max_results]

        if query.isdigit():
            qs = qs.filter(reference=query)
        else:
            qs = qs.filter(name__icontains=query)

        return qs.order_by("price")[:max_results]
    
class SigninView(ListAPIView):
    serializer_class = SigninSerializer