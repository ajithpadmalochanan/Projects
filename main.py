import requests
import json
import pyttsx3
import speech_recognition as sr
import re
import pyaudio
import threading
import time
API_KEY = "tVX6TSH4X6vL"
PROJECT_TOKEN = "thmxaJfzfqLT"
RUN_TOKEN = "twUHsWdQDLzo"
#print(data['total'])
class Data:
    def __init__(self,api_key,project_token):
        self.api_key = api_key
        self.project_token = project_token
        #params instead of context used in django!!
        self.params = {
            "api_key" : self.api_key
        }
        self.data=self.get_data()
 #get most recent data
    def get_data(self):
        response = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data',params=self.params)
        data=json.loads(response.text)
        return data
   #get total cases
    def get_total_cases(self):
       data=self.data['total']
       for content in data:
           if content['name']=="Coronavirus Cases:" :

               return content['value']

    def get_total_deaths(self):
        data=self.data['total']
        for content in data:
            if content['name']=="Deaths:":
                return content['value']
    def get_country_data(self,country):
        data=self.data['country']
        for content in data:
            if content['name'].lower()==country.lower():
                return content
        return 0 
    #list of countries
    def get_list_of_countries(self):
        countries = []
        for country in self.data['country']:
            countries.append(country['name'].lower())
        return countries       
    #update data import threading and time, then post req    proj token /run
    def update_data(self):
        response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run',params=self.params)
        

        def poll():
            #when one thread is idle it release itself amd let the other thread work
            time.sleep(0.1)
            old_data = self.data
            while True:
                new_data= self.get_data()
                if new_data != old_data:
                    self.data= new_data
                    print("Data Updated")
                    break
                time.sleep(5) 
#thread wont interfere with the other voice assistant part
        t= threading.Thread(target=poll)
        t.start()


#datas = Data(API_KEY ,PROJECT_TOKEN)     
#print(datas.get_list_of_countries())   
#print(datas.get_country_data("india")['total_deaths'])
#for the system to speak 


def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
#speak("Hello")        
def  get_audio():
    r=sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""
            
        try:
            said=r.recognize_google(audio)
          
        except Exception as e:
            print("Exception:",str(e))

    return said.lower()
#print what we said
#print(get_audio())                


def main():
    print("start program")
    datas = Data(API_KEY ,PROJECT_TOKEN)     
    END_PHRASE = "stop"
    #print(set(list(datas.get_list_of_countries())))
    country_list= datas.get_list_of_countries()

    TOTAL_PATTERNS= {
        re.compile("[\w\s]+ total [\w\s]+ cases"):datas.get_total_cases,
        re.compile("[\w\s]+ total cases"):datas.get_total_cases,
        re.compile("[\w\s]+ total [\w\s]+ deaths"):datas.get_total_deaths,
        re.compile("[\w\s]+ total deaths"):datas.get_total_deaths,

    }
    COUNTRY_PATTERNS = {
        re.compile("[\w\s]+ cases [\w\s]+"): lambda country: datas.get_country_data(country)['total_cases'],
        re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: datas.get_country_data(country)['total_deaths'],  
    }
    UPDATE_COMMAND = "update"
    while True:
        print("listening...")
        text = get_audio()
        print(text)
        #initializing results
        result =None 
        for pattern,func in COUNTRY_PATTERNS.items() :
            if pattern.match(text):
                words = text.split(" ")
                for country in country_list:     
                    if country in words:
                        print(country)
                        result =func(country)
                        break  
        for pattern,func in TOTAL_PATTERNS.items() :
            if pattern.match(text):
                result =func()
                break
        if text== UPDATE_COMMAND:
            result ="Data is being updated. This may take a moment"
            datas.update_data()
        if result:
            speak(result)

        #stop loop if we say stop
        if text.find(END_PHRASE)!= -1:
            print("Exit")
            break


main()