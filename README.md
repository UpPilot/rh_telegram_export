## RH Telegram Export Plugin
Плагин для экспорта данных в телеграмм во время гонки.
### Функции
С помощью плагина можно автоматически или вручную отправлять следующие данные:
+ Список пилотов 
+ Список групп 
+ Текущая группа
+ Уведомление о старте и финише гонки
+ Результаты последнего вылета 
+ Результат всего мероприятия

### Установка 
Чтобы установить плагин, необходимо скачать архив, разархивировать его и переместить папку rh_telegram_export в 
папку плагинов RH (\src\server\plugins)
Запустить виртуальное окружение и выполнить команду ```pip install requests```
После этого запускаем RotorHazard и на странице Run появится раздел Telegram Export 
### Использование 
#### Создание бота
Перед тем как начать отправлять сообщения надо создать бота в телеграмме.
 Для этого пишем @botfather 
/newbot , следуем инструкциям бота и получаем API Token, с помощью которого плагин будет отправлять сообщения 
Когда мы получили токен, вписываем его в поле API TOKEN 

>**!!! ВНИМАНИЕ !!! ПЕРЕД ЭКСПОРТОМ БАЗЫ ДАННЫХ ОБЯЗАТЕЛЬНО УДАЛИТЕ ТОКЕН ИЗ ПОЛЯ ВВОДА**

После этого добавляем бота в канал или группу, с правами администратора.
Если использовать канал, то в поле вводим @your_channel_name (название вашего канала с @)
Если же использовать группу, то в поле вводим id группы с -100 в начале.

#### Интерфейс

В интерфейсе можно настроить, какую именно информацию отправлять.
![](imgs/interface.png)

#### **Чекбоксы**:

+  **Auto send lap time**

    Отправлять результаты кругов каждого пилота во время гонки или нет 
+ **Auto send race results**

    Отправлять результаты группы сразу после  сохранения кргуов
+ **Hide pilots without band and channel**

    При отправке списка всех пилотов не отображать тех, у кого не назначен канала

+ **Send the race start and finish**


    Отправлять уведомление о начале и конце гонки 

#### **Кнопки:**
 + **Send Results**
    Результат последней гонки по лучшему кругу(можно отправлять автоматически)
  + **Send all pilots**

    Список всех пилотов (Можно выбрать только пилотов у которых назначена канал)

  + **Send all heats**

    Все группы
  
  + **Send current heat** 
    
    Группа текущей гонки

  + **Send event results**

    Результаты мероприятия 