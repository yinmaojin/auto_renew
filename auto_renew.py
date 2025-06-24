import logging  # 自带：Python 标准库中的日志模块
import re  # 自带：正则表达式模块
import sqlite3  # 自带：Python 内置的轻量级数据库支持
import time  # 自带：时间操作模块
import os  # 自带：操作系统接口模块
from selenium.webdriver.common.action_chains import ActionChains  # 第三方库：需 pip install selenium
from selenium.webdriver.common.by import By  # 第三方库
from selenium.webdriver.support import expected_conditions as EC  # 第三方库
from selenium.webdriver.support.ui import WebDriverWait  # 第三方库
from selenium.webdriver import Edge  # 第三方库
from dotenv import load_dotenv  # 第三方库：需 pip install python-dotenv

# 加载 .env 文件中的环境变量
load_dotenv()
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_now_time():
    """获取当前时间字符串"""
    time_stamp = time.time()
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_stamp))


def _renew_instances(driver, wait):
    """续费实例"""
    try:
        driver.get("https://www.autodl.com/console/instance/list")
        time.sleep(4)
        driver.refresh()

        start_up_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "thirteenSize")))

        for i in range(0, len(start_up_elements), 2):
            driver.refresh()
            start_up = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "thirteenSize")))

            print(f"正在开启第{int(i / 2 + 1)}个服务器")
            actions = ActionChains(driver)
            actions.move_to_element(start_up[i + 1]).perform()
            time.sleep(1)

            start_up_button = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//div[1]/div[1]/ul/ul/div[1]/li/span")))
            start_up_button[int(i / 2)].click()

            confirm_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                        "body > div.el-overlay.is-message-box > div > div.el-message-box__btns > button.el-button.el-button--default.el-button--small.el-button--primary")))
            confirm_button.click()

            time.sleep(5)

            while re.findall(r"开机中", wait.until(EC.presence_of_element_located((By.TAG_NAME, "body"))).text):
                time.sleep(4)
                print(f"等待服务器{int(i / 2 + 1)}启动中...")

            re_text = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body"))).text

            running_text = re.findall(r"运行中", re_text)
            if running_text:
                print(f"第{int(i / 2 + 1)}个服务器开启成功, 正在关闭...")
                close_button = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "thirteenSize")))
                close_button[i].click()

                confirm_button = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                                                    "body > div.el-overlay.is-message-box > div > div.el-message-box__btns > button.el-button.el-button--default.el-button--small.el-button--primary")))
                confirm_button.click()

                time.sleep(5)

                while re.findall(r"关机中", wait.until(EC.presence_of_element_located((By.TAG_NAME, "body"))).text):
                    time.sleep(4)
                    print(f"等待服务器{int(i / 2 + 1)}关闭中...")

        driver.quit()
        return True
    except Exception as e:
        logger.error(f"续费操作失败: {str(e)}")
        return False


class AutoDLRenewer:
    def __init__(self, username, password):
        self.driver = None
        self.wait = None
        self.username = username
        self.password = password
        self.db_path = "time.db"
        self._init_driver()

    def _init_driver(self):
        """初始化浏览器驱动"""
        try:
            self.driver = Edge()
            self.wait = WebDriverWait(self.driver, 60)
        except Exception as e:
            logger.error(f"初始化浏览器失败: {str(e)}")

    def get_running_count(self):
        """获取页面上“运行中”的实例数量"""
        try:
            # 定位到“运行中”对应的 key 元素
            running_key = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//span[@class="key" and contains(text(), "运行中")]'))
            )

            # 使用 XPath 定位其兄弟节点中的 .size.jump 元素
            running_value = running_key.find_element(By.XPATH, './following-sibling::span//span[@class="size jump"]')

            count = int(running_value.text.strip())
            logger.info(f"当前运行中的实例数量: {count}")
            return count
        except Exception as e:
            logger.error(f"获取运行中实例数量失败: {str(e)}")
            return None

    def is_running(self):
        """判断是否有服务器正在运行"""
        # 运行中的服务器的re字段是 运行中
        # 读取运行中标签key的对应的value
        self.driver.get("https://www.autodl.com/console/instance/list")
        return re.findall(r"运行中", self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body"))).text)

    def record_time(self):
        """记录当前时间到数据库"""
        time_str = get_now_time()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 创建表（如果不存在）
                cursor.execute("CREATE TABLE IF NOT EXISTS renewal_time (time TEXT)")
                # 插入数据
                cursor.execute("INSERT INTO renewal_time (time) VALUES (?)", (time_str,))
            logger.info("时间记录成功")
            return time_str  # 直接返回记录的时间，避免再次查询
        except sqlite3.Error as e:
            logger.error(f"数据库操作失败: {str(e)}")
            return None

    def get_time(self):
        """从数据库获取最新记录的时间"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 创建表（如果不存在），防止首次查询时报错
                cursor.execute("CREATE TABLE IF NOT EXISTS renewal_time (time TEXT)")
                cursor.execute("SELECT time FROM renewal_time ORDER BY time DESC LIMIT 1")
                res = cursor.fetchone()
            if res:
                return res[0]
            return None
        except sqlite3.Error as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return None

    def login(self):
        """执行登录操作"""
        try:
            self.driver.get("https://www.autodl.com/login")
            username_input = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[@id=\"app\"]/div[2]/div[3]/div/div[2]/div[1]/form/div[2]/div/div/input"))
            )
            username_input.clear()
            username_input.send_keys(self.username)

            pwd_input = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"app\"]/div[2]/div[3]/div/div[2]/div[1]/form/div[3]/div/div[1]/input")))
            pwd_input.clear()
            pwd_input.send_keys(self.password)

            login_button = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[@id=\"app\"]/div[2]/div[3]/div/div[2]/div[1]/button[1]"))
            )
            login_button.click()
            time.sleep(1)
            # re检测密码错误字段
            if re.findall(r"密码错误", self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body"))).text):
                logger.error("密码错误")
                return False
            if re.findall(r"用户不存在", self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body"))).text):
                logger.error("用户不存在")
                return False
            # 请输入正确手机号
            if re.findall(r"请输入正确手机号",
                          self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body"))).text):
                logger.error("请输入正确手机号")
                return False
            # return False
            return True
        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            return False

    def renew(self):
        """执行续费流程"""
        # 已在构造函数中初始化，无需重复初始化
        if not self.driver or not self.wait:
            logger.error("浏览器驱动未初始化")
            return False

        try:
            if not self.login():
                return False

            if not _renew_instances(self.driver, self.wait):
                return False

            return True
        except Exception as e:
            logger.error(f"续费流程异常: {str(e)}")
            return False

    def calculate_day(self, day):
        """计算是否需要续费"""
        now_time_str = get_now_time()

        record_time_str = self.get_time()
        if not record_time_str:
            # 如果没有记录，直接续费并记录时间
            logger.info("无历史记录，首次续费")
            self.record_time()
            return True

        try:
            # 将时间字符串转换为时间戳
            now_time_struct = time.strptime(now_time_str, "%Y-%m-%d %H:%M:%S")
            record_time_struct = time.strptime(record_time_str, "%Y-%m-%d %H:%M:%S")

            nt = time.mktime(now_time_struct)
            rt = time.mktime(record_time_struct)

            diff_time = nt - rt

            if diff_time > 3600 * 24 * day:
                logger.info(f'当前时间{now_time_str}')
                if self.renew():
                    self.record_time()
                    logger.info("续费成功")
                    return True
                else:
                    logger.error("续费失败")
                    return False
            else:
                logger.info("时间未到，无需续费")
                return False
        except Exception as e:
            logger.error(f"时间计算失败: {str(e)}")
            return False


if __name__ == '__main__':
    # 加载环境变量
    username = os.getenv("AUTODL_USERNAME")
    password = os.getenv("AUTODL_PASSWORD")

    if not username or not password:
        logger.error("用户名或密码为空，请检查 .env 文件配置")
        raise SystemExit(1)

    try:
        renewer = AutoDLRenewer(username, password)
    except RuntimeError as e:
        logger.error(str(e))
        raise SystemExit(1)

    try:
        # 登录并获取运行状态
        if not renewer.login():
            logger.error("登录失败，无法继续执行")
            raise SystemExit(1)

        # 跳转到个人主页并获取运行中实例数量
        renewer.driver.get("https://www.autodl.com/console/homepage/personal")
        running_count = renewer.get_running_count()

        if running_count is not None and running_count > 0:
            logger.info(f"检测到有 {running_count} 个服务器正在运行，暂停续费流程")
            result = False
        elif renewer.is_running():
            logger.info("检测到有服务器正在运行，暂停续费流程")
            result = False
        else:
            result = renewer.calculate_day(0)

        print(f"续费结果: {result}")

    finally:
        renewer.driver.quit()
