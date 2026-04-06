import yaml
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Union
from app.infrastructure.yaml_loader import ConfigLoader
from app.core.logger import get_logger

logger = get_logger(__name__)

class FlowOption(BaseModel):
    label: str
    value: Union[float, int, str, bool]
    next: str

class FlowStep(BaseModel):
    id: str
    field: str
    question: str
    options: List[FlowOption]

class InputFlowConfig(BaseModel):
    version: str
    flow: List[FlowStep]

class MessageVariant(BaseModel):
    text: str
    tone: Union[str, None] = "neutral"
    weight: Union[int, float, None] = 1.0

class MessageCategory(BaseModel):
    variants: List[MessageVariant]

class CompositionConfig(BaseModel):
    separator: str = "\n\n"
    add_streak_block: bool = True
    add_bonus_probability: float = 0.3

class MessagesConfig(BaseModel):
    composition: CompositionConfig
    messages: Dict[str, MessageCategory]
    bonus_phrases: List[str] = []

class RuleCondition(BaseModel):
    field: Union[str, None] = None
    op: Union[str, None] = None
    value: Union[float, int, str, bool, None] = None
    all: Union[List['RuleCondition'], None] = None
    any: Union[List['RuleCondition'], None] = None
    not_cond: Union['RuleCondition', None] = Field(None, alias='not')

class Rule(BaseModel):
    id: str
    category: str
    priority: int
    conditions: RuleCondition
    message_id: str
    weight: Union[float, None] = 1.0

class DerivedMetric(BaseModel):
    id: str
    all: Union[List[RuleCondition], None] = None
    any: Union[List[RuleCondition], None] = None

class EngineConfig(BaseModel):
    max_rules: int = 2
    selection_strategy: str = "weighted"
    max_per_category: int = 1
    allow_duplicates: bool = False
    memory_limit: int = 10

class StreakRule(BaseModel):
    conditions: RuleCondition
    message: str

class RulesConfig(BaseModel):
    version: str
    engine: EngineConfig
    derived_metrics: List[DerivedMetric] = []
    streak_rules: List[StreakRule] = []
    rules: List[Rule] = []

class ConfigRegistry:
    """Central registry with Pydantic strict-validation and fail-safe reload."""
    _instance = None

    def __new__(cls) -> 'ConfigRegistry':
        if cls._instance is None:
            cls._instance = super(ConfigRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if not getattr(self, "_initialized", False):
            self.rules_data: Union[RulesConfig, None] = None
            self.messages_data: Union[MessagesConfig, None] = None
            self.input_flow_data: Union[InputFlowConfig, None] = None
            self.reload()
            self._initialized = True

    def reload(self) -> None:
        """Reloads configs. Retains last valid state in memory if schema parsing fails."""
        try:
            raw_rules = ConfigLoader.load("config/rules.yaml")
            raw_messages = ConfigLoader.load("config/messages.yaml")
            raw_flow = ConfigLoader.load("config/input_flow.yaml")
            
            validated_rules = RulesConfig(**raw_rules)
            validated_messages = MessagesConfig(**raw_messages)
            validated_flow = InputFlowConfig(**raw_flow)
            
            self.rules_data = validated_rules
            self.messages_data = validated_messages
            self.input_flow_data = validated_flow
            logger.info("configs_reloaded_successfully")
        except ValidationError as e:
            logger.error("config_validation_error", error=str(e))
        except Exception as e:
            logger.error("config_critical_error", error=str(e))

config_registry = ConfigRegistry()
