import datetime
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import FirefoxOptions


import azure.functions as func


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info(scrap())

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

def scrap():
# URL base del portal BioPortal
  base_url = 'https://lod-cloud.net/clouds/lod-cloud.svg'

  stats = {'total': 0, 'hasLicense': 0, 'hasSparqlEndpoint': 0, 'errors': [], 'errorsCount': 0}
  # Realizar una solicitud GET a la página principal de ontologías
  response = requests.get(base_url)
  # Comprobar el estado de la respuesta
  if response.status_code == 200:
    
    # Crear un objeto BeautifulSoup para analizar el contenido HTML de la página
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Encontrar todos los enlaces a las ontologías en la página
    links = soup.find_all('a', class_='bubble')
    
    # Recorrer los enlaces y descargar las ontologías
    for link in links[1110:]:
        ontology_url = link['href']
        ontology_name = link.text.strip()

        # Realizar una solicitud GET a la URL de la ontología
        try:  
          dataset = clasify(ontology_url)
          dataset['url'] = ontology_url
          print(dataset)
          store(dataset)
          if(dataset['hasSPARQLEndpoint']):
            stats['hasSparqlEndpoint']= stats['hasSparqlEndpoint']+1
          if(dataset['hasLicense']):
            stats['hasLicense']= stats['hasLicense']+1     
        except:
          stats['errors'].append(ontology_url)
          stats['errorsCount']= stats['errorsCount']+1

        stats['total']= stats['total']+1
        logging.info(stats)

    logging.info(stats)    
  else:
      logging.error('Error al acceder al portal LODCLOUD')
  return stats


def clasify(dataset_url):  
  opts = FirefoxOptions()
  opts.add_argument("--headless")
  driver = webdriver.Firefox(options=opts)
  #dataset_url = 'https://lod-cloud.net/dataset/cz-vavai-research-plans'
  driver.get(dataset_url)
  html = driver.page_source
  driver.close()
  soup = BeautifulSoup(html)
  sparkep = False;
  dataset = {}
  dataset['hasLicense'] = False
  dataset['hasSPARQLEndpoint'] = False

  #verificación información de procedencia

  # 1- Licencia
  div_license_div = soup.find('div', class_='license')
  if div_license_div is not None:
    div_license = div_license_div.findChild('a')
    dataset['license'] = div_license.text.strip()
    dataset['hasLicense'] = True

  # 2- titulo, descripción
  title = soup.find('h1')
  if title is not None:
    titletext = title.text.replace('(Edit)', '')
    dataset['title'] = titletext

  descripcion = soup.select('div#app .row .col-md-10')
  if descripcion is not None:
    dataset['descripcion'] = descripcion[1].text.strip()

  # 3- Procedencia
  author = soup.find('div', class_='contactPoint').findChild('a')
  if author is not None:
    dataset['author'] = author.text.strip() 

  publisherdiv = soup.find('div', class_='website')
  if publisherdiv is not None:
    publisher = publisherdiv.findChild('a')
    dataset['publisher'] = publisher.text.strip()

  # 4- SPARQL

  spqrql_title = soup.find('h4', string='SPARQL Endpoints')
  if spqrql_title is not None:
    div = spqrql_title.parent
    ul = div.findChildren('ul')
    li = ul[0].findChildren('li')
    a = li[0].findChildren('a')
    sparql_endpoint = a[0]['href']
    dataset['sparql_endpoint'] = sparql_endpoint
    dataset['hasSPARQLEndpoint'] = True
    
  # 5- Valor de confianza
  stars = soup.find(id="stars_img")
  if stars is not None:
    dataset['stars'] = [x for x in stars["src"] if x.isdigit()][0]

  return dataset

def store(dataset):
  from rdflib import Graph, Literal, URIRef
  from rdflib.namespace import RDF
  from rdflib import Namespace
  import urllib3
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

  # Create a new RDF graph
  graph = Graph()

  # Define namespaces  
  uri = dataset['url'].split('/')
  instance_uri = URIRef(f'http://www.semanticweb.org/k_mil/ontologies/2021/8/EvalLOD#{uri[-1].replace(" ","")}')
  print(instance_uri);
  void = Namespace("http://rdfs.org/ns/void#")
  dcterms = Namespace("http://purl.org/dc/terms/")
  w3c = Namespace("http://www.w3.org/ns/adms#")
  trust = Namespace("http://trdf.sourceforge.net/trustvocab#")
  evalod = Namespace("http://www.semanticweb.org/k_mil/ontologies/2021/8/EvalLOD#")
  xsd = URIRef("http://www.w3.org/2001/XMLSchema#")

  # Add triples to the graph to represent the instance and quality evaluations
  graph.add((instance_uri, RDF.type, void.dataset))  
  graph.add((instance_uri, dcterms.title, Literal(dataset['title'])))
  graph.add((instance_uri, dcterms.description, Literal(dataset['descripcion'])))
  print(dataset['stars'])
  graph.add((instance_uri, evalod.reputationScore, Literal(dataset['stars'])))
  graph.add((instance_uri, evalod.hasProvenance, Literal("3")))
  if "publisher" in dataset:
    graph.add((instance_uri, dcterms.publisher, Literal(dataset['publisher'])))
    graph.add((instance_uri, dcterms.publisher, Literal(dataset['publisher'])))
    graph.add((instance_uri, evalod.isVerifiable, Literal("2")))
    graph.add((instance_uri, evalod.isTrusworthy, Literal("4")))
    graph.add((instance_uri, evalod.isTrusworthy, Literal("4")))
    graph.add((instance_uri, evalod.hasProvenance, Literal("5")))

  graph.add((instance_uri, dcterms.creator, Literal(dataset['author'])))
  graph.add((instance_uri, w3c.accessURL, Literal(dataset['url'])))


  if(dataset['hasSPARQLEndpoint']):
    graph.add((instance_uri, void.sparqlEndpoint, Literal(dataset['sparql_endpoint'])))
    graph.add((instance_uri, evalod.isVerifiable, Literal("3")))

  if(dataset['hasSPARQLEndpoint'] & ("publisher" in dataset)):
    graph.add((instance_uri, evalod.isVerifiable, Literal("5")))


  if(dataset['hasLicense']):
    graph.add((instance_uri, evalod.hasLicense, Literal("5")))
  else:    
    graph.add((instance_uri, evalod.hasLicense, Literal("0")))



  # Serialize the RDF graph to a string
  instance_data = graph.serialize(format='turtle', encoding='utf-8')

  # Send the instance data to the Fuseki server using HTTP POST
  base_url = "https://fusekiserver.eastus.cloudapp.azure.com/"
  dataset_name = "Evalod"
  store_url = f"{base_url}{dataset_name}/data"
  headers = {'Content-Type': 'text/turtle'}
  response = requests.post(store_url, data=instance_data, headers=headers, verify=False)

  # Check the response status code
  if response.status_code == 200:
      print("Instance stored successfully.")
  else:
      print("Error storing instance:", response.text)