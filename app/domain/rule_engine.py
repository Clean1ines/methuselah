import random
from typing import List, Dict, Union
from app.core.logger import get_logger
from app.core.config_registry import RulesConfig, Rule, RuleCondition

logger = get_logger(__name__)

class RuleEngine:
    """Runs logical evaluation parsing validated domain objects to maintain integrity."""
    def __init__(self, config: RulesConfig, history_records: List[Dict[str, str]]) -> None:
        self.config = config
        self.history_records = history_records
        self.history_rule_ids = [r['rule_id'] for r in history_records]

    def evaluate(self, context: Dict[str, Union[str, int, float, bool]]) -> List[Rule]:
        """Calculates derivations and triggers rules while emitting traceable logs."""
        enriched_ctx = dict(context)
        
        for metric in self.config.derived_metrics:
            cond_wrapper = RuleCondition(all=metric.all, any=metric.any)
            enriched_ctx[metric.id] = self._check_condition(cond_wrapper, enriched_ctx)

        matched: List[Rule] = []
        filtered: List[Dict[str, str]] = []

        for rule in self.config.rules:
            if not self.config.engine.allow_duplicates:
                if rule.id in self.history_rule_ids:
                    filtered.append({"rule_id": rule.id, "reason": "duplicate_rule_id"})
                    continue
            
            if self._check_condition(rule.conditions, enriched_ctx):
                matched.append(rule)
            else:
                filtered.append({"rule_id": rule.id, "reason": "condition_failed"})

        selected = self._select_diverse(matched)
        
        logger.info(
            "rule_engine_evaluation",
            context=enriched_ctx,
            matched_rules=[r.id for r in matched],
            filtered_rules=filtered,
            selected_rules=[r.id for r in selected]
        )
        
        return selected

    def _check_condition(self, cond: RuleCondition, ctx: Dict[str, Union[str, int, float, bool]]) -> bool:
        """Recursively parses and safely asserts strictly-typed conditions."""
        if cond.all is not None:
            return all(self._check_condition(c, ctx) for c in cond.all)
        if cond.any is not None:
            return any(self._check_condition(c, ctx) for c in cond.any)
        if cond.not_cond is not None:
            return not self._check_condition(cond.not_cond, ctx)
        
        field = cond.field
        op = cond.op
        target = cond.value

        if field is None or op is None:
            return False

        actual = ctx.get(field)
        if actual is None:
            return False

        try:
            if op == "==":
                return actual == target
            elif op == "!=":
                return actual != target
            elif op == ">":
                return float(actual) > float(target) # type: ignore
            elif op == "<":
                return float(actual) < float(target) # type: ignore
            elif op == ">=":
                return float(actual) >= float(target) # type: ignore
            elif op == "<=":
                return float(actual) <= float(target) # type: ignore
            return False
        except (ValueError, TypeError):
            return False

    def _select_diverse(self, matched: List[Rule]) -> List[Rule]:
        """Resolves collisions maximizing coverage based on categorization weights."""
        if not matched:
            return []
        
        selected: List[Rule] = []
        counts_by_cat: Dict[str, int] = {}
        max_per_cat = self.config.engine.max_per_category
        total_limit = self.config.engine.max_rules

        sorted_matched = sorted(
            matched, 
            key=lambda x: (x.priority, random.random() * (x.weight or 1.0)), 
            reverse=True
        )

        for rule in sorted_matched:
            cat = rule.category
            if counts_by_cat.get(cat, 0) < max_per_cat:
                selected.append(rule)
                counts_by_cat[cat] = counts_by_cat.get(cat, 0) + 1
            
            if len(selected) >= total_limit:
                break
        
        return selected
