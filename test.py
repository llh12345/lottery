from lxml import html

with open('500.html', 'r', encoding='utf-8') as file:
    # 使用lxml解析HTML文件
    tree = html.fromstring(file.read())

    # 找到所有的<a>标签并打印它们的文本内容
    for link in tree.xpath('//a'):
        print(link.text_content())