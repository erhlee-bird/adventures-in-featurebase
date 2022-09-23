import os
import sys
import time

from polling2 import poll
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options


# Verify configuration options have been set.

ready = True
for envvar in ["USERNAME", "PASSWORD", "TABLENAME"]:
  value = os.getenv(envvar)
  if not value:
    print(f"Need '{envvar}' environment variable to be set...")
    ready = False
    continue
  globals()[envvar.lower()] = value

if not ready:
  sys.exit(1)

# Start the driver.

options = Options()
options.binary_location = "/run/current-system/sw/bin/google-chrome-stable"

driver = webdriver.Chrome(chrome_options=options, keep_alive=False)

def quit():
  driver.close()
  driver.quit()

# Sign in.

driver.get("https://cloud.featurebase.com/login")
driver.delete_all_cookies()
driver.find_element_by_id("email").send_keys(username)
driver.find_element_by_id("password").send_keys(password)
def sign_in():
  for button in driver.find_elements_by_tag_name("button"):
    if button.text.upper() == "SIGN IN":
      button.click()
      return True
  else:
    print("Couldn't sign in...")
    quit()
poll(sign_in, step=1, timeout=10)

time.sleep(5)

# Go to "Tables".

def to_tables():
  for link in driver.find_elements_by_tag_name("a"):
    if link.get_property("title") == "Tables":
      link.click()
      return True
  else:
    print("Couldn't navigate to Tables...")
    quit()
poll(to_tables, step=1, timeout=10)

time.sleep(5)

# Locate target table.

def load_table():
  for link in driver.find_elements_by_tag_name("a"):
    if link.text == tablename:
      link.click()
      return True
  else:
    print("Couldn't find table...")
poll(load_table, step=1, timeout=10)

time.sleep(5)

# Go to "Columns".

def to_columns():
  for button in driver.find_elements_by_tag_name("button"):
    if button.text.upper() == "COLUMNS":
      button.click()
      return True
  else:
    print("Couldn't find columns...")
poll(to_columns, step=1, timeout=10)

time.sleep(5)

# Begin creating fields for the table.
