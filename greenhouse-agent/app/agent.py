# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Dict, List, Optional
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types
from google.cloud import firestore


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session to Memory Bank for extraction."""
    await callback_context.add_session_to_memory()
    return None
from .a2ui_prompt import A2UI_INSTRUCTION
from .a2ui_utils import a2ui_callback


MODEL = "gemini-3.8-flash"
# Hardcoded project ID as required for Agent Platform compatibility
PROJECT_ID = "qwiklabs-gcp-04-92a7633d9ea5"

_db: Optional[firestore.Client] = None


def get_db() -> firestore.Client:
    """Lazily initialize and return the Firestore client with hardcoded project ID."""
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def list_plants(
    light_level: Optional[str] = None,
    pet_safe_only: Optional[bool] = None,
    max_watering_days: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """List and filter houseplants available in the greenhouse inventory.

    Args:
        light_level: Optional filter by light requirements (e.g. 'low', 'bright', 'indirect').
        pet_safe_only: If True, only returns plants safe for cats and dogs.
        max_watering_days: If provided, only returns plants that can go at least this many days between waterings (lower maintenance).

    Returns:
        A list of matching plant dictionaries containing plant details.
    """
    db = get_db()
    docs = db.collection("plants").stream()
    results = []

    for doc in docs:
        plant = doc.to_dict()
        plant["id"] = doc.id

        if pet_safe_only is True and not plant.get("pet_safe", False):
            continue

        if light_level:
            light_req = plant.get("light_level", "").lower()
            if light_level.lower() not in light_req:
                continue

        if max_watering_days is not None:
            freq = plant.get("watering_frequency_days", 0)
            if freq < max_watering_days:
                continue

        results.append(plant)

    return results


def get_plant_details(plant_id: str) -> Dict[str, Any]:
    """Retrieve detailed care instructions, soil requirements, and pricing for a specific plant.

    Args:
        plant_id: The identifier of the plant (e.g. 'monstera-deliciosa', 'snake-plant', 'boston-fern').

    Returns:
        A dictionary with full plant and care details, or an error message if not found.
    """
    db = get_db()
    doc_ref = db.collection("plants").document(plant_id.strip().lower())
    doc = doc_ref.get()

    if not doc.exists:
        return {"error": f"Plant with ID '{plant_id}' not found in catalog."}

    data = doc.to_dict()
    data["id"] = doc.id
    return data


def add_plant(
    plant_id: str,
    name: str,
    light_level: str,
    watering_frequency_days: int,
    pet_safe: bool,
    care_difficulty: str = "easy",
    soil_type: str = "Well-draining potting mix",
    price_usd: float = 19.99,
    description: str = "",
) -> Dict[str, Any]:
    """Add or register a new houseplant in the inventory.

    Args:
        plant_id: Unique slug identifier for the plant (e.g., 'pothos-golden').
        name: Common name of the plant.
        light_level: Lighting requirements (e.g., 'low-light', 'bright-indirect').
        watering_frequency_days: Estimated days between waterings.
        pet_safe: True if non-toxic to pets, False otherwise.
        care_difficulty: Care level ('beginner', 'easy', 'moderate', 'intermediate', 'difficult').
        soil_type: Recommended soil or potting mix.
        price_usd: Retail price in USD.
        description: A short overview of the plant.

    Returns:
        Confirmation dictionary with the created plant data.
    """
    db = get_db()
    doc_id = plant_id.strip().lower()
    plant_data = {
        "id": doc_id,
        "name": name,
        "light_level": light_level,
        "watering_frequency_days": watering_frequency_days,
        "pet_safe": pet_safe,
        "care_difficulty": care_difficulty,
        "soil_type": soil_type,
        "price_usd": price_usd,
        "description": description,
        "in_stock": True,
    }
    db.collection("plants").document(doc_id).set(plant_data)
    return {"status": "success", "message": f"Added {name} to inventory", "plant": plant_data}


def calculate_watering_schedule(
    plant_id: str,
    season: str = "summer",
    pot_material: str = "plastic",
) -> Dict[str, Any]:
    """Calculate the estimated watering interval based on the plant, season, and pot material.

    Args:
        plant_id: Unique slug identifier for the plant (e.g. 'monstera-deliciosa', 'snake-plant').
        season: Current season ('spring', 'summer', 'fall', 'winter').
        pot_material: Pot type ('terracotta', 'ceramic', 'plastic').

    Returns:
        A dictionary with recommended watering interval in days, baseline frequency, and practical tips.
    """
    plant = get_plant_details(plant_id)
    if "error" in plant:
        return plant

    base_days = plant.get("watering_frequency_days", 7)
    adjusted = float(base_days)

    # Seasonal adjustment (plants grow faster in spring/summer, slower/dormant in winter)
    season_clean = season.strip().lower()
    if season_clean == "winter":
        adjusted *= 1.4
    elif season_clean == "summer":
        adjusted *= 0.85
    elif season_clean == "spring":
        adjusted *= 0.95

    # Pot material adjustment (terracotta is porous and dries fast, plastic retains moisture)
    pot_clean = pot_material.strip().lower()
    if "terracotta" in pot_clean or "clay" in pot_clean:
        adjusted *= 0.75
    elif "ceramic" in pot_clean or "glazed" in pot_clean:
        adjusted *= 1.05

    recommended_days = max(1, round(adjusted))

    return {
        "plant_name": plant.get("name"),
        "base_interval_days": base_days,
        "recommended_interval_days": recommended_days,
        "season": season,
        "pot_material": pot_material,
        "rule_of_thumb": (
            f"Water your {plant.get('name')} approximately every {recommended_days} days. "
            f"Always check that the top 1-2 inches of soil feel dry before adding water."
        ),
    }


def get_local_climate(city: str) -> Dict[str, Any]:
    """Fetch live temperature and relative humidity for a city to inform plant placement and watering advice.

    Uses Open-Meteo (free public meteorological API, no API key required).

    Args:
        city: City name (e.g. 'Seattle', 'Miami', 'Chicago', 'Denver').

    Returns:
        Dictionary containing current temperature (°C and °F), relative humidity %, and indoor plant climate advice.
    """
    import json
    import urllib.parse
    import urllib.request

    try:
        # Step 1: Geocode city name to lat/lon
        encoded_city = urllib.parse.quote(city.strip())
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1&language=en&format=json"
        geo_req = urllib.request.Request(geo_url, headers={"User-Agent": "greenhouse-agent/1.0"})
        with urllib.request.urlopen(geo_req, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode())

        results = geo_data.get("results")
        if not results:
            return {"error": f"Could not find coordinates for city: '{city}'"}

        location = results[0]
        lat, lon = location["latitude"], location["longitude"]
        resolved_name = f"{location.get('name')}, {location.get('country_code', '').upper()}"

        # Step 2: Fetch current meteorological conditions
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m"
        )
        weather_req = urllib.request.Request(weather_url, headers={"User-Agent": "greenhouse-agent/1.0"})
        with urllib.request.urlopen(weather_req, timeout=5) as resp:
            weather_data = json.loads(resp.read().decode())

        current = weather_data.get("current", {})
        temp_c = current.get("temperature_2m")
        temp_f = round((temp_c * 9 / 5) + 32, 1) if temp_c is not None else None
        humidity = current.get("relative_humidity_2m")

        humidity_advice = "Normal indoor conditions."
        if humidity is not None:
            if humidity < 40:
                humidity_advice = "Dry climate: Tropicals like Boston Fern and Calathea will benefit from a humidifier or pebble tray."
            elif humidity > 70:
                humidity_advice = "High humidity: Excellent for tropical foliage, but watch for fungus gnats or slow soil drying."

        return {
            "city": resolved_name,
            "temperature_c": temp_c,
            "temperature_f": temp_f,
            "relative_humidity_percent": humidity,
            "plant_climate_tip": humidity_advice,
        }
    except Exception as e:
        return {"error": f"Failed to fetch climate data for {city}: {str(e)}"}


def geocode_address(address: str) -> Dict[str, Any]:
    """Convert an address, neighborhood, or city name into geographic coordinates using the Google Geocoding API.

    Args:
        address: The address or place to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'Seattle, WA').

    Returns:
        Dictionary with formatted address, latitude, and longitude.
    """
    import os
    import json
    import urllib.parse
    import urllib.request

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "greenhouse-agent/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        if data.get("status") != "OK" or not data.get("results"):
            return {"error": f"Geocoding failed for '{address}': {data.get('status')} - {data.get('error_message', '')}"}

        first = data["results"][0]
        loc = first["geometry"]["location"]
        return {
            "address": first.get("formatted_address"),
            "latitude": loc["lat"],
            "longitude": loc["lng"],
        }
    except Exception as e:
        return {"error": f"Geocoding request failed: {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "florist",
    radius_meters: float = 5000.0,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """Search for nearby places of a given type around a location using the Google Places API (New).

    Args:
        latitude: Latitude of the center point.
        longitude: Longitude of the center point.
        place_type: Type of place to search for (e.g. 'florist', 'garden_center', 'home_goods_store').
        radius_meters: Radius in meters (default: 5000.0 meters, max 50000.0).
        max_results: Maximum number of places to return (default 5, max 20).

    Returns:
        A list of matching places with name, formatted address, and geographic location.
    """
    import os
    import json
    import urllib.request

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return [{"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}]

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
        "User-Agent": "greenhouse-agent/1.0",
    }
    payload = json.dumps({
        "includedTypes": [place_type.strip().lower()],
        "maxResultCount": min(max(1, max_results), 20),
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": float(radius_meters),
            }
        },
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        places = []
        for item in data.get("places", []):
            display_name = item.get("displayName", {}).get("text", "Unknown Place")
            address = item.get("formattedAddress", "")
            loc = item.get("location", {})
            places.append({
                "name": display_name,
                "address": address,
                "location": {
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude"),
                },
            })
        return places
    except Exception as e:
        return [{"error": f"Places search failed: {str(e)}"}]


# Hardcoded Cloud Storage bucket for greenhouse assets
GCS_BUCKET_NAME = "greenhouse-agent-assets-qwiklabs-gcp-04-92a7633d9ea5"


async def generate_plant_image(
    plant_name: str,
    tool_context: ToolContext,
    style_description: str = "healthy houseplant in a decorative ceramic pot, soft natural lighting, botanical photography",
) -> Dict[str, Any]:
    """Generate a photo or visual rendering of a houseplant using gemini-3.1-flash-lite-image.

    Saves the image into the agent's Artifacts panel and uploads it to public Cloud Storage.

    Args:
        plant_name: Name of the houseplant (e.g. 'Monstera Deliciosa', 'Calathea Orbifolia').
        style_description: Visual styling instructions (e.g. 'minimalist modern living room setting', 'close-up leaf fenestrations').

    Returns:
        Dictionary with status, artifact filename, and public https URL of the uploaded image.
    """
    import re
    import uuid
    from google import genai
    from google.cloud import storage

    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    prompt = f"Professional photograph of a {plant_name}, {style_description}"

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )

        image_bytes: Optional[bytes] = None
        mime_type = "image/jpeg"

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break

        if not image_bytes:
            return {"error": f"No image data returned from image model for {plant_name}"}

        clean_slug = re.sub(r"[^a-z0-9_-]", "", plant_name.lower().replace(" ", "-"))
        filename = f"{clean_slug}-{uuid.uuid4().hex[:8]}.jpg"

        # 1. Save as artifact in Playground's Artifacts panel
        part_artifact = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        try:
            await tool_context.save_artifact(filename=filename, artifact=part_artifact)
        except Exception as artifact_err:
            print(f"Warning: Failed to save artifact in context: {artifact_err}")

        # 2. Upload image bytes directly to the public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "plant_name": plant_name,
            "filename": filename,
            "image_url": public_url,
            "message": f"Generated image for {plant_name} and uploaded to {public_url}",
        }
    except Exception as e:
        return {"error": f"Image generation failed: {str(e)}"}


async def generate_plant_video(
    item_name: str,
    tool_context: ToolContext,
    video_description: str = "gentle time-lapse cinematic shot, soft natural sunlit breeze, botanical showcase",
) -> Dict[str, Any]:
    """Generate a short video clip for a houseplant or greenhouse item using Google's Omni model (gemini-omni-flash-preview).

    Saves the video as an artifact using tool_context.save_artifact so it appears in the
    Playground's Artifacts panel, and uploads the video bytes directly to the public Cloud Storage
    bucket, returning its public https URL.

    Args:
        item_name: Name of the houseplant or botanical item (e.g. 'Monstera Deliciosa', 'Fiddle Leaf Fig').
        video_description: Specific visual instructions for the video (e.g. 'leaf unfurling in morning light', 'water droplets trickling down the leaves').

    Returns:
        Dictionary with status, artifact filename, and public https URL of the uploaded video.
    """
    import base64
    import re
    import uuid
    from google import genai
    from google.cloud import storage

    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    prompt = f"A short video of {item_name}, {video_description}."

    try:
        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        output_video = getattr(interaction, "output_video", None)
        if not output_video or not getattr(output_video, "data", None):
            return {"error": f"No video data returned from Omni model for {item_name}"}

        video_bytes = base64.b64decode(output_video.data)
        mime_type = getattr(output_video, "mime_type", None) or "video/mp4"

        clean_slug = re.sub(r"[^a-z0-9_-]", "", item_name.lower().replace(" ", "-"))
        filename = f"{clean_slug}-{uuid.uuid4().hex[:8]}.mp4"

        # 1. Save artifact with tool_context.save_artifact for Playground's Artifacts panel
        part_artifact = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        try:
            await tool_context.save_artifact(filename=filename, artifact=part_artifact)
        except Exception as artifact_err:
            print(f"Warning: Failed to save video artifact in context: {artifact_err}")

        # 2. Upload video bytes to public Cloud Storage bucket without writing to a local file
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "item_name": item_name,
            "filename": filename,
            "video_url": public_url,
            "message": f"Generated video for {item_name} and uploaded to {public_url}",
        }
    except Exception as e:
        return {"error": f"Video generation failed: {str(e)}"}


# Agent Engine Sandbox resource from deployment_metadata.json
SANDBOX_RESOURCE_NAME = (
    "projects/986377528808/locations/us-east1/reasoningEngines/6721812659362070528/sandboxEnvironments/4935004009644687360"
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=A2UI_INSTRUCTION,
    tools=[
        PreloadMemoryTool(),
        list_plants,
        get_plant_details,
        add_plant,
        calculate_watering_schedule,
        get_local_climate,
        geocode_address,
        find_nearby_places,
        generate_plant_image,
        generate_plant_video,
    ],
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=SANDBOX_RESOURCE_NAME
    ),
    after_model_callback=a2ui_callback,

    after_agent_callback=generate_memories_callback,
)



app = App(
    root_agent=root_agent,
    name="app",
)





