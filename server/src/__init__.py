"""
server/src/ — 后端源代码根目录

🔧 什么是 __init__.py？
   这个文件告诉 Python："这个目录是一个 Python 包（package）"。
   有了它，其他文件才能用 `from src import xxx` 的方式导入这里的代码。
   如果一个目录没有 __init__.py，Python 不会把它当作包（新版 Python 3.3+ 允许省略，但保留它是最佳实践）。

   类比：前端的 index.ts 作为"桶文件"（barrel export），统一导出模块。
         __init__.py 的作用类似，但它是 Python 语言级别的"这是一个包"的声明。
"""
