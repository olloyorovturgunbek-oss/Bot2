from aiogram.fsm.state import State, StatesGroup

class ForceTextState(StatesGroup):
    waiting_text = State()

class ForceTextTimeState(StatesGroup):
    waiting_seconds = State()
