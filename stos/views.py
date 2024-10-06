from django.shortcuts import render
from django.views import View


class IndexView(View):
    def get(self, request):
        data = {
            "title": "Home",
        }
        return render(request, 'index.html', data)
