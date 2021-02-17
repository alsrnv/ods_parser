import json
import os
import csv
import re
import argparse
import sys
from datetime import datetime


def handle_annotated_mention(matchobj):
    return "@{}".format((matchobj.group(0)[2:-1]).split("|")[1])


def handle_mention(matchobj):
    global user
    try:
        print(user[matchobj.group(0)[2:-1]][0])
    except:
        return ' '
    return "@{}".format(user[matchobj.group(0)[2:-1]][0])


def transform_text(text):
    text = text.replace("<!channel>", "@channel")
    text = text.replace("&gt;", ">")
    text = text.replace("&amp;", "&")
    text = re.compile("<@U\w+\|[A-Za-z0-9.-_]+>").sub(handle_annotated_mention, text)
    text = re.compile("<@U\w+>").sub(handle_mention, text)
    return text


def write2csv(path_out, path_dir):
    try:
        f = open(path_out, 'w')
    except PermissionError as er:
        print(er)
    global user
    global include
    content_list = []
    csvwriter = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    if os.path.isdir(path_dir):
        for content in os.listdir(path_dir):
            content_list.append(content)
            with open(os.path.join(path_dir, content)) as data_file:
                data = json.load(data_file)
            for item in data:
                # and 'parent_user_id' not in item
                if item["type"] == "message" and include not in item:
                    if item["text"].find("> has joined the channel") == -1:
                        try:
                            user_cur = user[item["user"]]
                        except:
                            pass
                        ts = datetime.utcfromtimestamp(float(item['ts']))
                        time = ts.strftime("%Y-%m-%d %H:%M:%S")
                        item["text"] = transform_text(item["text"])
                        csvwriter.writerow([time, item['text'], user_cur[0]])
    else:
        print("Invalid dir")
        sys.exit()
    f.close()


def get_real_name_users(path_users):
    user = {}
    if not os.path.isfile(path_users) and not os.path.split(path_users)[1] == ".json":
        print("Invalid json users.file!")
        sys.exit()
    with open(path_users) as user_data:
        userlist = json.load(user_data)
        for userdata in userlist:
            userid = userdata["id"]
            if "real_name" in userdata and userdata["real_name"]:
                realname = userdata["real_name"]
                if not re.match('.*[a-zA-Z].*', realname):
                    realname = userdata["name"]
            else:
                realname = userdata["name"]
            user[userid] = [realname]
    return user


def _main():
    parser = argparse.ArgumentParser(description='post2table')
    parser.add_argument('path2dir',
                        type=str,
                        help='the path to the dir channel')
    parser.add_argument('path2json',
                        type=str,
                        help='the path to the users json file')
    parser.add_argument('-o',
                        '--out',
                        type=str,
                        help='the path to the output file. If is None, the current dir (channel_name.csv)')
    parser.add_argument('-t',
                        '--thread',
                        type=str,
                        help='include posts in the thread. If is none - dont it')
    args = parser.parse_args()
    global include
    include = 'kostyl' if args.thread == 'true' else 'parent_user_id'
    if not args.out:
        out_dir = os.path.join(os.getcwd(), os.path.split(args.path2dir)[-1] + '.csv')
    else:
        out_dir = args.out
    print(args.path2json)
    global user
    user = get_real_name_users(args.path2json)
    write2csv(out_dir, args.path2dir)


if __name__ == "__main__":
    _main()
