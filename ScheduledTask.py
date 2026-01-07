import json
import os

from jmcomic import JmOption, JmSearchPage, create_option_by_file

# 更新配置文件路径
config_path = "./data/plugins/astrbot_plugins_BAcharacterBirthday/module.json"
# config_path="./module.json"
# option_url = "./option.yml"

def get_unified_msg():
    """
    获取配置文件中的unified_msg列表
    Returns:
        list: unified_msg列表，如果不存在或文件不存在则返回空列表
    """
    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        return []
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 从static_config中获取unified_msg
            static_config = config.get('static_config', {})
            return static_config.get('unified_msg', [])
    except (json.JSONDecodeError, FileNotFoundError):
        # 如果文件损坏或无法读取，返回空列表
        return []

def add_unified_msg(message):
    """
    添加消息到配置文件中的unified_msg列表
    Args:
        message (str): 要添加的消息字符串
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # 如果文件不存在，创建一个默认配置
    if not os.path.exists(config_path):
        config = {
            "static_config": {
                "unified_msg": [message]
            },
            "dynamic_config": {}
        }
    else:
        # 读取现有配置
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            config = {
                "static_config": {
                    "unified_msg": [message]
                },
                "dynamic_config": {}
            }
        
        # 确保static_config和unified_msg存在
        if "static_config" not in config:
            config["static_config"] = {}
        if "unified_msg" not in config["static_config"]:
            config["static_config"]["unified_msg"] = []
        
        # 检查消息是否已存在，如果不存在则添加
        if message not in config["static_config"]["unified_msg"]:
            config["static_config"]["unified_msg"].append(message)
        else:
            # 消息已存在，直接返回
            return
    
    # 写入文件
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def remove_unified_msg(message):
    """
    从配置文件中的unified_msg列表中移除指定消息
    Args:
        message (str): 要移除的消息字符串
    """
    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        return
    
    # 读取现有配置
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return
    
    # 确保static_config和unified_msg存在
    if "static_config" not in config or "unified_msg" not in config["static_config"]:
        return
    
    # 从unified_msg列表中移除消息
    if message in config["static_config"]["unified_msg"]:
        config["static_config"]["unified_msg"].remove(message)
    
    # 写入文件
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

