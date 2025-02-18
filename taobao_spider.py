
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from time import sleep
from pyquery import PyQuery as pq

class taobao_good:
    def __init__(self, title, price, url):
        self.title = title
        self.price = price
        self.url = url
        self.detail_images = []

class TaobaoSpider:
    def __init__(self, chromedriver_path, chrome_path):
       
        url = 'https://login.taobao.com/member/login.jhtml'
        self.url = url

        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2}) # 不加载图片,加快访问速度
        options.add_experimental_option('excludeSwitches', ['enable-automation']) # 此步骤很重要，设置为开发者模式，防止被各大网站识别出来使用了Selenium
        options.binary_location = chrome_path

        service = Service(executable_path=chromedriver_path, options=options)

        self.browser = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.browser, 5) #超时时长为10s

    def start(self):
        self.browser.get("https://s.taobao.com/search?fromTmallRedirect=true&page=1&q=电脑&spm=&tab=mall")
        main_tab = self.browser.current_window_handle #获取当前窗口句柄

        # Open a new tab using keyboard shortcuts
        # self.browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + 't')  # For Windows/Linux
        self.browser.execute_script('window.open("")')
        # Switch to the new tab
        self.browser.switch_to.window(self.browser.window_handles[-1])  # Switch to the last opened tab
        good_tab = self.browser.current_window_handle

        self.browser.switch_to.window(main_tab)

        page_total = self.search_toal_page()
        print("总共页数" + str(page_total))

        # 遍历所有页数
        for page in range(2,int(page_total)):

            # 等待该页面全部商品数据加载完毕
            good_total = self.wait.until(EC.presence_of_element_located((By.ID, 'content_items_wrapper')))

            # 等待该页面input输入框加载完毕
            current_page = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.next-pagination-list>button.next-current')))
           
            # 获取当前页
            now_page = current_page.find_element(By.TAG_NAME, 'span').text
            print("当前页数" + now_page + ",总共页数" + page_total)

            # 获取本页面源代码
            html = self.browser.page_source

            # pq模块解析网页源代码
            doc = pq(html)

            # 存储天猫商品数据
            good_items = doc('.search-content-col').items()

            # 遍历该页的所有商品
            current_page_good_count = 0
            current_page_good_list = []
            for item in good_items:
                good_title = item.find('[class*="title"]').text()
                # good_status = item.find('.productStatus').text().replace(" ","").replace("笔","").replace('\n',"").replace('\r',"")
                good_price = item.find('[class*="priceWrapper"]>div:nth-of-type(1)').text()
                good_url = "https:"+item.find('a').attr('href').strip()
                good = taobao_good(good_title, good_price, good_url)
                current_page_good_list.append(good)
                current_page_good_count+=1
                print(str(current_page_good_count)+ "     "+ good.title + "   " + good.price + "   " + good.url + '\n')

            self.browser.switch_to.window(good_tab)
            for good in current_page_good_list:
                self.browser.get(good.url)
                detail_page = None
                try:
                    # 等待详情页加载完毕
                    detail_page = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#content>div')))
                except Exception as e:
                    print ('get detail page failed: ', e)
                    # 等待滑动验证码出现,超时时间为5秒，每0.5秒检查一次
                    # 大部分情况不会出现滑动验证码，所以如果有需要可以注释掉下面的代码
                    # sleep(5)
                    WebDriverWait(self.browser, 1, 0.5).until(EC.presence_of_element_located((By.XPATH, '//div[@class="J_MIDDLEWARE_FRAME_WIDGET"]/iframe'))) #等待滑动拖动控件出现
                    try:
                        sub_frame = self.browser.find_element(By.XPATH, '//div[@class="J_MIDDLEWARE_FRAME_WIDGET"]/iframe')
                        if(sub_frame is not None):
                            self.swipe(sub_frame)
                    except Exception as e:
                        print ('get verify button failed: ', e)
                try:
                    if(detail_page is not None):
                        detail_page = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#content>div')))
                    if(detail_page is not None):
                        # 获取详情页图片
                        detail_images = self.get_detail_images(detail_page)
                        good.detail_images = detail_images
                        good.detail_images = detail_images
                except Exception as e:
                    print ('get detail page failed: ', e)
                sleep(2)

            # 切换到主页
            self.browser.switch_to.window(main_tab)

            # 精髓之处，大部分人被检测为机器人就是因为进一步模拟人工操作
            # 模拟人工向下浏览商品，即进行模拟下滑操作，防止被识别出是机器人
            self.swipe_down(2)

            # 翻页，下一页
            self.next_page(page)

            # 等待滑动验证码出现,超时时间为5秒，每0.5秒检查一次
            # 大部分情况不会出现滑动验证码，所以如果有需要可以注释掉下面的代码
            sleep(5)
            try:
                sub_frame = self.browser.find_element(By.XPATH, '//div[@class="J_MIDDLEWARE_FRAME_WIDGET"]/iframe')
                if(sub_frame is not None):
                    self.swipe(sub_frame)
            except Exception as e:
                print ('get verify button failed: ', e)



    def waitlogin(self):
        self.browser.implicitly_wait(30)
        # self.swipe(self.browser.find_element(By.XPATH, '//div[@id="baxia-password"]/div/iframe'))
        self.browser.find_element(By.CLASS_NAME,"search-suggest-combobox-imageSearch-input")

    def loginManually(self):
        self.browser.get(self.url)
        # self.swipe()
        # 获取天猫商品总共的页数
    def search_toal_page(self):

        sub_frame = None
        try:
            sub_frame = self.browser.find_element(By.XPATH, '//div[@class="J_MIDDLEWARE_FRAME_WIDGET"]/iframe')
            if(sub_frame is not None):
                self.swipe(sub_frame)
        except Exception as e:
            print('sub frame not found: ', e)
        number_total = None
        try:

            # 等待本页面全部天猫商品数据加载完毕
            good_total = self.wait.until(EC.presence_of_element_located((By.ID, 'content_items_wrapper')))
            #获取天猫商品总共页数
            number_total = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.next-pagination-list>button:nth-last-of-type(1)')))
        except Exception as e:
            print('get good total failed: ', e)
            # self.wait.until(EC.presence_of_element_located((By.ID, "nc_1_n1z"))) #等待滑动拖动控件出现
            try:
                sub_frame = self.browser.find_element(By.XPATH, '//div[@class="J_MIDDLEWARE_FRAME_WIDGET"]/iframe')
                if(sub_frame is not None):
                    self.swipe(sub_frame)
            except Exception as e:
                print('sub frame not found: ', e)

        except Exception as e:
            print ('get button failed: ', e)
        page_total = 0 if number_total is None else number_total.text.replace("共","").replace("页，到第页 确定","").replace("，","")

        return page_total

    # 模拟向下滑动浏览
    def swipe_down(self,second):
        for i in range(int(second/0.1)):
            js = "var q=document.documentElement.scrollTop=" + str(300+200*i)
            self.browser.execute_script(js)
            sleep(0.1)
        js = "var q=document.documentElement.scrollTop=100000"
        self.browser.execute_script(js)
        sleep(0.2)

        # 翻页操作
    def next_page(self, page_number):
        # 等待该页面input输入框加载完毕
        input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.next-input>input')))

        # 等待该页面的确定按钮加载完毕
        submit = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.next-pagination-jump-go')))

        # 清除里面的数字
        input.clear()

        # 重新输入数字
        input.send_keys(page_number)

        # 强制延迟1秒，防止被识别成机器人
        sleep(1)

        # 点击确定按钮
        submit.click()


    def get_detail_images(self, detail_page):
        # 获取详情页图片
        detail_images = []
        detail_image_items = detail_page.find_elements(By.TAG_NAME, 'img')
        for item in detail_image_items:
            detail_images.append(item.get_attribute('src'))
        return detail_images

    def swipe(self, frame):
        self.browser.switch_to.frame(frame)
        try:
            swipe_button = self.browser.find_element(By.ID, 'nc_1_n1z') #获取滑动拖动控件
            sleep(1)
            #模拟拽托
            action = ActionChains(self.browser) # 实例化一个action对象
            action.click_and_hold(swipe_button).perform() # perform()用来执行ActionChains中存储的行为
            # action.reset_actions()
            parent_width = swipe_button.find_element(By.XPATH, '..').size.get('width')
            current_width = swipe_button.size.get('width')
            # action.move_by_offset(320, 0).perform() # 移动滑块
            action.move_by_offset(parent_width - current_width, 0).perform() # 移动滑块
            # self.smooth_move_by_offset(self.browser, 320, 0, 1, 100)

        except Exception as e:
            print ('get button failed: ', e)
        self.browser.switch_to.parent_frame()

    def smooth_move_by_offset(self, driver, x_offset, y_offset, duration_seconds, steps=100):
        # Calculate per-step offsets and time
        x_per_step = x_offset / steps
        y_per_step = y_offset / steps
        step_delay = duration_seconds / steps

        # Initialize accumulated offsets for precise movement
        x_accumulated = 0.0
        y_accumulated = 0.0

        actions = ActionChains(driver)
        for _ in range(steps):
            x_accumulated += x_per_step
            y_accumulated += y_per_step

            # Convert accumulated floats to integer steps
            dx = int(round(x_accumulated))
            dy = int(round(y_accumulated))

            if dx != 0 or dy != 0:
                actions.move_by_offset(dx, dy)
                # actions.pause(step_delay)
                # Reset accumulated values after moving
                x_accumulated -= dx
                y_accumulated -= dy

        # Add any remaining movement due to rounding errors
        final_dx = int(round(x_accumulated))
        final_dy = int(round(y_accumulated))
        if final_dx != 0 or final_dy != 0:
            actions.move_by_offset(final_dx, final_dy)
        actions.perform()

if __name__ == '__main__':
    chromedriver_path = "\\chromedriver.exe" #改成你的chromedriver的完整路径地址
    binary_location = "\\chrome.exe"
    
    spider = TaobaoSpider(chromedriver_path, binary_location)
    spider.loginManually()
    spider.waitlogin()
    spider.start()
    pass
