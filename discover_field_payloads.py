import os
import shutil
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


def driver_quit():
  driver.close()
  driver.quit()


def click_that(
    tag_name,
    attrs=[],
    click=True,
    props=[],
    raise_if_not_found=True,
    text=None,
    timeout=5,
    upper=True
):
  retval = None
  def inner():
    nonlocal retval

    for elem in driver.find_elements_by_tag_name(tag_name):
      match = True

      for attr in attrs:
        key, value = attr
        match &= elem.get_attribute(key) == value
      for prop in props:
        key, value = prop
        match &= elem.get_property(key) == value
      if text is not None:
        left = elem.text.upper() if upper else elem.text
        right = text.upper() if upper else text
        match &= left == right
      if match:
        if click:
          elem.click()
        retval = elem
        return True
    else:
      if not raise_if_not_found:
        return True
      print(f"Could not find <{tag_name}> with:")
      for k, v in attrs:
        print(f"  - {k}={v}")
      for k, v in props:
        print(f"  - {k}={v}")
      if text is not None:
        print(f"  - text={text}")
      raise RuntimeException("click_that failure")
  poll(inner, step=1, timeout=10)
  time.sleep(timeout)
  return retval


# Sign in.
def sign_in():
  driver.get("https://cloud.featurebase.com/login")
  driver.delete_all_cookies()
  driver.find_element_by_id("email").send_keys(username)
  driver.find_element_by_id("password").send_keys(password)
  click_that("button", text="SIGN IN")


def visit_table():
  # Go to "Tables".
  click_that("a", props=[("title", "Tables")], timeout=3)

  # Locate target table.
  click_that("a", text=tablename, timeout=3, upper=False)

  # Go to "Columns".
  click_that("button", text="COLUMNS", timeout=3)


columns = [
  ("a", "int"),
  ("b", "timestamp"),
  ("c", "decimal"),
  ("d", "string"),
  ("e", "stringset"),
  ("f", "id"),
  ("g", "idset"),
]
columns_map = dict(columns)

def delete_fields():
  for cname, _ in columns:
    print(f"deleting column {cname}")
    action_menu = click_that("button", props=[("id", f"action-menu-{cname}")], timeout=1)
    # Field not found.
    if not action_menu:
      continue
    click_that("li", props=[("role", "menuitem")], timeout=1)
    click_that("input", props=[("id", "confirmDelete")], timeout=1).send_keys("DELETE")
    click_that("button", props=[("type", "submit")], text="DELETE", timeout=1)


def make_fields():
  # Begin creating fields for the table.
  for cname, ctype in columns:
    print(f"creating column {cname} - {ctype}")
    click_that("button", props=[("type", "button")], text="Add column", timeout=1)

    # Set the Column name.
    click_that("input", click=False, props=[("id", "name")], timeout=1).send_keys(cname)

    # Set the Column type.
    click_that("div", props=[("id", "type")], timeout=1)
    click_that("li", attrs=[("data-value", ctype)], timeout=1)

    click_that("button", props=[("type", "submit")], text="Add column")


def write_requests():
  # Back up existing results.
  if os.path.exists("data/field_payloads.jsonl"):
    shutil.copy("data/field_payloads.jsonl", f"data/field_payloads.{int(time.time())}.jsonl")

  with open("data/field_payloads.jsonl", "a") as fd:
    for r in driver.requests:
      if f"{tablename}/fields/" not in r.url:
        continue
      field = os.path.basename(r.url)
      ctype = columns_map[field]
      fd.write(ctype + "," + r.body.decode() + "\n")


sign_in()
visit_table()
delete_fields()
del driver.requests
make_fields()
write_requests()
driver_quit()
