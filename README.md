# interface_kp

部分借鉴了一位大神的想法（http://bbs.canet.com.cn/thread-568341-1-1.html） ，借用了他的Excel模板，代码部分为原创。

目的是将Excel文件转化为开票软件可导入的XML文件


## 使用

1.根据Excel模板文件格式，创建需要开发票的信息，例如对方税号、公司名称、产品名称、数量、单价、税率等

2.运行python命令行

```python
import main

main.main('<excel文件名称带路径和后缀>','<xml文件名称带路径和后缀>')

```

3.在开票软件中选择开票，在上方找到导入，选择刚转换的XML文件导入，检查所导入的信息


## 已知Bug

当对方税号为纯数字时，转换后的XML文件中税号格式有误，无法被税务开票系统识别。


