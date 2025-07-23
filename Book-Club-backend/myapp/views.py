from django.shortcuts import render

def home(request):
    return render(request, 'myapp/home.html', {'message': 'Welcome to My Django App!'})
