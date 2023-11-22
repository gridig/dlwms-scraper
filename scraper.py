from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# Function to read previously stored data from a CSV file
def read_previous_data():
    try:
        with open('data.csv', 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return [row for row in reader]
    except FileNotFoundError:
        return []

# Function to write newly fetched data to a CSV file
def write_new_data(new_data):
    with open('data.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=new_data[0].keys())
        writer.writerows(new_data)

# Function to send email
def send_email(new_data):
    sender_email = os.getenv( "SENDER_EMAIL" )
    sender_password = os.getenv( "SENDER_PASSWORD" )
    receiver_email = os.getenv( "RECEIVER_EMAIL" )
    sender_name = "FIT DLWMS"

    # Create message container
    msg = MIMEMultipart()
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['To'] = receiver_email
    msg['Subject'] = new_data[0]['Title']

    # Prepare email body with new data
    body = f"<strong>{new_data[0]['Subject']}</strong><br/><p>{new_data[0]['Abstract']}<br/><br/>Objavljeno {new_data[0]['Date']}<em> <a href='{new_data[0]['HyperlinksLink']}'>{new_data[0]['Hyperlinks']}</a></em><br/><br/><a href='{new_data[0]['TitleLink']}'>Procitaj na DLWMS</a></p>"

    msg.attach(MIMEText(body, 'html'))

    # Send the email
    with smtplib.SMTP('smtp.office365.com', 587) as smtp_server:
        smtp_server.starttls()
        smtp_server.login(sender_email, sender_password)
        smtp_server.send_message(msg)

# Function to scrape data, compare, and send email
def scrape_compare_send():
    chrome_driver_path = '/opt/homebrew/bin/chromedriver'
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    url = 'https://www.fit.ba/student/'
    student_no = os.getenv( "STUDENT_NO" )
    dlwms_password = os.getenv( "DLWMS_PASSWORD" )
    driver.get(url)

    broj_dosijea = driver.find_element(By.ID, 'txtBrojDosijea')
    lozinka = driver.find_element(By.ID, 'txtLozinka')
    prijava = driver.find_element(By.ID, 'btnPrijava')

    broj_dosijea.send_keys(student_no)
    lozinka.send_keys(dlwms_password)
    prijava.click()

    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'dgObavijesti'))
        )
        news_lists = table.find_elements(By.CLASS_NAME, 'newslist')

        dates = []
        subjects = []
        titlesText = []
        titlesHref = []
        abstracts = []
        hyperlinksText = []
        hyperlinksHref = []

        for news_list in news_lists:
            span_date = news_list.find_element(By.ID, 'lblDatum')
            span_subject = news_list.find_element(By.ID, 'lblPredmet')
            a_tag = news_list.find_element(By.ID, 'lnkNaslov')
            div_abstract = news_list.find_element(By.CLASS_NAME, 'abstract')
            a_hyperlink = news_list.find_element(By.ID, 'HyperLink9')

            dates.append(span_date.text)
            subjects.append(span_subject.text)
            titlesText.append(a_tag.text)
            titlesHref.append(a_tag.get_attribute('href'))
            abstracts.append(div_abstract.text)
            hyperlinksText.append(a_hyperlink.text)
            hyperlinksHref.append(a_hyperlink.get_attribute('href'))

        new_data = []
        for i in range(len(dates)):
            new_data.append({
                'Date': dates[i],
                'Subject': subjects[i],
                'Title': titlesText[i],
                'TitleLink': titlesHref[i],
                'Abstract': abstracts[i],
                'Hyperlinks': hyperlinksText[i],
                'HyperlinksLink': hyperlinksHref[i]
            })

        previous_data = read_previous_data()
        new_rows = [row for row in new_data if row not in previous_data]

        if new_rows:
            send_email(new_rows)

        write_new_data(new_data)

    except Exception as e:
        print(f"Exception occurred: {e}")

    driver.quit()

# Call the function to scrape, compare, and send email
scrape_compare_send()
