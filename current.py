import pandas as pd
import numpy as np
import flask
from flask import render_template
from flask import Flask, request

import requests
from bs4 import BeautifulSoup


app = Flask(__name__)


@app.route('/')
def home():
    return HOME_HTML


HOME_HTML = """
    <html><body>
        <h2>Welcome to the Greeter</h2>
        <form action="/greet">
            Input Event Code <input type='text' name='eventCode'><br>
            <input type='submit' value='Continue'>
        </form>
    </body></html>"""


@app.route('/greet')
def greet():
    eventCode = request.args.get('eventCode', '')
    if eventCode == '':
        msg = 'Failed to input event code'
    else:
        URL = "https://www.thebluealliance.com/event/2024" + eventCode + "#rankings"
        # concoctanates the URL to use for webscraping

        page = requests.get(URL)
        # creates a page object of the scouting data

        soup = BeautifulSoup(page.content, "html.parser")

        rankings = soup.find(id="rankingsTable").text
        # isolates the data table in the html code and converts it to text
        rankings = rankings.split("\n")
        # breaks the data into invidual strings
        dataList = []
        for value in rankings:
            value = value.strip()
            if len(value) != 0:
                dataList.append(value)

        # appends all non-empty strings from the data to the data list with excess whitespace removed
        # This allows the data to be formatted as a table

        # ----------------------------------------------------------------------------------------------------------------------
        # Table Creation

        newList = np.array(dataList).reshape(-1, 11).tolist()
        # Converts the data list into a table

        headings = newList[0]
        data = newList[1:]
        rawData = pd.DataFrame(data, columns=headings)
        analyzedData = rawData.drop(
            ['Ranking Score', 'Avg Coop', 'Avg Match', 'Record (W-L-T)', 'DQ', 'Played', 'Total Ranking Points*'],
            axis=1, inplace=False)
        # creates the analzyed version of the data table with excess information removed
        record = rawData['Record (W-L-T)'].tolist()
        # I want to add a win percentage to the analyzed data. I convert the win record from the raw data into a list
        # so each string can be converted into a win percentage and then add that column to the analyzed data frame

        i = 0
        while i < len(record):
            record[i] = record[i].split("-")
            # breaks each win record into a list containing win, loss, and tie values
            record[i] = (int(record[i][0]) / (int(record[i][0]) + int(record[i][1]) + int(record[i][2]))) * 100
            record[i] = round(record[i], 2)
            # computes and rounds the win percentage
            i = i + 1

        analyzedData['Win %'] = record
        # adds the win percentage to the analyzed data table

        URL2 = "https://www.thebluealliance.com/event/2024" + eventCode + "#event-insights"
        # concoctanates the URL to use for webscraping

        data = requests.get(URL2).text
        soup = BeautifulSoup(data, 'html.parser')
        soup = soup.prettify()
        soup = soup.split('OPR')
        OPR = soup[5]
        OPR = OPR.split("]]")
        OPR = OPR[0].split(",")
        OPRlist = []
        for x in OPR:
            x = x.replace("[", " ")
            x = x.replace("]", " ")
            x = x.replace("\"", " ")
            x = x.replace("\'", " ")
            x = x.replace(":", " ")
            OPRlist.append(x.strip())

        a = 1
        while a < len(OPRlist):
            if a % 2 != 0:
                OPRlist[a] = round(float(OPRlist[a]), 2)
            a = a + 1

        OPRdict = {}
        for i in range(0, len(OPRlist), 2):
            OPRdict[OPRlist[i]] = OPRlist[i + 1]

        OPRdf = pd.DataFrame(list(OPRdict.items()), columns=['Team', 'OPR'])
        analyzedData = pd.merge(analyzedData, OPRdf, how="left")

        URL = "https://docs.google.com/spreadsheets/u/1/d/e/2PACX-1vQdEySR4HFSmPRIkghkzGFKMjrSRVu-K0P9uFterllQZFikHt1bnO-m7h-mV3B2pwamRy9jIIu5-fOa/pubhtml"
        # concoctanates the URL to use for webscraping
        qualData = pd.read_html(URL)
        qualData = qualData[0]
        qualData.columns = qualData.iloc[0]
        qualData = qualData.drop(["Timestamp", 1.0], axis=1)
        qualData = qualData.drop(labels=[0, 1])

        # create new DataFrame by combining rows with same id values
        qualData = qualData.groupby(['Team']).agg({'Notes': ', '.join}).reset_index()

        analyzedData = pd.merge(analyzedData, qualData, how="left")
        analyzedData['Avg Auto'] = analyzedData['Avg Auto'].astype(float)
        analyzedData['Avg Stage'] = analyzedData['Avg Stage'].astype(float)
        analyzedData['Rank'] = analyzedData['Rank'].astype(float)

        analyzedData['Prediction'] = round((((analyzedData['OPR']) * 0.25) + ((analyzedData['Avg Auto']) * 0.3) + (
                    (analyzedData['Avg Stage']) * 0.1) + (abs(analyzedData['OPR'] - analyzedData['Rank'])) * 0.35) / 4,
                                           2)
        analyzedData = analyzedData.drop(['Rank'], axis=1)
        analyzedData = analyzedData.sort_values(by=['Prediction'], ascending=False)
        analyzedData = analyzedData.reset_index()

        # convert dataframe to html
        msg = analyzedData.to_html() + rawData.to_html()
        #msg = eventCode

    return GREET_HTML.format(eventCode, msg)


GREET_HTML = """
    <html><body>
        <h2>Hello, {0}!</h2>
        {1}
    </body></html>
    """

if __name__ == "__main__":
    # Launch the Flask dev server
    #app.run(host="localhost", debug=True)
    app.run(debug=True)

@app.route('/')
def index():
   #return render_template('index.html')  # this line only displays files in the templates sub directory.  To display from other directories, see below
   return flask.send_from_directory(".", path="index.html")
#if __name__ == '__main__':
 #  app.run()