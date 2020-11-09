import csv
import io
import requests
import lxml
import re
from bs4 import BeautifulSoup
import pandas as pd

#Will need to be updated regularly as URLs are changed
cur_URL = 'https://www.gov.ie/en/publication/1d513-updates-on-covid-19-coronavirus-from-october-2020/'
jul_url = 'https://www.gov.ie/en/publication/b6a9e-updates-on-covid-19-coronavirus-from-july-september-2020/'
apr_url = 'https://www.gov.ie/en/publication/72d92-updates-on-covid-19-coronavirus-from-april-june-2020/'
jan_url = 'https://www.gov.ie/en/publication/ce3fe8-previous-updates-on-covid-19-coronavirus/'


def get_links(c_url):
    base_url: str = 'https://www.gov.ie'

    content = requests.get(c_url)
    soup = BeautifulSoup(content.content, 'html.parser')
    #print(soup.prettify())

    links = []

    for link in soup.find_all('a'):
        link_url = link.get('href')
        if link_url:
            if '/en/press-release/' in link_url:
                if link_url[0:4] == '/en/':
                    links.append(f"{base_url}{link_url}")
                else:
                    links.append(link_url)

    return links

links = get_links(cur_URL)
links.extend(get_links(jul_url))
links.extend(get_links(apr_url))
links.extend(get_links(jan_url))
#print(links)

df_county = pd.DataFrame()
df_temp = pd.DataFrame()
i = 0

for publication_link in links:
    #if i == 5:
        #pass
        #break

    print(f"Getting table from {publication_link}")
    content = requests.get(publication_link)
    soup = BeautifulSoup(content.content,'html.parser')

    published_search = re.search('Published at(.*)2020', content.text, re.IGNORECASE)
    if published_search:
        published_date = published_search.group(1).strip()
        published_search = re.search('time datetime="(.*)">', published_date, re.IGNORECASE)
        published_date = published_search.group(1).strip()

    else:
        published_date = ''
        
    num_tables = len(soup.find_all('table'))

    if num_tables > 1:
        tables = pd.read_html(content.text)
    
        if num_tables == 8: #8 tables on 20th March
            table = tables[num_tables-2]   
        #elif published_date > "2020-04-07": #Extra table listing unknowns add on 2020-04-08
            #table = tables[num_tables-2]
        else:
            table = tables[num_tables-1]
        
        if published_date < "2020-03-21": #Tables prior had headings. 
            table = table.drop(table.index[0])

        if published_date > "2020-05-12": #Tables after have headings. 
            table = table.drop(table.index[0])
        
        
        table = table.rename({0:'County', 1:'Cases', 2:'Percentage'},axis='columns')
        
        #if published_date < "2020-04-04":
         #   table['Cases'] = table['Cases'].map(lambda x: x.lstrip('≤'))

        table['Published_date'] = published_date
        table['Source'] = publication_link
    
        print('Table saved')
        df_county = df_county.append(table)
        
    i = i + 1

df_county['Percentage'] = df_county['Percentage'].fillna('0')
print(df_county)

csvFile = 'countyData.csv'
df_county.to_csv(csvFile, index=False, header=True)
    