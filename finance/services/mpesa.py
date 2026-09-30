import base64
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class MpesaService:
    """
    Safaricom Daraja M-Pesa service.

    This service:
    - Gets a Daraja access token
    - Generates the STK Push password
    - Normalizes Kenyan phone numbers
    - Validates payment amounts
    - Sends STK Push requests
    - Provides useful error information
    """

    # ============================================================
    # ACCESS TOKEN
    # ============================================================

    @staticmethod
    def get_access_token():
        url = (
            f"{settings.MPESA_BASE_URL}"
            "/oauth/v1/generate?grant_type=client_credentials"
        )

        try:
            response = requests.get(
                url,
                auth=(
                    settings.MPESA_CONSUMER_KEY,
                    settings.MPESA_CONSUMER_SECRET,
                ),
                timeout=30,
            )

            logger.info(
                "M-Pesa access token response: %s",
                response.status_code
            )

            response.raise_for_status()

            data = response.json()

            access_token = data.get("access_token")

            if not access_token:
                raise ValueError(
                    "M-Pesa did not return an access token."
                )

            return access_token

        except requests.exceptions.RequestException as exc:
            logger.error(
                "M-Pesa access token request failed: %s",
                exc
            )

            if exc.response is not None:
                logger.error(
                    "Daraja response: %s",
                    exc.response.text
                )

            raise RuntimeError(
                "Unable to connect to M-Pesa. "
                "Please check your Daraja credentials and internet connection."
            ) from exc

        except ValueError as exc:
            logger.error(
                "Invalid M-Pesa access token response: %s",
                exc
            )
            raise


    # ============================================================
    # PHONE NUMBER NORMALIZATION
    # ============================================================

    @staticmethod
    def normalize_phone_number(phone_number):
        """
        Convert common Kenyan phone formats to:

        2547XXXXXXXX

        Examples:

        0712345678
        +254712345678
        254712345678
        712345678

        all become:

        254712345678
        """

        if not phone_number:
            raise ValueError("Phone number is required.")

        phone = str(phone_number).strip()

        # Remove spaces, hyphens and brackets
        phone = (
            phone
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        # +254712345678 -> 254712345678
        if phone.startswith("+254"):
            phone = phone[1:]

        # 0712345678 -> 254712345678
        elif phone.startswith("0"):
            phone = "254" + phone[1:]

        # 712345678 -> 254712345678
        elif phone.startswith("7") and len(phone) == 9:
            phone = "254" + phone

        # Validate final format
        if (
            len(phone) != 12
            or not phone.isdigit()
            or not phone.startswith("2547")
        ):
            raise ValueError(
                "Invalid Kenyan phone number. "
                "Use a number such as 0712345678."
            )

        return phone


    # ============================================================
    # AMOUNT VALIDATION
    # ============================================================

    @staticmethod
    def normalize_amount(amount):
        """
        Convert the payment amount into a valid whole-number
        M-Pesa amount.
        """

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Invalid payment amount.")

        if amount <= 0:
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        # STK Push uses whole KES
        if amount != amount.to_integral_value():
            raise ValueError(
                "M-Pesa payment amount must be a whole number."
            )

        return int(amount)


    # ============================================================
    # GENERATE PASSWORD
    # ============================================================

    @staticmethod
    def generate_password(timestamp):
        """
        Daraja password:

        Base64(
            Shortcode + Passkey + Timestamp
        )
        """

        raw = (
            f"{settings.MPESA_SHORTCODE}"
            f"{settings.MPESA_PASSKEY}"
            f"{timestamp}"
        )

        return base64.b64encode(
            raw.encode("utf-8")
        ).decode("utf-8")


    # ============================================================
    # STK PUSH
    # ============================================================

    @staticmethod
    def stk_push(
        phone_number,
        amount,
        account_reference,
        transaction_desc,
    ):
        """
        Send an STK Push to the customer's phone.
        """

        # --------------------------------------------------------
        # Normalize and validate phone
        # --------------------------------------------------------

        phone_number = MpesaService.normalize_phone_number(
            phone_number
        )

        # --------------------------------------------------------
        # Normalize and validate amount
        # --------------------------------------------------------

        amount = MpesaService.normalize_amount(amount)

        # --------------------------------------------------------
        # Timestamp
        # --------------------------------------------------------

        timestamp = datetime.now().strftime(
            "%Y%m%d%H%M%S"
        )

        # --------------------------------------------------------
        # Generate password
        # --------------------------------------------------------

        password = MpesaService.generate_password(
            timestamp
        )

        # --------------------------------------------------------
        # Get access token
        # --------------------------------------------------------

        access_token = MpesaService.get_access_token()

        # --------------------------------------------------------
        # STK Push URL
        # --------------------------------------------------------

        url = (
            f"{settings.MPESA_BASE_URL}"
            "/mpesa/stkpush/v1/processrequest"
        )

        # --------------------------------------------------------
        # Headers
        # --------------------------------------------------------

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # --------------------------------------------------------
        # Request payload
        # --------------------------------------------------------

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": str(account_reference),
            "TransactionDesc": str(transaction_desc),
        }

        # --------------------------------------------------------
        # Safe logging
        # --------------------------------------------------------

        logger.info(
            "Sending M-Pesa STK Push | Phone=%s | Amount=%s | "
            "Reference=%s",
            phone_number,
            amount,
            account_reference,
        )

        # --------------------------------------------------------
        # Send request
        # --------------------------------------------------------

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30,
            )

            logger.info(
                "Daraja STK response status: %s",
                response.status_code
            )

            logger.info(
                "Daraja STK response: %s",
                response.text
            )

            response.raise_for_status()

        except requests.exceptions.RequestException as exc:

            logger.error(
                "Daraja STK Push request failed: %s",
                exc
            )

            if exc.response is not None:
                logger.error(
                    "Daraja error response: %s",
                    exc.response.text
                )

            raise RuntimeError(
                "Unable to communicate with M-Pesa."
            ) from exc

        # --------------------------------------------------------
        # Parse response
        # --------------------------------------------------------

        try:
            data = response.json()
        except ValueError as exc:
            logger.error(
                "Daraja returned an invalid JSON response: %s",
                response.text
            )

            raise RuntimeError(
                "M-Pesa returned an invalid response."
            ) from exc

        # --------------------------------------------------------
        # Check Daraja response
        # --------------------------------------------------------

        response_code = data.get("ResponseCode")

        if response_code != "0":
            error_message = (
                data.get("ResponseDescription")
                or data.get("errorMessage")
                or "M-Pesa rejected the STK Push request."
            )

            logger.error(
                "M-Pesa STK Push rejected: %s",
                error_message
            )

            raise RuntimeError(error_message)

        # --------------------------------------------------------
        # Verify important IDs exist
        # --------------------------------------------------------

        checkout_request_id = data.get(
            "CheckoutRequestID"
        )

        merchant_request_id = data.get(
            "MerchantRequestID"
        )

        if not checkout_request_id:
            raise RuntimeError(
                "M-Pesa did not return a CheckoutRequestID."
            )

        logger.info(
            "M-Pesa STK Push accepted | "
            "MerchantRequestID=%s | CheckoutRequestID=%s",
            merchant_request_id,
            checkout_request_id,
        )

        return data




# import base64
# import requests
# from datetime import datetime
# from django.conf import settings


# class MpesaService:

#     @staticmethod
#     def get_access_token():
#         url = (
#             f"{settings.MPESA_BASE_URL}"
#             "/oauth/v1/generate?grant_type=client_credentials"
#         )

#         response = requests.get(
#             url,
#             auth=(
#                 settings.MPESA_CONSUMER_KEY,
#                 settings.MPESA_CONSUMER_SECRET,
#             ),
#             timeout=30,
#         )

#         print("\n========== M-PESA ACCESS TOKEN ==========")
#         print("URL:", url)
#         print("STATUS:", response.status_code)
#         print("RESPONSE:", response.text)
#         print("=========================================\n")

#         response.raise_for_status()

#         return response.json()["access_token"]

#     @staticmethod
#     def generate_password(timestamp):
#         raw = (
#             f"{settings.MPESA_SHORTCODE}"
#             f"{settings.MPESA_PASSKEY}"
#             f"{timestamp}"
#         )

#         return base64.b64encode(
#             raw.encode()
#         ).decode()

#     @staticmethod
#     def stk_push(
#         phone_number,
#         amount,
#         account_reference,
#         transaction_desc,
#     ):
#         # =========================================
#         # TIMESTAMP
#         # =========================================
#         timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

#         print("\n========== M-PESA STK PUSH ==========")
#         print("Phone:", phone_number)
#         print("Amount:", amount)
#         print("Shortcode:", settings.MPESA_SHORTCODE)
#         print("Base URL:", settings.MPESA_BASE_URL)
#         print("Callback URL:", settings.MPESA_CALLBACK_URL)

#         # =========================================
#         # PASSWORD
#         # =========================================
#         password = MpesaService.generate_password(timestamp)

#         # =========================================
#         # ACCESS TOKEN
#         # =========================================
#         access_token = MpesaService.get_access_token()

#         # =========================================
#         # STK PUSH URL
#         # =========================================
#         url = (
#             f"{settings.MPESA_BASE_URL}"
#             "/mpesa/stkpush/v1/processrequest"
#         )

#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json",
#         }

#         payload = {
#             "BusinessShortCode": settings.MPESA_SHORTCODE,
#             "Password": password,
#             "Timestamp": timestamp,
#             "TransactionType": "CustomerPayBillOnline",
#             "Amount": int(amount),
#             "PartyA": phone_number,
#             "PartyB": settings.MPESA_SHORTCODE,
#             "PhoneNumber": phone_number,
#             "CallBackURL": settings.MPESA_CALLBACK_URL,
#             "AccountReference": account_reference,
#             "TransactionDesc": transaction_desc,
#         }

#         print("STK URL:", url)
#         print("STK request prepared.")

#         # =========================================
#         # SEND STK PUSH
#         # =========================================
#         try:
#             response = requests.post(
#                 url,
#                 json=payload,
#                 headers=headers,
#                 timeout=30,
#             )

#             print("\n========== DARaja RESPONSE ==========")
#             print("STATUS:", response.status_code)
#             print("RESPONSE:", response.text)
#             print("=====================================\n")

#             response.raise_for_status()

#             return response.json()

#         except requests.exceptions.RequestException as e:

#             print("\n========== DARaja ERROR ==========")
#             print("ERROR:", repr(e))

#             if e.response is not None:
#                 print("STATUS:", e.response.status_code)
#                 print("BODY:", e.response.text)

#             print("==================================\n")

#             raise


