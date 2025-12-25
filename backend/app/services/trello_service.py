# import requests
# import logging
# from typing import List, Optional, Dict

# import google.generativeai as genai

# from app.models.schemas import ReviewPoint, ReviewCategory
# from app.config import settings

# logger = logging.getLogger(__name__)

# CRITICAL_ICON = "⚠"  
# MISSING_ICON = "✖"   

# class TrelloService:
#     BASE_URL = "https://api.trello.com/1"

#     def __init__(self, api_key: str, token: str):
#         self.auth_params = {
#             "key": api_key,
#             "token": token,
#         }

#         # Initialize Gemini if key exists
#         if settings.google_api_key:
#             genai.configure(api_key=settings.google_api_key)
#             self.model = genai.GenerativeModel("gemini-2.5-flash")
#         else:
#             self.model = None
#             logger.warning("GOOGLE_API_KEY not found. Trello titles will be basic.")

#     async def generate_ai_title(
#         self,
#         category: str,
#         advice: str,
#         quote: Optional[str],
#     ) -> str:
#         """
#         Generates a smart title using Gemini.
#         Falls back to basic string manipulation if API fails or quota is exceeded.
#         """
#         icon = CRITICAL_ICON if category == "CRITICAL" else MISSING_ICON

#         # --- Fallback Logic (Reuseable) ---
#         def basic_fallback():
#             # Grab first sentence, remove fluff
#             base = advice.split('.')[0]
#             base = base.replace("Advice:", "").replace("Review:", "").strip()
#             if len(base) > 60:
#                 base = base[:57] + "..."
#             return f"{icon} {base}"

#         if not self.model:
#             return basic_fallback()

#         try:
#             prompt = (
#                 "Summarize the following legal advice into a SINGLE, short, "
#                 "action-oriented task title (max 7 words). "
#                 "Do NOT use quotes or markdown.\n\n"
#                 f"Advice:\n{advice}\n\n"
#                 f"Original Clause:\n{quote or 'Clause missing'}"
#             )

#             response = await self.model.generate_content_async(prompt)
            
#             clean_title = (
#                 response.text
#                 .strip()
#                 .replace('"', "")
#                 .replace("*", "")
#                 .replace("\n", " ")
#             )

#             if not clean_title:
#                 return basic_fallback()

#             return f"{icon} {clean_title}"

#         except Exception as e:
#             # Handle Quota/Rate Limit Errors Gracefully
#             if "429" in str(e) or "Quota exceeded" in str(e):
#                 logger.warning(f"Gemini Quota Exceeded. Switching to basic title for this card.")
#             else:
#                 logger.error(f"Gemini title generation failed: {e}")
            
#             return basic_fallback()

#     def get_or_create_list(self, board_id: str, list_name: str) -> str:
#         """Finds a list on the board or creates it if missing."""
#         # 1. Fetch existing lists
#         url = f"{self.BASE_URL}/boards/{board_id}/lists"
#         response = requests.get(url, params=self.auth_params)
#         response.raise_for_status()

#         for lst in response.json():
#             if lst["name"].lower() == list_name.lower():
#                 return lst["id"]

#         # 2. Create if not found
#         create_url = f"{self.BASE_URL}/lists"
#         payload = {
#             **self.auth_params,
#             "name": list_name,
#             "idBoard": board_id,
#             "pos": "top",
#         }

#         resp = requests.post(create_url, params=payload)
#         resp.raise_for_status()
#         return resp.json()["id"]

#     def create_card(
#         self,
#         list_id: str,
#         name: str,
#         desc: str,
#         labels: Optional[List[str]] = None,
#     ):
#         """Creates the card on Trello."""
#         url = f"{self.BASE_URL}/cards"

#         # Auth in Params, Data in Body (Safe for long text)
#         query_params = {
#             'key': self.auth_params['key'],
#             'token': self.auth_params['token']
#         }
        
#         body_data = {
#             "idList": list_id,
#             "name": name,
#             "desc": desc,
#             "pos": "top",
#         }

#         response = requests.post(url, params=query_params, json=body_data)
#         response.raise_for_status()
#         card_data = response.json()

#         # Add Visual Labels
#         label_colors = {
#             "CRITICAL": "red",
#             "MISSING": "sky",
#         }

#         if labels:
#             for label in labels:
#                 color = label_colors.get(label, "grey")
#                 try:
#                     requests.post(
#                         f"{self.BASE_URL}/cards/{card_data['id']}/labels",
#                         params={
#                             **self.auth_params,
#                             "color": color,
#                             "name": label,
#                         },
#                     )
#                 except Exception:
#                     pass

#         return card_data

#     async def sync_findings_to_trello(
#         self,
#         board_id: str,
#         review_points: List[ReviewPoint],
#         filters: List[str],
#     ) -> int:
#         """
#         Main function to sync findings to specific lists on a board.
#         """
#         list_map: Dict[str, str] = {}

#         # Pre-fetch or Create Lists based on filters
#         if "CRITICAL" in filters:
#             list_map["CRITICAL"] = self.get_or_create_list(
#                 board_id,
#                 f"{CRITICAL_ICON} Critical Issues",
#             )

#         if "MISSING" in filters:
#             list_map["MISSING"] = self.get_or_create_list(
#                 board_id,
#                 f"{MISSING_ICON} Missing Clauses",
#             )

#         cards_created = 0

#         print(f"DEBUG: Starting Trello Sync for {len(review_points)} points. Filters: {filters}")

#         for point in review_points:
#             category = point.category.value

#             # Skip if not in requested filters or list not set up
#             if category not in filters or category not in list_map:
#                 continue

#             # Generate Title (Async)
#             title = await self.generate_ai_title(
#                 category=category,
#                 advice=point.advice,
#                 quote=point.quote,
#             )

#             description = (
#                 f"**Action Required:**\n{point.advice}\n\n"
#                 f"---\n"
#                 f"**Legal Reference:**\n{point.legal_reference}\n\n"
#                 f"**Original Text:**\n> "
#                 f"{point.quote if point.quote else '(Clause Missing)'}"
#             )

#             try:
#                 self.create_card(
#                     list_id=list_map[category],
#                     name=title,
#                     desc=description,
#                     labels=[category],
#                 )
#                 cards_created += 1
#             except Exception as e:
#                 logger.error(f"Failed to create card for {title}: {e}")

#         return cards_created

# trello_service: Optional[TrelloService] = None

# if settings.trello_api_key and settings.trello_token_key:
#     trello_service = TrelloService(
#         api_key=settings.trello_api_key,
#         token=settings.trello_token_key,
#     )

import requests
import logging
from typing import List, Optional, Dict

import google.generativeai as genai

from app.models.schemas import ReviewPoint, ReviewCategory
from app.config import settings

logger = logging.getLogger(__name__)

CRITICAL_ICON = "⚠"
MISSING_ICON = "✖"


class TrelloService:
    BASE_URL = "https://api.trello.com/1"

    def __init__(self, api_key: str, token: str):
        self.auth_params = {
            "key": api_key,
            "token": token,
        }

        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
        else:
            self.model = None

    async def generate_ai_title(
        self,
        category: str,
        advice: str,
        quote: Optional[str],
    ) -> str:
        icon = CRITICAL_ICON if category == "CRITICAL" else MISSING_ICON

        def basic_fallback():
            base = advice.split(".")[0].strip()
            if len(base) > 60:
                base = base[:57] + "..."
            return f"{icon} {base}"

        if not self.model:
            return basic_fallback()

        try:
            prompt = (
                "Summarize the following legal advice into a SINGLE, short, "
                "action-oriented task title (max 7 words). "
                "Do NOT use quotes or markdown.\n\n"
                f"Advice:\n{advice}\n\n"
                f"Original Clause:\n{quote or 'Clause missing'}"
            )

            response = await self.model.generate_content_async(prompt)

            clean_title = (
                response.text
                .strip()
                .replace('"', "")
                .replace("*", "")
                .replace("\n", " ")
            )

            if not clean_title:
                return basic_fallback()

            return f"{icon} {clean_title}"

        except Exception:
            return basic_fallback()

    def get_or_create_list(self, board_id: str, list_name: str) -> str:
        url = f"{self.BASE_URL}/boards/{board_id}/lists"
        response = requests.get(url, params=self.auth_params)
        response.raise_for_status()

        for lst in response.json():
            if lst["name"].lower() == list_name.lower():
                return lst["id"]

        create_url = f"{self.BASE_URL}/lists"
        payload = {
            **self.auth_params,
            "name": list_name,
            "idBoard": board_id,
            "pos": "top",
        }

        resp = requests.post(create_url, params=payload)
        resp.raise_for_status()
        return resp.json()["id"]

    def create_card(
        self,
        list_id: str,
        name: str,
        desc: str,
        labels: Optional[List[str]] = None,
    ):
        url = f"{self.BASE_URL}/cards"

        response = requests.post(
            url,
            params=self.auth_params,
            json={
                "idList": list_id,
                "name": name,
                "desc": desc,
                "pos": "top",
            },
        )
        response.raise_for_status()
        card_data = response.json()

        label_colors = {
            "CRITICAL": "red",
            "MISSING": "sky",
        }

        if labels:
            for label in labels:
                color = label_colors.get(label, "grey")
                try:
                    requests.post(
                        f"{self.BASE_URL}/cards/{card_data['id']}/labels",
                        params={
                            **self.auth_params,
                            "color": color,
                            "name": label,
                        },
                    )
                except Exception:
                    pass

        return card_data

    async def sync_findings_to_trello(
        self,
        board_id: str,
        review_points: List[ReviewPoint],
        filters: List[str],
    ) -> int:
        list_map: Dict[str, str] = {}

        if "CRITICAL" in filters:
            list_map["CRITICAL"] = self.get_or_create_list(
                board_id,
                f"{CRITICAL_ICON} Critical Issues",
            )

        if "MISSING" in filters:
            list_map["MISSING"] = self.get_or_create_list(
                board_id,
                f"{MISSING_ICON} Missing Clauses",
            )

        cards_created = 0
        category_count: Dict[str, int] = {
            "CRITICAL": 0,
            "MISSING": 0,
        }

        for point in review_points:
            category = point.category.value

            if category not in filters or category not in list_map:
                continue

            if category_count[category] >= 3:
                continue

            title = await self.generate_ai_title(
                category=category,
                advice=point.advice,
                quote=point.quote,
            )

            description = (
                f"**Action Required:**\n{point.advice}\n\n"
                f"---\n"
                f"**Legal Reference:**\n{point.legal_reference}\n\n"
                f"**Original Text:**\n> "
                f"{point.quote if point.quote else '(Clause Missing)'}"
            )

            try:
                self.create_card(
                    list_id=list_map[category],
                    name=title,
                    desc=description,
                    labels=[category],
                )
                cards_created += 1
                category_count[category] += 1
            except Exception:
                pass

        return cards_created


trello_service: Optional[TrelloService] = None

if settings.trello_api_key and settings.trello_token_key:
    trello_service = TrelloService(
        api_key=settings.trello_api_key,
        token=settings.trello_token_key,
    )
