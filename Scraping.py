# import libraries
import pandas as pd
import numpy as np
import flask
from flask import render_template
from flask import Flask
import requests
from bs4 import BeautifulSoup
eventCode = input("input event code")
URL = "https://www.thebluealliance.com/event/2024" + eventCode + "#rankings"

page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")

rankings = soup.find(id ="rankingsTable").text
rankings = rankings.split("\n")
newList = []
for x in rankings:
    x = x.strip()
    if len(x) != 0:
        newList.append(x)


newList = np.array(newList).reshape(-1, 11).tolist()
df = pd.DataFrame(newList)
