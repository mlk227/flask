import logging

import requests
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import validate_email
from django.db.models import Q, Sum, F, FloatField
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status, generics
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from app1.models import UserAccount

logger = logging.getLogger(__name__)


class CustomMessage(Exception):
    def __init__(self, message):
        self.message = message


def jwt_get_secret_key(user):
    return user.jwt_secret


class DataRender(APIView):
    permission_classes = (AllowAny, )

    def get(self, request, *args, **kwargs):
        try:
            country_code = 28   # As Task says Myanmar is fixed
            item_codes = {
                "Rice, paddy": "27",
                "Maize": "56",
                "Sugar Cane": "156"
            }
            element_codes = {
                "Area harvested": "2312",
                "Yield": "2413",
                "Production Quantity": "2510"
            }
            try:
                item_code = request.query_params['item_code']
                element_code = request.query_params['element_code']
                year = request.query_params['year']
            except ValueError:
                raise CustomMessage("Provide Values for item_code, element_code, year")

            item_list = item_code.split(",")
            for i in item_list:
                if i not in list(item_codes.values()):
                    raise CustomMessage("item_code value must be 27 for Rice or Paddy, 56 for Maize, 156 for Sugar Cane")

            element_list = element_code.split(",")
            for i in element_list:
                if i not in list(element_codes.values()):
                    raise CustomMessage("element_code value must be 2312 for Area harvested, 2413 for Yield, 2510 for Production Quantity")

            year_list = year.split(",")
            for i in year_list:
                if int(i) < 1961 or int(i) > 2018:
                    raise CustomMessage("year value must be between 1961 and 2018")

            url = f"http://fenixservices.fao.org/faostat/api/v1/en/data/QC?area={country_code}&element={element_code}&item={item_code}&item_cs=FAO&year={year}&show_codes=true&show_unit=true&show_flags=true&null_values=false&page_number=1&page_size=100&output_type=objects"
            r = requests.get(url=url)

            return Response({"data": {"is_data_exist": True, "data": r.json()}}, status=status.HTTP_200_OK)
        except (ParseError, ZeroDivisionError, MultiValueDictKeyError, KeyError, ValueError, ValidationError,
                ObjectDoesNotExist):
            logger.info(f"class name: {self.__class__.__name__},request: {request.data}")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except CustomMessage as e:
            return Response({"data": {"is_data_exist": False, "message": e.message}}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"class name: {self.__class__.__name__},request: {request.data}, message: str({e})")
            return Response({"status": status.HTTP_500_INTERNAL_SERVER_ERROR, "message": "fail", "raw_message": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateUser(APIView):
    permission_classes = (AllowAny, )

    def post(self, request):
        try:
            first_name = request.data['first_name']
            password = request.data['password']
            email = request.data['email']
            if len(first_name) < 3 or len(first_name) > 14:
                raise CustomMessage("first_name must be between 3 and 14 Chars")
            if len(password) < 5 or len(password) > 10:
                raise CustomMessage("password must be between 5 and 10 Chars")
            try:
                validate_email(email)
            except validate_email.ValidationError:
                raise CustomMessage("Email is not Valid")
            try:
                UserAccount.objects.get(email=email)
                raise CustomMessage("Email is already Registered")
            except UserAccount.DoesNotExist:
                UserAccount.objects.create_user(email=email, first_name=first_name, password=password)
                user_obj = UserAccount.objects.get(email=email)
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user_obj)
            del payload['email']
            payload["first_name"] = user_obj.first_name
            token = jwt_encode_handler(payload)
            return Response({"data": {"is_account_created": True, "first_name": first_name, "message": "Success", "token": token}},
                            status=status.HTTP_200_OK)
        except CustomMessage as e:
            return Response({"data": {"is_account_created": False, "message": e.message}}, status=status.HTTP_200_OK)
        except (ParseError, ZeroDivisionError, MultiValueDictKeyError, KeyError, ValueError, ValidationError):
            logger.debug(f"class name: {self.__class__.__name__},request: {request.data}")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"class name: {self.__class__.__name__},request: {request.data}, message: str({e})")
            return Response(
                {"status": status.HTTP_500_INTERNAL_SERVER_ERROR, "message": "fail", "raw_message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLogin(APIView):
    permission_classes = (AllowAny, )

    def post(self, request):
        try:
            password = request.data['password']
            email = request.data['email']
            try:
                user_obj = UserAccount.objects.get(email=email)
            except UserAccount.DoesNotExist:
                raise CustomMessage("Email is already Registered")
            user = authenticate(username=user_obj.user_id, password=password)
            if user is None:
                raise CustomMessage("Credentials didn't match")
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user_obj)
            del payload['email']
            payload["first_name"] = user_obj.first_name
            token = jwt_encode_handler(payload)
            return Response({"data": {"is_login": True, "first_name": user_obj.first_name, "message": "Success", "token": token}},
                            status=status.HTTP_200_OK)
        except CustomMessage as e:
            return Response({"data": {"is_login": False, "message": e.message}}, status=status.HTTP_200_OK)
        except (ParseError, ZeroDivisionError, MultiValueDictKeyError, KeyError, ValueError, ValidationError):
            logger.debug(f"class name: {self.__class__.__name__},request: {request.data}")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"class name: {self.__class__.__name__},request: {request.data}, message: str({e})")
            return Response(
                {"status": status.HTTP_500_INTERNAL_SERVER_ERROR, "message": "fail", "raw_message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
