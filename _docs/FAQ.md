## 常见问题解答

1. 启动 Bot 时报 **ImportError: Unable to find zbar shared library** 错误

   > 
   > **缺少 zbar 库**
   > 
   > CentOS 执行 
   > ```shell
   > yum install zbar-devel
   > ```
   > Ubuntu 执行
   > ```shell
   > sudo apt install libzbar-dev
   > ```

2. 使用需要发送语音的功能时报错 **NameError: name 'warn' is not defined**

   > **系统内未安装 ffmpeg**
   > 
   > 请自行使用搜索引擎查询并安装 ffmpeg
