import pyttsx3
import meteofrance_api
import datetime
from babel.dates import format_datetime
import requests
from bs4 import BeautifulSoup
import smtplib
import feedparser
from email.mime.multipart import MIMEMultipart

class Assistant():
    def __init__(self) -> None:
        self.engine = pyttsx3.init()
    
    def say(self,text : str):
        self.engine.say(text)
        self.engine.runAndWait()
        self.engine.stop()


    def __get_rss_feed(self,rss_feed_url : str):
        feed = feedparser.parse(rss_feed_url)
        return feed.entries
    
    def __get_traffic_info(self):
        reseau_astuce_rss_feed = "https://www.reseau-astuce.fr/fr/rss/Disruptions"
        reseau_astuce_feed = self.__get_rss_feed(reseau_astuce_rss_feed)
        for article in reseau_astuce_feed:
            if str(article.title).__contains__("M"):
                return article.title
        return "Aucune perturbation du réseau aujourd'hui."
        

    def __find_news(self):
        feeds = {"lequipe" : "https://dwh.lequipe.fr/api/edito/rss?path=/Football/","lemonde" : "https://www.lemonde.fr/rss/une.xml"}
        lequipe_feed = self.__get_rss_feed(feeds.get("lequipe"))
        lemonde_feed = self.__get_rss_feed(feeds.get("lemonde"))
        return [(lequipe_feed[0].link,lequipe_feed[0].title),(lemonde_feed[0].link,lemonde_feed[0].title)]

    def send_hello_email(self):
        print("What's your the email address you want it to be sent to ?")
        email = input()
        print("What's the server ?")
        server = input()
        print("What's the password ?")
        passwd = input()

        from email.mime.text import MIMEText



        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Récapitulatif de la journée du {self.__get_date()[0]}"
        msg['From'] = email
        msg['To'] = email

        news = self.__find_news()
        traffic_news = self.__get_traffic_info()

        html = """\
        <html>
        <head></head>
        <body>
            <h2>Bonjour {name}, comment allez vous ?</h2>
            <p>{info_journee}</p><br/>
            <h3>Voici les informations d'aujourd'hui</h3>
            <ul>
                <li><a href = "{news_1_link}">{news_1_title}</a></li>
                <li><a href = "{news_2_link}">{news_2_title}</a></li>
                <li>{traffic_news}</li>
            </ul>

            <h3> Passez une bonne journée </h3>

        </body>
        </html>
        """.format(name = email,info_journee = self.collect_info(),traffic_news = traffic_news,news_1_link = news[0][0],news_2_link = news[1][0],news_1_title = news[0][1],news_2_title = news[1][1])

        part2 = MIMEText(html, 'html')
        msg.attach(part2)
        server = smtplib.SMTP_SSL(server, 465)
        server.login(email, passwd)

        server.sendmail(
            email,
            email,   
            msg.as_string())
        server.quit()

    def collect_info(self):
        location = self.get_location()
        weather = self.__fetch_weather(location)
        date,heure,*rest = self.__get_date()
        heure = heure.replace(":","h")
        return f"Nous sommes le {date}, il est {heure} et aujourd'hui le temps sera {weather.get('description').lower()} avec des températures allant de {weather.get('minimal')} à {weather.get('maximal')} degrés à {location}"

    def __fetch_weather(self,place : str):
        client = meteofrance_api.MeteoFranceClient()
        place = client.search_places(place)[0]
        forecast = client.get_forecast_for_place(place)
        return {"description" : forecast.today_forecast.get('weather12H').get("desc"),"minimal" : int(forecast.today_forecast.get('T').get("min")),"maximal" : int(forecast.today_forecast.get('T').get("max"))}
        
    def __get_date(self):
        date_formatee = format_datetime(datetime.datetime.now(), format='short', locale='fr')
        return (date_formatee.split(" "))
    
    
    def __get_ip(self):
        response = requests.get('https://api64.ipify.org?format=json').json()
        return response["ip"]

    def get_location(self):
        ip_address = self.__get_ip()
        response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
        location_data = {
            "ip": ip_address,
            "city": response.get("city"),
            "region": response.get("region"),
            "country": response.get("country_name")
        }
        return location_data.get("city")

a = Assistant()
a.send_hello_email()

