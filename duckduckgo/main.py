from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import  Options
from shutil import which
import pprint

chrome_options = Options()
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--log-level=1')
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

chrome_path = which('chromedriver')


driver = webdriver.Chrome(executable_path= chrome_path, options=chrome_options)



driver.get('https://duckduckgo.com')

search_input = driver.find_element_by_id('search_form_input_homepage')
search_input.send_keys("site:linktr.ee")

def click_show_more():
    
    
    if driver.find_element_by_xpath("//*[contains(@class,'result--more')]"):
        driver.implicitly_wait(5)
        show_more = driver.find_element_by_xpath("//*[contains(@class,'result--more')]")
        
        show_more.click()
        click_show_more()
        
    
    else:
        driver.quit()   

# link = driver.find_element_by_xpath("//div[@class = 'result result--more']")
# show_more_btn = driver.find_element_by_id('search_button_homepage')
# show_more_btn.click()

search_input.send_keys(Keys.ENTER)
# link = driver.find_element_by_xpath("//div[@class = 'nrn-react-div']/article/div[@class = 'ikg2IXiCD14iVX7AdZo1']/h2/a")
# print(link)

# pprint.pprint(driver.current_url)
click_show_more()

# driver.close()

