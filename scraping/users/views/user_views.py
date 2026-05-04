from rest_framework.generics import CreateAPIView, ListAPIView 
from django.db

from ...models import Bicycle
from ..serializers import UserSerializer, BicycleSerializer

class SignupView(CreateAPIView):
    serializer_class = UserSerializer

class SearchBicycleView(ListAPIView):
    serializer_class = BicycleSerializer

    def get_queryset(self):
        qs = Bicycle.objects.all()
        query = self.request.query_params.get("q")
        try:
            query_int = int(query)
            qs.filter(reference=query_int)
        except:
            try:
                qs.filter(name__icontains=query)
            except 
        return Bicycle.objects.filter(name__icontains=query)