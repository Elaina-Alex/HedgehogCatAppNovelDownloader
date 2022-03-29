import sys
from bookshelf import *
import HbookerAPI
import re


def refresh_bookshelf_list():
    response = HbookerAPI.BookShelf.get_shelf_list()
    if response.get('code') == '100000':
        Vars.cfg.data['shelf_list'] = response['data']['shelf_list']
        Vars.cfg.save()
        BookShelfList.clear()
        for shelf in Vars.cfg.data['shelf_list']:
            BookShelfList.append(BookShelf(shelf))
    for shelf in BookShelfList:
        shelf.show_info()


def shell_login(inputs):
    if len(inputs) >= 3:
        Vars.cfg.data['account_info'] = {'login_name': inputs[1], 'passwd': inputs[2]}
        response = HbookerAPI.SignUp.login(Vars.cfg.data.get('account_info'))
        if response.get('code') == '100000':
            Vars.cfg.data['common_params'] = {
                'login_token': response['data']['login_token'],
                'account': response['data']['reader_info']['account']
            }
            HbookerAPI.set_common_params(Vars.cfg.data['common_params'])
            Vars.cfg.save()
            print('登录成功, 当前用户昵称为:', HbookerAPI.SignUp.user_account())
        else:
            print(response.get('tip'))
    else:
        print("当前用户昵称为:", HbookerAPI.SignUp.user_account())


def shell_bookshelf(inputs):
    refresh_bookshelf_list()
    if len(inputs) >= 2:
        Vars.current_bookshelf = get_bookshelf_by_index(inputs[1])
    else:
        Vars.current_bookshelf = get_bookshelf_by_index('1')
    if Vars.current_bookshelf is None:
        print('请输入正确的参数')
    else:
        print('已经选择书架: "' + Vars.current_bookshelf.shelf_name + '"')
        Vars.current_bookshelf.get_book_list()
        Vars.current_bookshelf.show_book_list()
        for book in Vars.current_bookshelf.BookList:
            print('开始下载书籍《' + book.book_name + '》')
            book.get_division_list()
            book.get_chapter_catalog()
            if len(book.chapter_list) != 0:
                Vars.out_text_file = os.path.join(os.getcwd(), 'downloads', book.book_name + '.txt')
                Vars.config_text = os.path.join(os.getcwd(), 'Hbooker', book.book_name)
                book.download_chapter()
            if Vars.cfg.data['downloaded_book_id_list'].count(book.book_id) == 0:
                Vars.cfg.data['downloaded_book_id_list'].append(book.book_id)
                Vars.cfg.save()
        print('书架下载已完成')


def shell_download_book(inputs):
    if len(inputs) >= 2:
        Vars.current_book = HbookerAPI.Book.get_info_by_id(inputs[1]).get('data')
        if Vars.current_book is not None:
            Vars.current_book = Book(book_info=Vars.current_book.get('book_info'))
            print('开始下载书籍《' + Vars.current_book.book_name + '》')
            Vars.current_book.get_division_list()
            Vars.current_book.get_chapter_catalog()
            if len(Vars.current_book.chapter_list) != 0:
                Vars.out_text_file = os.path.join(os.getcwd(), 'downloads', Vars.current_book.book_name + '.txt')
                Vars.config_text = os.path.join(os.getcwd(), 'Hbooker', Vars.current_book.book_name)
                Vars.current_book.download_chapter()
            else:
                print(Vars.current_book.book_name, "没有需要下载的章节！")
            if Vars.cfg.data['downloaded_book_id_list'].count(Vars.current_book.book_id) == 0:
                Vars.cfg.data['downloaded_book_id_list'].append(Vars.current_book.book_id)
                Vars.cfg.save()
        else:
            print('获取书籍信息失败, book_id:', inputs[1])
    else:
        print('未输入book_id:')


def shell_update():
    if Vars.cfg.data.get('downloaded_book_id_list') is None or \
            len(Vars.cfg.data.get('downloaded_book_id_list')) == 0:
        print('暂无已下载书籍')
        return
    for book_id in Vars.cfg.data['downloaded_book_id_list']:
        Vars.current_book = HbookerAPI.Book.get_info_by_id(book_id).get('data')
        if Vars.current_book is not None:
            Vars.current_book = Book(None, Vars.current_book['book_info'])
            Vars.current_book.get_division_list()
            Vars.current_book.get_chapter_catalog()
            if len(Vars.current_book.chapter_list) != 0:
                Vars.out_text_file = os.path.join(os.getcwd(), 'downloads', Vars.current_book.book_name + '.txt')
                Vars.config_text = os.path.join(os.getcwd(), 'Hbooker', Vars.current_book.book_name)
                Vars.current_book.download_chapter()
        else:
            print('[提示]获取书籍信息失败, book_id:', book_id)
    print('[提示]书籍更新已完成')


def update_config():
    Vars.cfg.load()
    if Vars.cfg.data.get('common_params') is None:
        Vars.cfg.data['common_params'] = {'login_token': "", 'account': ""}
    if Vars.cfg.data.get('downloaded_book_id_list') is None:
        Vars.cfg.data['downloaded_book_id_list'] = []
    if Vars.cfg.data.get('copy_start') is None:
        Vars.cfg.data['copy_start'] = False
    Vars.cfg.save()
    HbookerAPI.set_common_params(Vars.cfg.data.get('common_params'))


def tests_account_login():
    if HbookerAPI.SignUp.user_account() is not None:
        print("当前登入账号:", HbookerAPI.SignUp.user_account())
    else:
        if Vars.cfg.data.get('account_info') is not None:
            print("检测到本地配置文件，尝试自动登入...")
            response = HbookerAPI.SignUp.login(Vars.cfg.data['account_info'])
            if response.get('code') == '100000':
                Vars.cfg.data['common_params'] = {
                    'login_token': response['data']['login_token'],
                    'account': response['data']['reader_info']['account']
                }
                HbookerAPI.set_common_params(Vars.cfg.data['common_params'])
                Vars.cfg.save()
                print("账号:", HbookerAPI.SignUp.user_account(), "自动登入成功！")
            else:
                print("登入失败:", response.get('tip'))
        else:
            print("检测到本地配置文件账号信息为空，请手动登入！")


def shell(inputs):
    if inputs[0] == 'q' or inputs[0] == 'quit':
        exit()
    elif inputs[0] == 'l' or inputs[0] == 'login':
        shell_login(inputs)
    elif inputs[0].startswith('books'):
        shell_bookshelf(inputs)
    elif inputs[0] == 'd' or inputs[0] == 'download':
        shell_download_book(inputs)
    elif inputs[0] == 'bs' or inputs[0] == 'bookshelf':
        shell_bookshelf(inputs)
    elif inputs[0] == 'up' or inputs[0] == 'updata':
        shell_update()


if __name__ == '__main__':
    update_config()
    tests_account_login()
    if len(sys.argv) >= 2:
        shell(sys.argv[1:])
    else:
        for info in Vars.help_info:
            print('[帮助]', info)
        inputs_list = re.split('\\s+', get('>').strip())
        while True:
            shell(inputs_list)
            inputs_list = re.split('\\s+', get('>').strip())
