import pandas as pd

def generate_

df = pd.read_html("https://en.wikipedia.org/wiki/List_of_companies_operating_trains_in_the_United_Kingdom",
                  flavor="bs4", attrs={"class": "wikitable"})[0]

operator_list = df['Operator'].tolist()
