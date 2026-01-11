# BAcharacterBirthday

astrbot_plugins_BAcharacterBirthday 插件

可以根据当前日期，自动从已准备好的角色生日数据当中，获取当前日期的生日角色，并返回随机寻找一本该角色的本子返回给指定的用户（私聊或者群聊）。  

## 依赖：
本插件仅测试过使用napcat运行，其他环境未测试，建议使用了napcat的用户安装使用。  
该插件依赖以下模块：  
```
jmcomic
```
若未安装，请自行pip安装
```pycon
pip install jmcomic
```

## 配套插件：  
与本插件配套的是本人另外写的一个JM的插件：  
[astrbot_plugins_JMPlugins](https://github.com/orchidsziyou/astrbot_plugins_JMPlugins)  
建议搭配使用。  

## 使用方法
请根据自己的需求和代理配置，自己配置option.yml当中的对应参数。  

配置完成后，在所需要发送信息的群聊或者私聊当中发送以下指令：  
```pycon
/ba addlist
```
之后，就会把对应发送信息频道的唯一对应标识符umos保存起来，等到后续需要发送消息的之后使用。  

注意：如果当天没有角色生日，则不会发送消息。  

另外，还有以下指令：   
1./ba addchara name<角色名称> date<x月x日>    : 添加角色生日  
2./ba delchara name<角色名称>   : 删除角色生日  
3./ba recent   : 获取距离当前日期最近的的生日角色    

