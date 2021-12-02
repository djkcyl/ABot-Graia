## 常见问题解答

1. 启动 Bot 时报 **ImportError: Unable to find zbar shared library** 错误

   > 
   > **缺少 zbar 库**
   > 
   > CentOS 执行 
   > ```shell
   > yum install python-devel
   > yum install zbar-devel
   > ```
   > Ubuntu 执行
   > ```shell
   > sudo apt install libzbar-dev
   > ```

2. 安装依赖报错 **Unable to find installation candidates for pyacrcloud (1.0.2)**

   > **该问题仅会出现在非 Linux 系统，由于该包的非 Linux 版本并未上传于 PyPI ，会出现找不到包的情况，请手动安装**
   > 
   > ```shell
   > poetry remove pyacrcloud
   > poetry add git+https://github.com/acrcloud/acrcloud_sdk_python
   > poetry install
   > ```

3. 使用需要发送语音的功能时报错 **NameError: name 'warn' is not defined**

   > **系统内未安装 ffmpeg**
   > 
   > 请自行使用搜索引擎查询并安装 ffmpeg
