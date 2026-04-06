from typing import cast
from app.domain.models import DailyEntry
from app.infrastructure.repositories import UserRepository, EntryRepository, InsightHistoryRepository
from app.domain.rule_engine import RuleEngine
from app.application.narrative_composer import NarrativeComposer
from app.application.context_builder import ContextBuilder
from app.core.config_registry import config_registry
from app.core.logger import get_logger

logger = get_logger(__name__)

class ProcessDailyEntryUseCase:
    """Primary actor executing bounded domain context mutations and reporting pipeline."""
    async def execute(self, entry: DailyEntry) -> str:
        """Processes cleanly structured domain model through rule ingestion."""
        user = await UserRepository.get_or_create(entry.telegram_id)
        await EntryRepository.save_entry(entry)
        
        if not config_registry.rules_data:
            return "Система настраивается. Попробуй позже."

        mem_limit = config_registry.rules_data.engine.memory_limit
        history_records = await InsightHistoryRepository.get_recent_insights(
            entry.telegram_id, limit=mem_limit
        )
        
        history_dicts = [{"rule_id": str(r['rule_id']), "message_text": str(r['message_text'])} for r in history_records]
        history_texts = [str(r['message_text']) for r in history_records]

        context = ContextBuilder.build(user, entry)
        logger.info("processing_daily_entry", user_id=user.telegram_id, context=context)
        
        engine = RuleEngine(config_registry.rules_data, history_dicts)
        
        eval_context = {str(k): v for k, v in context.items() if isinstance(v, (str, int, float, bool))}
        selected_rules = engine.evaluate(eval_context)
        
        streak_msg = self._get_streak_message(user.streak_days)
        
        composer = NarrativeComposer()
        result = composer.compose(selected_rules, streak_msg, history_texts)
        
        for rule in selected_rules:
            await InsightHistoryRepository.save_insight(
                telegram_id=entry.telegram_id,
                rule_id=rule.id,
                text=result["text"],
                tone=result["tone"]
            )

        return result["text"]

    def _get_streak_message(self, streak: int) -> str:
        """Retrieves targeted streak message natively matched securely."""
        if not config_registry.rules_data:
            return ""
        streak_rules = config_registry.rules_data.streak_rules
        for s in streak_rules:
            cond = s.conditions
            if cond.field == "streak_days" and cond.op == "==" and cond.value == streak:
                return s.message
        return ""
