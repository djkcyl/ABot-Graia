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
