from telethon import TelegramClient, sync  # need to keep sync in otherwise get await errors
import os
import argparse
import pandas as pd
from datetime import datetime

# Обязательно нужно ввести данные api telegram!
phonenumber =
api_id =
api_hash = 

out_dir = '.'

client = TelegramClient(phonenumber, api_id, api_hash)
client.connect()
if not client.is_user_authorized():
    print('Need ')
    client.send_code_request(phonenumber)
    client.sign_in(phonenumber, input('Enter the code: '))


def xstr(s):
    if s is None:
        return ''
    return str(s)


def channel2csv(channel_username, from_date=None, to_date=None):
    if ":::?:::" in channel_username:
        channel_IDusername, channel_username = channel_username.split(":::?:::")
        channel_IDusername = int(channel_IDusername)
    else:
        channel_IDusername = channel_username

    # Тут запросы с выборкой по дате. Костыли потому-что в самой апи не реализовано between выборка между датами
    if not from_date and to_date:
        chats = client.get_messages(channel_IDusername, offset_date=to_date, limit=None)
    elif from_date and to_date:
        pre_first_msg = client.get_messages(channel_IDusername, offset_date=from_date, limit=1)[0]
        first_msg = client.get_messages(channel_IDusername, min_id=pre_first_msg.id, limit=1, reverse=True)[0]
        last_msg = client.get_messages(channel_IDusername, offset_date=to_date, limit=1)[0]
        chats = client.get_messages(channel_IDusername, min_id=first_msg.id, max_id=last_msg.id) + [first_msg,
                                                                                                          last_msg]
    elif from_date and not to_date:
        pre_first_msg = client.get_messages(channel_IDusername, offset_date=from_date, limit=1)[0]
        first_msg = client.get_messages(channel_IDusername, min_id=pre_first_msg.id, limit=1, reverse=True)[0]
        last_msg = client.get_messages(channel_IDusername, limit=1)[0]
        chats = client.get_messages(channel_IDusername, min_id=first_msg.id, max_id=last_msg.id) + [first_msg,
                                                                                                        last_msg]
    elif not from_date and not to_date:
        chats = client.get_messages(channel_IDusername, limit=None)

    sender_username = []
    sendername = []
    message_id = []
    message = []
    sender = []
    reply_to = []
    time_msg = []
    channel_id = []
    channel_name = []

    if len(chats):
        print(F"{str(len(chats))} messages found!")
        for chat in chats:
            message_id.append(chat.id)
            message.append(str(chat.message))
            sender.append(chat.from_id)
            reply_to.append(chat.reply_to_msg_id)
            time_msg.append(chat.date)
            try:
                sender_username.append(str(chat.sender.username))
                sender_name = F"{xstr(chat.sender.first_name)} {xstr(chat.sender.last_name)}" #Пустая строка если нет имени
                sendername.append(sender_name)
            except Exception as e:
                pass
            channel_id.append(str(chat.to_id.channel_id))
            channel_name.append(str(chat._chat.title))
        data = {"channel_name": channel_name, "channel_ID": channel_id, 'message_id': message_id, 'message': message,
                'sender_ID': sender, "sender_username": sender_username, "sender_name": sendername,
                'reply_to_msg_id': reply_to, 'time': time_msg}
        df = pd.DataFrame.from_dict(data, orient='index')
        df = df.transpose()
        path_csv = os.path.join(out_dir, F"telegram_{channel_username.split('/')[-1]}.csv")
        print(f"Created CSV. Path:{path_csv}")
        try:
            df.to_csv(path_csv, index=False)
        except PermissionError as er:
            print(er)


def scrape_channel(channels, fromdate, todate):
    for channel in channels:
        channel = str.strip(channel)
        try:
            channel2csv(channel, fromdate, todate)
        except:
            print(f"Messages not found in the channel {channel} or wrong link to the channel")


def get_channel_list_from_file(path):
    try:
        with open(path, 'r') as f:
            channel_list = f.readlines()
    except FileExistsError as err:
        print(err)
    return channel_list


def _main():
    parser = argparse.ArgumentParser(description='post2table')
    parser.add_argument('path2channels',
                        type=str,
                        help='the path to the channel list')
    parser.add_argument('-o',
                        '--out',
                        type=str,
                        help='output file name or full path. (Default: .telegram_<channel_name>.csv)')
    parser.add_argument('-f',
                        '--fromdate',
                        type=str,
                        help='from date. If is none -  early datetime (Example: "DAY-MONTH-YEAR HOURS:MINUTES)')
    parser.add_argument('-t',
                        '--todate',
                        type=str,
                        help='to date. IF is none - current datetime (Example: "DAY-MONTH-YEAR HOURS:MINUTES)')
    args = parser.parse_args()
    if args.out:
        global out_dir
        out_dir = args.out
    else:
        out_dir = os.getcwd()
    from_date = datetime.strptime(args.fromdate, '%d-%m-%Y %H:%M') if args.fromdate else None
    to_date = datetime.strptime(args.todate, '%d-%m-%Y %H:%M') if args.todate else None
    channels = get_channel_list_from_file(args.path2channels)
    scrape_channel(channels, from_date, to_date)
    client.disconnect()


if __name__ == "__main__":
    _main()
