from datetime import datetime
import json
import os.path
import random

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from jmcomic import create_option_by_file, JmOption, JmSearchPage, JmAlbumDetail, JmPhotoDetail, JmImageDetail

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.message.components import Node, Plain, Image
from astrbot.core.star.filter.permission import PermissionType
from data.plugins.astrbot_plugins_BAcharacterBirthday.ScheduledTask import add_unified_msg, remove_unified_msg, \
    get_unified_msg

birthday_data_path = "./data/plugins/astrbot_plugins_BAcharacterBirthday/birthday.json"
option_url = './data/plugins/astrbot_plugins_BAcharacterBirthday/option.yml'
download_path = "./data/plugins/astrbot_plugins_BAcharacterBirthday/pic/"

global characters  # 存储所有角色的生日数据

def get_birthday_data():
    global characters
    if not os.path.exists(birthday_data_path):
        return False
    with open(birthday_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    characters = data['charater_birthday']


def find_character_by_name(name):
    for character in characters:
        if name in character['name']:
            return character
    return None


# 获取当天生日的角色
def get_today_birthdate_characters():
    global characters
    # 获取当前日期
    now = datetime.now()
    month = now.month
    day = now.day
    # month = 9
    # day = 29
    current_month_day = f"{month}月{day}日"
    print(current_month_day)
    character_name = []

    # 判断当前日期是否是某个角色的生日
    for character in characters:
        if character['birthday'] == current_month_day:
            print(f"今天是{character['name']}的生日！")
            character_name.append(character['name'])

    return character_name,current_month_day


async def send_daily_birthday_message(context, botid):
    # 获取当天生日的角色
    character_name,current_month_day = get_today_birthdate_characters()
    count = len(character_name)
    if count == 0:
        return # 没有生日就不报

    # 有角色生日
    # 随机获取一个本子并且下载封面
    album_list = []
    tag_list = []
    title_list = []
    for i in range(count):
        mark = True
        while(mark):
            option = create_option_by_file(option_url)

            client = JmOption.copy_option(option).new_jm_client()
            albums: JmSearchPage = client.search_site(search_query=character_name[i], page=1)

            # 从这个album集合里面随机选一个
            selected_album_id, selected_title = random.choice(list(albums))
            if not selected_album_id:
                print("没有找到本子")
                title_list.append("没找到本子")
                album_list.append("没找到本子")
                tag_list.append("没找到本子")
                break

            print(f"随机选择的本子: {selected_album_id} {selected_title}")
            # 下载本子封面
            detail_download_path = os.path.join(download_path, f"{i}.jpg")

            if os.path.exists(detail_download_path):
                os.remove(detail_download_path)

            client = JmOption.copy_option(option).new_jm_client()
            page = client.search_site(search_query=selected_album_id)
            album: JmAlbumDetail = page.single_album

            #检查tag是否含有违禁的tag
            filter_tag = ['NTR', '猎奇', '寝取']
            tag_str = album.tags
            if any(tag in tag_str for tag in filter_tag):
                continue
            # 跳出循环
            mark = False
            # 下载封面
            photo: JmPhotoDetail = album.getindex(0)
            photo01 = client.get_photo_detail(photo.photo_id, False)
            image: JmImageDetail = photo01[0]

            client.download_by_image_detail(image, detail_download_path)

            # 打上防检测
            if os.path.exists(detail_download_path):
                from PIL import Image as ProcessImage

                original_image = ProcessImage.open(detail_download_path)
                # 获取原始图片的宽度和高度
                width, height = original_image.size
                # 创建一张新的空白图片，大小为原图的宽度和五倍高度
                new_image = ProcessImage.new('RGB', (width, height * 5 + 200), color=(255, 255, 255))
                # 将原图粘贴到新图片的下半部分
                new_image.paste(original_image, (0, height * 4))
                # 保存最终结果
                new_image.save(detail_download_path)

            title_list.append(selected_title)
            album_list.append(selected_album_id)
            tag_list.append(tag_str)

    # 发送消息
    umos = get_unified_msg()

    from astrbot.api.event import MessageChain
    message_chain = MessageChain()

    birthday_name_str = ""
    for character in character_name:
        birthday_name_str += character+" "
    birthday_name_str+="\n"
    #构造节点
    time_node = Node(
        uin=botid,
        name="仙人",
        content=[
            Plain(f"今天是{current_month_day},今天过生日的角色有:\n"),
            Plain(birthday_name_str),
            Plain("为了庆祝她们生日，下面随机推荐一本本子：")
        ]
    )
    message_chain.chain.append(time_node)

    for i in range(count):
        node = Node(
            uin=botid,
            name="仙人",
            content=[
                Plain(f"ID: {album_list[i]}\n"),
                Plain(f"标题: {title_list[i]}\n"),
                Plain(f"tag: {tag_list[i]}\n"),
            ]
        )
        message_chain.chain.append(node)

        if album_list[i]=="没找到本子":
            continue

        pic_path = os.path.join(download_path, f"{i}.jpg")
        if os.path.exists(pic_path):
            pic_node = Node(
                uin=botid,
                name="仙人",
                content=[
                    Image.fromFileSystem(pic_path)
                ]
            )
            message_chain.chain.append(pic_node)

    for umo in umos:
        try:
            await context.send_message(umo, message_chain)
        except Exception as e:
            print(f"发送消息失败: {e}")

            #发送纯文字版本的
            from astrbot.api.event import MessageChain
            message_chain_text = MessageChain()

            birthday_name_str = ""
            for character in character_name:
                birthday_name_str += character + " "
            birthday_name_str += "\n"
            # 构造节点
            time_node = Node(
                uin=botid,
                name="仙人",
                content=[
                    Plain(f"今天是{current_month_day},今天过生日的角色有:\n"),
                    Plain(birthday_name_str),
                    Plain("为了庆祝她们生日，下面随机推荐一本本子：")
                ]
            )
            message_chain_text.chain.append(time_node)

            for i in range(count):
                node = Node(
                    uin=botid,
                    name="仙人",
                    content=[
                        Plain(f"ID: {album_list[i]}\n"),
                        Plain(f"标题: {title_list[i]}\n"),
                        Plain(f"tag: {tag_list[i]}\n"),
                    ]
                )
                message_chain_text.chain.append(node)
            try:
                await context.send_message(umo, message_chain_text)
            except Exception as e:
                print(f"发送纯文字消息失败: {e}")


def add_character_to_json(name: str, birthday: str) -> bool:
    """向 birthday.json 添加新角色"""
    try:
        # 读取现有数据
        with open(birthday_data_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # 检查是否已存在相同名称的角色
        for character in data['charater_birthday']:
            if character['name'] == name:
                print(f"角色 {name} 已存在")
                return False

        # 添加新角色
        new_character = {
            "name": name,
            "birthday": birthday
        }
        data['charater_birthday'].append(new_character)

        # 保存回文件
        with open(birthday_data_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print(f"添加角色失败: {e}")
        return False


def del_character_from_json(name):
    try:
        # 读取现有数据
        with open(birthday_data_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # 查找并删除指定名称的角色
        original_length = len(data['charater_birthday'])
        data['charater_birthday'] = [char for char in data['charater_birthday'] if char['name'] != name]

        # 检查是否有角色被删除
        if len(data['charater_birthday']) == original_length:
            print(f"未找到角色 {name}")
            return False  # 没有找到要删除的角色

        # 保存回文件
        with open(birthday_data_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

        print(f"成功删除角色：{name}")
        return True
    except Exception as e:
        print(f"删除角色失败: {e}")
        return False


def get_most_recent_birthday_character() -> str:
    global characters
    if not characters:
        return "暂无角色生日数据"

    now = datetime.now()
    current_year = now.year
    current_date = now.date()
    upcoming_birthdays = []

    for character in characters:
        birthday_str = character['birthday']
        # 解析生日字符串 "M月D日" 或 "MM月DD日"
        import re
        match = re.match(r'(\d+)月(\d+)日', birthday_str)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))

            # 创建今年的生日日期
            try:
                birthday_this_year = datetime(current_year, month, day).date()

                # 如果今年的生日已过，则计算明年的生日
                if birthday_this_year < current_date:
                    birthday_next_year = datetime(current_year + 1, month, day).date()
                    days_until = (birthday_next_year - current_date).days
                    upcoming_birthdays.append({
                        'name': character['name'],
                        'birthday': birthday_next_year,
                        'days_until': days_until
                    })
                else:
                    days_until = (birthday_this_year - current_date).days
                    upcoming_birthdays.append({
                        'name': character['name'],
                        'birthday': birthday_this_year,
                        'days_until': days_until
                    })
            except ValueError:
                # 处理无效日期（如2月30日）
                continue

    if not upcoming_birthdays:
        return "暂无可计算的生日数据"

        # 按照距离天数排序，找出最近的生日
    nearest_birthday = min(upcoming_birthdays, key=lambda x: x['days_until'])

    if nearest_birthday['days_until'] == 0:
        return f"今天是 {nearest_birthday['name']} 的生日！"
    else:
        return f"最近的生日是 {nearest_birthday['name']}，还有 {nearest_birthday['days_until']} 天 ({nearest_birthday['birthday'].strftime('%m月%d日')})"


def find_character_by_name_fuzzy(name):
    """模糊匹配查找角色"""
    global characters
    if not characters:
        return []

    # 查找名称中包含指定字符串的角色
    related_character = [character for character in characters if name in character['name']]
    return related_character

def get_character_birthday_with_name(name):
    global characters
    if not characters:
        return "暂无角色生日数据"

    # 模糊匹配角色
    matched_characters = find_character_by_name_fuzzy(name)
    if not matched_characters:
        return f"未找到包含 '{name}' 的角色"

    from datetime import datetime
    now = datetime.now()
    current_year = now.year
    current_date = now.date()

    # 存储匹配角色的生日信息
    upcoming_birthdays = []

    for character in matched_characters:
        birthday_str = character['birthday']
        # 解析生日字符串 "M月D日" 或 "MM月DD日"
        import re
        match = re.match(r'(\d+)月(\d+)日', birthday_str)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))

            # 创建今年的生日日期
            try:
                birthday_this_year = datetime(current_year, month, day).date()

                # 如果今年的生日已过，则计算明年的生日
                if birthday_this_year < current_date:
                    birthday_next_year = datetime(current_year + 1, month, day).date()
                    days_until = (birthday_next_year - current_date).days
                    upcoming_birthdays.append({
                        'name': character['name'],
                        'birthday': birthday_next_year,
                        'days_until': days_until
                    })
                else:
                    days_until = (birthday_this_year - current_date).days
                    upcoming_birthdays.append({
                        'name': character['name'],
                        'birthday': birthday_this_year,
                        'days_until': days_until
                    })
            except ValueError:
                # 处理无效日期（如2月30日）
                continue

    if not upcoming_birthdays:
        return f"匹配到的角色 '{name}' 暂无可计算的生日数据"

    # 按照距离天数排序，找出最近的生日
    nearest_birthday = min(upcoming_birthdays, key=lambda x: x['days_until'])

    if nearest_birthday['days_until'] == 0:
        return f"今天就是 {nearest_birthday['name']} 的生日！"
    else:
        return f"匹配到的角色中最近的生日是 {nearest_birthday['name']}，还有 {nearest_birthday['days_until']} 天 ({nearest_birthday['birthday'].strftime('%m月%d日')})"

@register("BAcharacterBirthday", "orchidsziyou", "一个简单的 BA角色生日 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        if not os.path.exists("./data/plugins/astrbot_plugins_BAcharacterBirthday/pic/"):
            os.mkdir("./data/plugins/astrbot_plugins_BAcharacterBirthday/pic/")

        get_birthday_data()

        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(
            self.send_daily_birthday_task,
            CronTrigger(hour=10, minute=0),
            # IntervalTrigger(minutes=2),
            id='daily_birthday_send',
            misfire_grace_time=120,  # 允许120秒的延迟容
            coalesce=True,  # 合并错过的任务
            max_instances=1
        )
        self.scheduler.start()
        print("APScheduler 定时任务已启动")

    async def send_daily_birthday_task(self):
        """每日推送任务"""
        try:
            print(f"开始执行每日任务: {datetime.now()}")
            await send_daily_birthday_message(self.context, "123321123")
            print(f"每日任务执行完成: {datetime.now()}")
        except Exception as e:
            print(f"定时任务执行失败: {e}")
            import traceback
            traceback.print_exc()

    @filter.command_group("ba")
    async def ba_command_group(self, event: AstrMessageEvent):
        ...

    @filter.permission_type(PermissionType.ADMIN)
    @ba_command_group.command("addlist")
    async def jm_addlist_command(self, event: AstrMessageEvent):
        """ 这是一个 添加群聊/私聊消息串 指令"""
        umo = event.unified_msg_origin
        print(umo)
        add_unified_msg(umo)
        yield event.plain_result(f"添加成功")

    @filter.permission_type(PermissionType.ADMIN)
    @ba_command_group.command("removelist")
    async def jm_removelist_command(self, event: AstrMessageEvent):
        """ 这是一个 删除群聊/私聊消息串 指令"""
        umo = event.unified_msg_origin
        remove_unified_msg(umo)
        yield event.plain_result(f"删除成功")

    @filter.permission_type(PermissionType.ADMIN)
    @ba_command_group.command("addchara")
    async def jm_addchara_command(self, event: AstrMessageEvent,name:str,date:str):
        """ 这是一个 添加角色生日 指令"""
        import re
        if not re.match(r'\d+月\d+日', date):
            yield event.plain_result("日期格式错误！正确格式：MM月DD日")
            return
        success = add_character_to_json(name, date)
        if success:
            yield event.plain_result(f"添加角色成功")
        else:
            yield event.plain_result(f"添加角色失败")

        get_birthday_data() # 更新数据

    @filter.permission_type(PermissionType.ADMIN)
    @ba_command_group.command("delchara")
    async def jm_delchara_command(self, event: AstrMessageEvent,name:str):
        """ 这是一个 删除角色生日 指令"""
        success = del_character_from_json(name)
        if success:
            yield event.plain_result(f"删除角色成功")
        else:
            yield event.plain_result(f"删除角色失败")

        get_birthday_data()  # 更新数据

    @ba_command_group.command("recent")
    async def jm_recent_command(self, event: AstrMessageEvent):
        """ 这是一个 最近生日 指令"""
        result = get_most_recent_birthday_character()
        yield event.plain_result(result)

    @ba_command_group.command("search")
    async def jm_recent_fuzzy_command(self, event: AstrMessageEvent, name: str):
        """模糊匹配最近生日指令"""
        result = get_character_birthday_with_name(name)
        yield event.plain_result(result)

