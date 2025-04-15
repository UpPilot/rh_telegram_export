import requests
import json
from RHUI import UIField, UIFieldType

class Handler:
    def __init__(self,rhapi):
        self.rhapi = rhapi
        self.results_type = "by_fastest_lap"  

    def init_ui(self, args):
        
        TELEGRAM_EXPORT_PLUGIN = "telegram-export-plugin"
        ui = self.rhapi.ui
        fields = self.rhapi.fields

        ui.register_panel(TELEGRAM_EXPORT_PLUGIN, "Telegram export", "run")
        
        telegram_token = UIField(name = "telegram-filed-token", label = "Telegram API token", field_type = UIFieldType.PASSWORD, desc = "Telegram API token for the bot (get it from @botfather)")  
        fields.register_option(telegram_token, TELEGRAM_EXPORT_PLUGIN)

        channel_id = UIField(name = "telegram-filed-channel-id", label = "Telegram channel @uesrname or id", field_type = UIFieldType.TEXT, desc = "Username @ or channel ID to which the bot (must be an admin) will send data")  
        fields.register_option(channel_id, TELEGRAM_EXPORT_PLUGIN)
        
        laps_send = UIField(name = 'telegram-check-lap-send', label = 'Auto send lap time', field_type = UIFieldType.CHECKBOX, desc = "Automatically send data about the time of the passage of the lap")
        fields.register_option(laps_send, TELEGRAM_EXPORT_PLUGIN)

        results_send = UIField(name = 'telegram-check-results-send', label = 'Auto send race results',\
                                field_type = UIFieldType.CHECKBOX, desc = "After the finish, automatically send information about the laps of each pilot")
        fields.register_option(results_send, TELEGRAM_EXPORT_PLUGIN)


        hide_empty_pilots = UIField( name = 'telegram-check-hide-empty-pilots',label = "Hide pilots without band and channel",\
                                     field_type=UIFieldType.CHECKBOX,desc="Hide the pilot in list if it does not have a band and channel defined.")
        fields.register_option(hide_empty_pilots,TELEGRAM_EXPORT_PLUGIN)

        start_finish_send = UIField( name = 'telegram-check-start-finish-send', label = 'Send the race start and finish',\
                                     field_type = UIFieldType.CHECKBOX, desc = "Send notifications about the start and finish of the race")
        fields.register_option(start_finish_send, TELEGRAM_EXPORT_PLUGIN)
        
        
        # Кнопочки
        ui.register_quickbutton(TELEGRAM_EXPORT_PLUGIN, "telegram-btn-heat", "Send current heat", self.race_heat)   
        ui.register_quickbutton(TELEGRAM_EXPORT_PLUGIN, "telegram-btn-all-heats", "Send all heats", self.all_heats)              
        ui.register_quickbutton(TELEGRAM_EXPORT_PLUGIN, "telegram-btn-results", "Send results", self.race_results)
        ui.register_quickbutton(TELEGRAM_EXPORT_PLUGIN, "telegram-btn-pilots", "Send all pilots", self.all_pilots)
        ui.register_quickbutton(TELEGRAM_EXPORT_PLUGIN, "telegram-btn-event-results", "Send event results", self.event_results)

       

    #Отправляем 
    def send(self,text):
        token = self.rhapi.db.option("telegram-filed-token")
        channel_id = self.rhapi.db.option("telegram-filed-channel-id")


        if not token or not channel_id: #Токен и какнал обязательны 
            self.rhapi.ui.message_notify("API token and channel id is required")
            return
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": channel_id,
            "text": text,
            "parse_mode": "HTML" 
        }
        
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 400 or response.status_code == 401:
                self.rhapi.ui.message_notify("Invalid token or channel id")
                return
            
        except requests.exceptions.ConnectionError:
            self.rhapi.ui.message_notify("Connection error")
            response = None
        

        return response.json()
    
    #Для каждого ивента своя функция для отправки 

    def race_start(self,args=None):
        
        if self.rhapi.db.option("telegram-check-start-finish-send") == "1":
            heat = self.rhapi.db.heat_by_id(self.rhapi.race.heat)
            self.send(text=f"<i>{heat.name}</i> | Round:{self.rhapi.race.round}\n<b>Race started</b>!🟢")
        return
    
    def race_end(self,args=None):
        
        if self.rhapi.db.option('telegram-check-start-finish-send') == "1":
            heat_name = self.rhapi.db.heat_by_id(self.rhapi.race.heat).name
            self.send(text=f"<i>{heat_name}</i>\n<b>Race finished!</b>🔴")
        return
    
    def lap_recorded(self,args=None): #Пройденный круг 
        if self.rhapi.db.option("telegram-check-lap-send") == "1":
            lap_data = args
            pilot_id = lap_data["pilot_id"]
            pilot_name = self.rhapi.db.pilot_by_id(pilot_id).name
            lap_number = lap_data["lap"].lap_number
            lap_time_formatted = lap_data["lap"].lap_time_formatted
            self.send(text=f"{pilot_name} | 🏁 Lap {lap_number} | ⏱️ {lap_time_formatted}")

        return

    
    def auto_race_results(self,args=None):
        if self.rhapi.db.option("telegram-check-results-send") == "1":
            self.race_results()
        return
    
    def race_results(self,args=None):
        last_race = self.rhapi.db.races[-1]
        result_sort = self.results_type
        print(result_sort)
        race_data = self.rhapi.db.race_results(last_race)[result_sort] #Парсим данные по result-type (Лучший круг, лучшее время и тп)

        round_number = last_race.round_id
        heat_name = self.rhapi.db.heat_by_id(last_race.heat_id).name
        
        text = f"<b>{heat_name}</b> | Round: {round_number}\n"
        cnt = 1
        for i in race_data:
            pilot_id = i["pilot_id"]
            pilot_name = self.rhapi.db.pilot_by_id(pilot_id).name
            laps = i["laps"]
            best_lap = i["fastest_lap"]
            total_time = i["total_time"]
            text += f"{cnt}. <b>{pilot_name}</b>\n<b>{best_lap}</b> | laps <b>{laps}</b> | <b>{total_time}</b>\n"
            cnt += 1
        self.send(text=text)
        return
    
    def db_backup_fix(self,args):
        #Юзеру ОБЯЗАТЕЛЬНО надо удалять свой токен из бд 
        if self.rhapi.db.option("telegram-filed-token") != "":
            self.rhapi.ui.message_alert("!!! ATTENTION BEFORE EXPORTING THE DATABASE, REMOVE THE TELEGRAM TOKEN FROM THE INPUT FIELD !!!")

        self.rhapi.db.option_set(name="telegram-filed-token", value = "")


    def race_heat(self,args=None): #Отправляем текущий список пилотов с каналами и название группы
        heat_id = self.rhapi.race.heat
        heat = self.rhapi.db.heat_by_id(heat_id)
        if heat == None:
            return
        pilots_list = self.rhapi.race.pilots
        
        text = f"<i>Heat name:</i>\n<b>{heat.name}</b>\n<i>Pilots:</i>\n"
        cnt = 1
        for i in pilots_list:
            pilot_id = pilots_list[i]
            if pilot_id != 0:
                pilot = self.rhapi.db.pilot_by_id(pilot_id)
                pilot_name = pilot.name
                pilot_frequencies = pilot.used_frequencies
                band_channel = str(json.loads(pilot_frequencies)[-1]["b"]) + str(json.loads(pilot_frequencies)[-1]["c"])
                text += f"{cnt}. <b>{pilot_name}</b> | <b>{band_channel}</b>\n"
                cnt += 1
        
        self.send(text=text)
        return
    
    def all_pilots(self,args=None):

        text = "<i>All pilots:</i>\n"
        pilots_list = self.rhapi.db.pilots
        hide_empty = self.rhapi.db.option("telegram-check-hide-empty-pilots") == "1"
        cnt = 1
        for pilot in pilots_list:
            pilot_frequencies = pilot.used_frequencies
            if  pilot_frequencies != None and pilot_frequencies != "":
                band_channel = str(json.loads(pilot_frequencies)[-1]["b"]) + str(json.loads(pilot_frequencies)[-1]["c"])
            else:
                band_channel = "-"

            if band_channel == "-":
                if  hide_empty:
                    text += ""
                else:
                    text += f"{cnt}. {pilot.callsign} | <b>{band_channel}</b>\n" 
                    cnt += 1
            else:
                text += f"{cnt}. {pilot.callsign} | <b>{band_channel}</b>\n"
                cnt += 1

        self.send(text)
        return
    
    def all_heats(self,args=None):
        #Проходимся по всем хитам и в каждом хите по всем слотам (в каждом слоте берем пилота)

        heats_list = self.rhapi.db.heats    
        for heat in heats_list:
            text = f"<b>{heat.name}</b>\n<i>Pilots:</i>\n"
            
            slot_list = self.rhapi.db.slots_by_heat(heat.id)

            for _slot in slot_list:
                pilot_id = _slot.pilot_id
                if pilot_id != 0:                
                    pilot = self.rhapi.db.pilot_by_id(pilot_id)
                    pilot_frequencies = pilot.used_frequencies
                    band_channel = str(json.loads(pilot_frequencies)[-1]["b"]) + str(json.loads(pilot_frequencies)[-1]["c"])
                    text += f"<b>{pilot.name}</b> | {band_channel}\n"

            self.send(text=text)
        return


    def event_results(self,args=None):
        results = self.rhapi.eventresults.results["event_leaderboard"][self.results_type]        
        race_data = results
        text = f""
        cnt = 1
        for i in race_data:
            pilot_id = i["pilot_id"]
            pilot_name = self.rhapi.db.pilot_by_id(pilot_id).name
            laps = i["laps"]
            best_lap = i["fastest_lap"]
            total_time = i["total_time"]
            text += f"{cnt}. <b>{pilot_name}</b>\n<b>{best_lap}</b> | laps <b>{laps}</b> | <b>{total_time}</b>\n\n"
            cnt += 1
        self.send(text=text)
        return

