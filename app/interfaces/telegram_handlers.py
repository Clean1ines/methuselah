from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.core.config_registry import config_registry, FlowOption, FlowStep
from app.application.use_cases import ProcessDailyEntryUseCase
from app.domain.models import DailyEntry
from app.core.logger import get_logger
from typing import Union, List, cast

logger = get_logger(__name__)
router = Router()

def get_flow_step(step_id: str) -> Union[FlowStep, None]:
    if not config_registry.input_flow_data:
        return None
    for s in config_registry.input_flow_data.flow:
        if s.id == step_id:
            return s
    return None

def build_keyboard(options: List[FlowOption], step_id: str) -> types.InlineKeyboardMarkup:
    """Constructs stable deterministic FSM options with compact structural keys."""
    builder = InlineKeyboardBuilder()
    for opt in options:
        val_str = str(opt.value)[:15] 
        builder.button(text=opt.label, callback_data=f"{step_id}:{val_str}")
    builder.adjust(2)
    return builder.as_markup()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    """Entry point clearing memory securely."""
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text="Начать запись", callback_data="start_flow")
    await message.answer("Я Мафусаил. Твои данные — это всё, что останется. Начнем?", reply_markup=kb.as_markup())

@router.callback_query(F.data == "start_flow")
async def start_flow(callback: types.CallbackQuery, state: FSMContext) -> None:
    first_step = get_flow_step("step_0")
    if not first_step:
        await callback.answer("Ошибка: конфиг не загружен.")
        return
    
    await state.update_data(current_step_id="step_0", answers={})
    msg = callback.message
    if isinstance(msg, types.Message):
        await msg.edit_text(
            first_step.question, 
            reply_markup=build_keyboard(first_step.options, "step_0")
        )

@router.callback_query(F.data.contains(":"))
async def process_step(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Processes sequential FSM execution deterministically mapping answers explicitly."""
    data = await state.get_data()
    curr_id = str(data.get("current_step_id", ""))
    answers = cast(dict, data.get("answers", {}))
    
    curr_step = get_flow_step(curr_id)
    if not curr_step:
        await callback.answer("Ошибка состояния. Начни заново /start")
        return

    if not callback.data:
        return

    parts = callback.data.split(":")
    if len(parts) != 2 or parts[0] != curr_id:
        await callback.answer("Неверный шаг. Начни заново /start")
        return

    raw_val = parts[1]
    selected_opt = next((o for o in curr_step.options if str(o.value)[:15] == raw_val), None)
    
    if not selected_opt:
        await callback.answer("Неверная опция.")
        return

    answers[curr_step.field] = selected_opt.value
    next_id = selected_opt.next
    
    msg = callback.message
    if not isinstance(msg, types.Message):
        return

    if next_id == "finalize":
        await msg.edit_text("⌛ *Считываю биополе...*", parse_mode="Markdown")
        
        try:
            entry = DailyEntry(
                telegram_id=callback.from_user.id,
                sleep=float(answers.get("sleep", 0.0)),
                energy=int(answers.get("energy", 0)),
                mood=int(answers.get("mood", 0)),
                activity=str(answers.get("activity", "none")),
                food=str(answers.get("food", "normal")),
                screen=float(answers.get("screen", 0.0)),
                alcohol=bool(answers.get("alcohol", False))
            )
            
            use_case = ProcessDailyEntryUseCase()
            final_text = await use_case.execute(entry)
            await msg.edit_text(final_text, parse_mode="Markdown")
        except Exception as e:
            logger.error("error_finalizing_flow", error=str(e))
            await msg.edit_text("Произошла ошибка при анализе.")
        finally:
            await state.clear()
    else:
        next_step = get_flow_step(next_id)
        if next_step:
            await state.update_data(current_step_id=next_id, answers=answers)
            await msg.edit_text(
                next_step.question, 
                reply_markup=build_keyboard(next_step.options, next_id)
            )
