from django.urls import path

from app1 import views

urlpatterns = [
    #   Homepage
    path('faostat/data', views.DataRender.as_view()),
    path('faostat/user/create/', views.CreateUser.as_view()),
    path('faostat/user/login/', views.UserLogin.as_view()),

]