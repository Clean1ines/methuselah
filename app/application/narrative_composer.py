import random
from typing import List, Dict
from app.core.config_registry import config_registry, Rule, MessageVariant
from app.core.logger import get_logger

logger = get_logger(__name__)

class NarrativeComposer:
    """Assembles the finalized message layout ensuring stable fallbacks."""
    def compose(self, selected_rules: List[Rule], streak_msg: str, history_texts: List[str]) -> Dict[str, str]:
        """Composes insights while respecting history to circumvent exact repetitions."""
        if not config_registry.messages_data:
            return {"text": "Наблюдение временно прервано. Конфигурация недоступна.", "tone": "neutral"}
        
        comp_cfg = config_registry.messages_data.composition
        messages_repo = config_registry.messages_data.messages
        
        parts: List[str] = []
        tones: List[str] = []
        
        if comp_cfg.add_streak_block and streak_msg:
            parts.append(streak_msg)

        for rule in selected_rules:
            msg_category = messages_repo.get(rule.message_id)
            if msg_category and msg_category.variants:
                variant = self._select_variant(msg_category.variants, history_texts)
                parts.append(variant.text)
                tones.append(variant.tone or "neutral")

        if random.random() < comp_cfg.add_bonus_probability:
            bonus_phrases = config_registry.messages_data.bonus_phrases
            if bonus_phrases:
                parts.append(f"*{random.choice(bonus_phrases)}*")

        final_text = comp_cfg.separator.join(parts) if parts else "Сегодня без особых отклонений."
        final_tone = tones[0] if tones else "neutral"

        logger.info("narrative_composed", tone=final_tone, length=len(final_text))
        
        return {"text": final_text, "tone": final_tone}

    def _select_variant(self, variants: List[MessageVariant], history_texts: List[str]) -> MessageVariant:
        """Selects variant securely preventing direct string duplicate in history window."""
        available = [v for v in variants if v.text not in history_texts]
        if not available:
            available = variants 
        
        weighted_variants = []
        for v in available:
            weight = v.weight if v.weight is not None else 1.0
            weighted_variants.extend([v] * max(1, int(weight * 10)))
            
        return random.choice(weighted_variants) if weighted_variants else variants[0]
