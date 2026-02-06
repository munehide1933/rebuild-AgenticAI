from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import UserProfile


class UserProfileService:
    """记录长期使用偏好，用于增强 MCP 上下文。"""

    DEFAULT_PROFILE_ID = "default"

    @staticmethod
    async def get_or_create_default_profile(db: AsyncSession) -> UserProfile:
        profile = await db.get(UserProfile, UserProfileService.DEFAULT_PROFILE_ID)
        if profile:
            return profile

        profile = UserProfile(
            id=UserProfileService.DEFAULT_PROFILE_ID,
            preferences={
                "preferred_domains": [],
                "key_concept_frequency": {},
                "feature_usage": {"deep_thinking": 0, "web_search": 0, "messages": 0},
                "last_intents": [],
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def update_from_interaction(
        db: AsyncSession,
        *,
        deep_thinking: bool,
        web_search_enabled: bool,
        question: str,
        intent_meta: dict[str, Any] | None,
    ) -> UserProfile:
        profile = await UserProfileService.get_or_create_default_profile(db)
        prefs = profile.preferences or {}

        feature_usage = dict(prefs.get("feature_usage", {}))
        feature_usage["messages"] = int(feature_usage.get("messages", 0)) + 1
        if deep_thinking:
            feature_usage["deep_thinking"] = int(feature_usage.get("deep_thinking", 0)) + 1
        if web_search_enabled:
            feature_usage["web_search"] = int(feature_usage.get("web_search", 0)) + 1
        prefs["feature_usage"] = feature_usage

        if intent_meta:
            domain = str(intent_meta.get("domain", "general"))
            concepts = intent_meta.get("key_concepts", [])
            if not isinstance(concepts, list):
                concepts = [str(concepts)]

            preferred_domains = list(prefs.get("preferred_domains", []))
            if domain and domain not in preferred_domains:
                preferred_domains.append(domain)
            prefs["preferred_domains"] = preferred_domains[-10:]

            concept_freq = dict(prefs.get("key_concept_frequency", {}))
            for concept in concepts:
                key = str(concept).strip()
                if not key:
                    continue
                concept_freq[key] = int(concept_freq.get(key, 0)) + 1
            prefs["key_concept_frequency"] = concept_freq

            intents = list(prefs.get("last_intents", []))
            intent_text = str(intent_meta.get("intent", ""))
            if intent_text:
                intents.append(intent_text)
            prefs["last_intents"] = intents[-20:]
        else:
            intents = list(prefs.get("last_intents", []))
            intents.append(question.strip()[:120])
            prefs["last_intents"] = intents[-20:]

        profile.preferences = prefs
        profile.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(profile)
        return profile
