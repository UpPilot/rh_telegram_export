import json
from eventmanager import Evt
from .tg_controller import Handler



def initialize(rhapi):
    handler = Handler(rhapi)
    rhapi.events.on(Evt.STARTUP, handler.init_ui)
    rhapi.events.on(Evt.RACE_STAGE, handler.race_start)
    rhapi.events.on(Evt.RACE_LAP_RECORDED, handler.lap_recorded)
    rhapi.events.on(Evt.RACE_STOP, handler.race_end)
    rhapi.events.on(Evt.LAPS_SAVE, handler.auto_race_results)
    rhapi.events.on(Evt.DATABASE_BACKUP,handler.db_backup_fix,priority = 90)
