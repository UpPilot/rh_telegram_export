import requests
import json
import time
from RHUI import UIField, UIFieldType, UIFieldSelectOption
from collections import defaultdict

DEFAULT_BATTERY_THRESHOLD = 12.0

class Handler:
    def __init__(self,rhapi):
        self.rhapi = rhapi
        self.results_type = "by_fastest_lap"
        self.last_battery_check_time = 0  # For periodic check interval
        self.message_templates = {
            "results":{
                "msg_start": "<b>{heat_name}</b> | Round: {round_number}\n",
                "msg_end":""
            },
            
            "race_start":{
                "msg_start":"<i>{heat_name}</i> | Round:{round_number}\n<b>Race started</b>!🟢",
                "msg_end":""
            },

            "race_end":{
                "msg_start":"<i>{heat_name}</i>\n<b>Race finished!</b>🔴",
                "msg_end":""
            },
            "lap_recorded":{
                "msg_start":"{pilot_name} | 🏁 Lap {lap_number} | ⏱️ {lap_time_formatted}",
                "msg_end":""
            },
            "battery_alert":{
                "msg_start":"⚠️ <b>LOW BATTERY WARNING</b> ⚠️\nVoltage: {voltage}V (threshold: {threshold}V)",
                "msg_end":""
            },
            "battery_status":{
                "msg_start":"🔋 Battery: {voltage}V",
                "msg_end":""
            }

        }

    def init_ui(self, args):
        
        TELEGRAM_EXPORT_PLUGIN = "telegram-export-plugin"
        ui = self.rhapi.ui
        fields = self.rhapi.fields

        ui.register_panel(TELEGRAM_EXPORT_PLUGIN, "Telegram export", "run")
        
        telegram_token = UIField(name = "telegram-filed-token", label = "Telegram API token", field_type = UIFieldType.PASSWORD, desc = "Telegram API token for the bot (get it from @botfather)")  
        fields.register_option(telegram_token, TELEGRAM_EXPORT_PLUGIN)

        channel_id = UIField(name = "telegram-filed-channel-id", label = "Telegram channel @uesrname or id", field_type = UIFieldType.TEXT, desc = "Username @ or channel ID to which the bot (must be an admin) will send data")  
        fields.register_option(channel_id, TELEGRAM_EXPORT_PLUGIN)

        thread_id = UIField(name = "telegram-filed-thread-id", label = "Telegram channel's thread id", field_type = UIFieldType.TEXT, desc = "Thread or topic ID to which the bot (must be an admin) will send data")  
        fields.register_option(thread_id, TELEGRAM_EXPORT_PLUGIN)
        
        results_text = UIField(name = "telegram-filed-results-text", label = "Results message text:", field_type = UIFieldType.TEXT, desc = "Select what text to send using {lp_best} , {lp_avg} , {lps_num} , {lps_consecutives} , {lps_total_time}"\
                               ,value = "{lp_best} | laps: {lps_num} | {lps_total_time}",placeholder = "{lp_best} | laps: {lps_num} | {lps_total_time}")  
        fields.register_option(results_text, TELEGRAM_EXPORT_PLUGIN)

        laps_send = UIField(name = 'telegram-check-lap-send', label = 'Auto send lap time', field_type = UIFieldType.CHECKBOX, desc = "Automatically send data about the time of the passage of the lap")
        fields.register_option(laps_send, TELEGRAM_EXPORT_PLUGIN)

        results_send = UIField(name = 'telegram-check-results-send', label = 'Auto send race results',\
                                field_type = UIFieldType.CHECKBOX, desc = "After the finish, automatically send information about the laps of each pilot")
        fields.register_option(results_send, TELEGRAM_EXPORT_PLUGIN)


        hide_empty_pilots = UIField( name = 'telegram-check-hide-empty-pilots',label = "Send pilots with assigned channels",\
                                     field_type=UIFieldType.CHECKBOX,desc="send a list of only those pilots who have a band and channel assigned")
        fields.register_option(hide_empty_pilots,TELEGRAM_EXPORT_PLUGIN)

        start_finish_send = UIField( name = 'telegram-check-start-finish-send', label = 'Send the race start and finish',\
                                     field_type = UIFieldType.CHECKBOX, desc = "Send notifications about the start and finish of the race")
        fields.register_option(start_finish_send,TELEGRAM_EXPORT_PLUGIN)

        # Battery monitoring settings
        battery_alert_enable = UIField(name='telegram-check-battery-alert', label='Enable battery voltage alert',
                                       field_type=UIFieldType.CHECKBOX, desc="Send alert when battery voltage drops below threshold")
        fields.register_option(battery_alert_enable, TELEGRAM_EXPORT_PLUGIN)

        battery_threshold = UIField(name='telegram-field-battery-threshold', label='Battery voltage threshold (V)',
                                    field_type=UIFieldType.TEXT, desc=f"Minimum battery voltage before sending alert (default: {DEFAULT_BATTERY_THRESHOLD}V)",
                                    value=str(DEFAULT_BATTERY_THRESHOLD), placeholder=str(DEFAULT_BATTERY_THRESHOLD))
        fields.register_option(battery_threshold, TELEGRAM_EXPORT_PLUGIN)

        battery_check_interval = UIField(name='telegram-field-battery-interval', label='Battery check interval (sec)',
                                         field_type=UIFieldType.TEXT, desc="How often to check battery voltage (in seconds)",
                                         value="30", placeholder="30")
        fields.register_option(battery_check_interval, TELEGRAM_EXPORT_PLUGIN)

        value_by_fastest = UIFieldSelectOption(value = "by_fastest_lap", label = "Fastest lap")
        value_by_race_time = UIFieldSelectOption(value = "by_race_time", label = "Race time")
        value_by_consecutives = UIFieldSelectOption(value = "by_consecutives", label = "Consecutives")

        results_type = UIField( name = 'telegram-select-results-type', label = 'Select a method to sort the results',\
                                     field_type = UIFieldType.SELECT, desc = "When sending results, pilots will be displayed according to the selected type",options = [value_by_fastest,value_by_consecutives,value_by_race_time],value = "by_fastest_lap")
        
        fields.register_option(results_type,TELEGRAM_EXPORT_PLUGIN)
        

        
        # Кнопочки
        #ui.register_quickbutton(TELEGRAM_EXPORT_PLUGIN, "telegram-btn-heat", "Send current heat", self.race_heat)
        ui.register_quickbutton(TELEGRAM_EXPORT_PLUGIN, "telegram-btn-all-heats", "Send all heats", self.all_heats)
        ui.register_quickbutton(TELEGRAM_EXPORT_PLUGIN, "telegram-btn-results", "Send results", self.race_results)
        ui.register_quickbutton(TELEGRAM_EXPORT_PLUGIN, "telegram-btn-pilots", "Send all pilots", self.all_pilots)
        ui.register_quickbutton(TELEGRAM_EXPORT_PLUGIN, "telegram-btn-event-results", "Send event results", self.event_results)
        ui.register_quickbutton(TELEGRAM_EXPORT_PLUGIN, "telegram-btn-send-battery", "Send battery status", self.send_battery_status)
       

    #Отправляем 
    def send(self,text):
        token = self.rhapi.db.option("telegram-filed-token")
        channel_id = self.rhapi.db.option("telegram-filed-channel-id")
        thread_id = self.rhapi.db.option("telegram-filed-thread-id")


        if not token or not channel_id: #Токен и какнал обязательны 
            self.rhapi.ui.message_notify("API token and channel id is required")
            return
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": channel_id,
            "text": text,
            "parse_mode": "HTML" 
        }
        if thread_id:
            payload["message_thread_id"] = thread_id
        
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
            heat_name = self.get_heat_name(self.rhapi.db.heat_by_id(self.rhapi.race.heat))
            data = {
                "heat_name":heat_name,
                "round_number":self.rhapi.race.round
            }
            msg_tmp = self.message_templates["race_start"]
            text = msg_tmp["msg_start"].format_map(defaultdict(str,data)) + msg_tmp["msg_end"]
            self.send(text=text)
        return
    
    def race_end(self,args=None):
        
        if self.rhapi.db.option('telegram-check-start-finish-send') == "1":
            heat_name = self.get_heat_name(self.rhapi.db.heat_by_id(self.rhapi.race.heat))
            data = {
                "heat_name": heat_name
            }
            msg_tmp = self.message_templates["race_end"]
            text = msg_tmp["msg_start"].format_map(defaultdict(str,data)) + msg_tmp["msg_end"]
            self.send(text=text)
        return
    
    def lap_recorded(self,args=None): #Пройденный круг 
        if self.rhapi.db.option("telegram-check-lap-send") == "1":
            lap_data = args
            pilot_id = lap_data["pilot_id"]
            pilot_name = self.rhapi.db.pilot_by_id(pilot_id).name
            lap_number = lap_data["lap"].lap_number
            lap_time_formatted = lap_data["lap"].lap_time_formatted
            data = {
                "pilot_name":pilot_name,
                "lap_number":lap_number,
                "lap_time_formatted":lap_time_formatted
            }
            msg_tmp = self.message_templates["lap_recorded"]
            text = msg_tmp["msg_start"].format_map(defaultdict(str,data)) + msg_tmp["msg_end"]
            self.send(text=text)

        return

    
    def auto_race_results(self,args=None):
        if self.rhapi.db.option("telegram-check-results-send") == "1":
            self.race_results()
        return

    def race_results(self,args=None):
        races = self.rhapi.db.races
        if len(races) == 0:
            return
        last_race = self.rhapi.db.races[-1]
        
        result_sort = self.rhapi.db.option("telegram-select-results-type")#self.results_type
        race_data = self.rhapi.db.race_results(last_race)[result_sort] #Парсим данные по result-type (Лучший круг, лучшее время и тп)
        
        round_number = last_race.round_id
        heat_data = self.rhapi.db.heat_by_id(last_race.heat_id)
        heat_name = self.get_heat_name(heat_data)
        
        
        data = {
            "heat_name":heat_name,
            "round_number":round_number
        }
        msg_tmp = self.message_templates["results"]
        text = msg_tmp["msg_start"].format_map(defaultdict(str,data))
        cnt = 1
    
        for race in race_data:
            
            pilot_id = race["pilot_id"]
            pilot_name = self.rhapi.db.pilot_by_id(pilot_id).name
            
            data = {"lp_best":race["fastest_lap"],
                    "lp_avg":race["average_lap"],
                    "lps_num": race["laps"],
                    "lps_consecutives":race["consecutives"],
                    "lps_total_time" : race["total_time_laps"]
                    }
            
            text += f"{cnt}. <b>{pilot_name}</b>\n"
            text += self.rhapi.db.option("telegram-filed-results-text").format_map(defaultdict(str,data)) + "\n"
            
            cnt += 1
        text += msg_tmp["msg_end"]
        self.send(text=text)
        return   


    def db_backup_fix(self,args):
        #Юзеру ОБЯЗАТЕЛЬНО надо удалять свой токен из бд 
        if self.rhapi.db.option("telegram-filed-token") != "":
            self.rhapi.ui.message_alert("!!! ATTENTION BEFORE EXPORTING THE DATABASE, REMOVE THE TELEGRAM TOKEN FROM THE INPUT FIELD !!!")

        self.rhapi.db.option_set(name="telegram-filed-token", value = "")


    def all_pilots(self,args=None):

        text = "<i>All pilots:</i>\n"
        pilots_list = self.rhapi.db.pilots
        hide_empty = self.rhapi.db.option("telegram-check-hide-empty-pilots") == "1"
        cnt = 1
        if hide_empty:

            heats_data = self.get_pilot_freqs()
            pilots_list = {} #pilot : [r1,r2]

            for heat in heats_data:
                for pilot in heats_data[heat]:
                    if pilot.name not in pilots_list:
                        pilots_list[pilot.name] = set()
                    pilots_list[pilot.name].add(heats_data[heat][pilot])

            for pilot in pilots_list:
                bc_text = f"<b>{pilot}</b>  "
                for bc in pilots_list[pilot]:
                    bc_text += f"<i>{bc}</i> "
                text += bc_text+"\n"

        else:
            for pilot in pilots_list:
                text += pilot.name + "\n"
        self.send(text)
        return
    
    def get_pilot_freqs(self): # Возвращаем словарь {"heat_name1" :{"pilot_name":"R2"},"heat_name2" :{"pilot_name2":"R3"}}
        pilot_bc = {}
        heats_list = self.rhapi.db.heats
        freqs = json.loads(self.rhapi.race.frequencyset.frequencies)

        for heat in heats_list: #Проходимся по всемхитам 
            pilot_bc[heat] = {}
            
            slots = self.rhapi.db.slots_by_heat(heat.id) #Получаем все слоты 
            for slot in range(len(slots)): 
                pilot = self.rhapi.db.pilot_by_id(slots[slot].pilot_id)
                  # Name or callsign
                if pilot == None:
                    continue
                pilot_bc[heat][pilot]  = str(freqs["b"][slot])+str(freqs["c"][slot])
 
        return  pilot_bc
    
    def get_heat_name(self,heat):
        heat_name = heat.name
        if heat_name == None or heat_name == "None" or heat_name == "":
            heat_name = heat.auto_name
        return heat_name


    def all_heats(self,args=None):
        #Проходимся по всем хитам и в каждом хите по всем слотам (в каждом слоте берем пилота)
        heats_data = self.get_pilot_freqs()
        for heat in heats_data:
            text = f"<i>{self.get_heat_name(heat)}</i>\n"
            for pilot in heats_data[heat]:
                text += f"{pilot.name} {heats_data[heat][pilot]}\n"
            self.send(text)
            


    def event_results(self,args=None):
        results = self.rhapi.eventresults.results["event_leaderboard"][self.rhapi.db.option("telegram-select-results-type")]
        race_data = results
        text = f""
        cnt = 1
        for race in race_data:

            data = {"lp_best":race["fastest_lap"],
                    "lp_avg":race["average_lap"],
                    "lps_num":race["laps"],
                    "lps_consecutives":race["consecutives"],
                    "lps_total_time" : race["total_time_laps"]
                    }
            pilot_id = race["pilot_id"]
            pilot_name = self.rhapi.db.pilot_by_id(pilot_id).name
            text += f"{cnt}. <b>{pilot_name}</b>\n"
            text += self.rhapi.db.option("telegram-filed-results-text").format_map(defaultdict(str,data)) + "\n\n"
        self.send(text=text)
        return

    def get_battery_voltage(self):
        """Get current battery voltage from sensors. Returns None if not available."""
        try:
            # Search through all available sensors for one with voltage() method
            for sensor in self.rhapi.sensors.sensor_objs:
                if hasattr(sensor, 'voltage') and callable(sensor.voltage):
                    try:
                        val = sensor.voltage()
                        if val is not None:
                            return float(val)
                    except:
                        continue
            return None
        except Exception:
            return None

    def check_battery(self, args=None):
        """Check battery voltage and send alert if below threshold."""
        if self.rhapi.db.option("telegram-check-battery-alert") != "1":
            return

        voltage = self.get_battery_voltage()
        if voltage is None:
            return

        try:
            threshold = float(self.rhapi.db.option("telegram-field-battery-threshold") or DEFAULT_BATTERY_THRESHOLD)
        except ValueError:
            threshold = DEFAULT_BATTERY_THRESHOLD

        if voltage < threshold:
            data = {
                "voltage": f"{voltage:.2f}",
                "threshold": f"{threshold:.1f}"
            }
            msg_tmp = self.message_templates["battery_alert"]
            text = msg_tmp["msg_start"].format_map(defaultdict(str, data)) + msg_tmp["msg_end"]
            self.send(text=text)

    def battery_heartbeat(self, args=None):
        """Called on each heartbeat - checks battery if interval has passed."""
        try:
            interval = float(self.rhapi.db.option("telegram-field-battery-interval") or "30")
        except ValueError:
            interval = 30

        current_time = time.time()
        if current_time - self.last_battery_check_time >= interval:
            self.last_battery_check_time = current_time
            self.check_battery()

    def send_battery_status(self, args=None):
        """Send current battery status to Telegram."""
        voltage = self.get_battery_voltage()
        if voltage is None:
            self.rhapi.ui.message_notify("No voltage sensor available")
            return

        try:
            threshold = float(self.rhapi.db.option("telegram-field-battery-threshold") or DEFAULT_BATTERY_THRESHOLD)
        except ValueError:
            threshold = DEFAULT_BATTERY_THRESHOLD

        data = {
            "voltage": f"{voltage:.2f}",
            "threshold": f"{threshold:.1f}"
        }

        if voltage < threshold:
            msg_tmp = self.message_templates["battery_alert"]
        else:
            msg_tmp = self.message_templates["battery_status"]

        text = msg_tmp["msg_start"].format_map(defaultdict(str, data)) + msg_tmp["msg_end"]
        self.send(text=text)
        self.rhapi.ui.message_notify(f"Battery status sent: {voltage:.2f}V")
