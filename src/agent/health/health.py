from dataclasses import dataclass
from typing import List, Optional
import json, os
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

class UserProfile(BaseModel):
    diet: Optional[str] = None          # e.g., "vegan", "keto", "vegetarian"
    allergies: List[str] = []           # e.g., ["peanuts", "gluten"]
    dislikes: List[str] = []            # e.g., ["mushrooms"]
    calories_target: Optional[int] = None
    weight: int
    height: int 

@dataclass
class HealthDeps:
    profile_file: str  # path to JSON file storing the profile

def _load_profile(path: str) -> UserProfile:
    if not os.path.exists(path):
        return UserProfile()
    with open(path, "r") as f:
        data = json.load(f)
    return UserProfile(**data)

def _save_profile(path: str, profile: UserProfile) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(profile.model_dump(), f, indent=2)

class HealthAnswer(BaseModel):
    answer: str

health_agent = Agent[HealthDeps, HealthAnswer](
    "groq:llama-3.1-8b-instant",
    deps_type=HealthDeps,
    output_type=HealthAnswer,
    instructions="""
    You are a health and nutrition assistant.
    - Read/update the user's health profile (diet, allergies, dislikes, calories).
    - Suggest 3 dish ideas aligned with the profile.
    - Avoid allergens/dislikes; align with diet. If info is missing, ask clarifying questions.
    - Suggest personalised diet plans if requested.
    - Keep answers concise.
    """,
    model_settings={"tool_choice": "auto"},
)

@health_agent.tool(name="get_profile")
def get_profile(ctx: RunContext[HealthDeps]) -> UserProfile:
    return _load_profile(ctx.deps.profile_file)

@health_agent.tool(name="update_profile")
def update_profile(
    ctx: RunContext[HealthDeps],
    diet: Optional[str] = None,
    allergies: Optional[List[str]] = None,
    dislikes: Optional[List[str]] = None,
    calories_target: Optional[int] = None,
) -> UserProfile:
    profile = _load_profile(ctx.deps.profile_file)
    if diet is not None:
        profile.diet = diet
    if allergies is not None:
        profile.allergies = allergies
    if dislikes is not None:
        profile.dislikes = dislikes
    if calories_target is not None:
        profile.calories_target = calories_target
    _save_profile(ctx.deps.profile_file, profile)
    return profile