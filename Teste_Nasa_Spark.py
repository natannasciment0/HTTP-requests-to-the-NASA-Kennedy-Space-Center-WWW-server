'''
	Teste de log - Nasa Kennedy Server
	
	Desenvolvedor: Natan Nascimento
	Data de criação: 09/09/2019

'''


from pyspark import SparkContext, SparkConf
from datetime import datetime
#Regax
import re 


class LogNasa(object):

    def __init__(self):
        self.__conf = SparkConf().setMaster('local[*]')
        self.__files = 'data'

    def date_to_str(self, in_date):
        try: 
			return datetime.fromordinal(in_date).strftime('%d/%b/%Y')
        except Exception as e:
            return '01/01/1500'

	
	def get_url(self, url):	
        try:
            re_result = re.compile('(HEAD|GET|POST) (.*)').match(url[2])
            return url[0] + re_result.group(2).split()[0]
        except Exception as e:
            return ''

	
	def parseLog(self, data):
        RE_MASK = '(.*) - - \[(.*):(.*):(.*):(.*)\] "(.*)" ([0-9]*) ([0-9]*|-)'

        try:
            re_result = re.compile(RE_MASK).match(data)
            host = re_result.group(1)
            ord_day = datetime.strptime(re_result.group(2), '%d/%b/%Y').toordinal()
            req = re_result.group(6)
            reply_code = int(re_result.group(7))
            
            try:
                reply_bytes = int(re_result.group(8))
            except ValueError as e:
                reply_bytes = 0
            return host, ord_day, req, reply_code, reply_bytes
        
        except Exception as e:
            return '', -1, '', -1, -1
		
#quantidade de host unicos		
    def run(self) -> int:
        sc = SparkContext().getOrCreate(self.__conf)

        rows = sc.textFile(self.__files)
        rdd = rows.map(self.parseLog).filter(lambda l: l[1] > -1)
        rdd.cache

        n_host = rdd.keys().distinct().count()
				
		#self.print('Numero de hosts unicos: ', n_host)

#qtd de erros totais
        erro404 = rdd.filter(lambda l: l[3] == 404)
        erro404.cache
        qtd_erro404 = erro404.count()

        url_dt = erro404.map(lambda s: (self.get_url(s), 1)).reduceByKey(lambda a, b: a + b).sortBy(keyfunc=lambda l: l[1], ascending=False)
        
		#self.print('tl de erros 404: ', qtd_erro404)
		
#qtd de erros 404/dia 
        erro_dia = erro404.map(lambda qtd: (qtd[1], 1))
        qtd_erro_dia = erro_dia.reduceByKey(lambda a, b: a + b).sortByKey()
        qtd_erro_data = qtd_erro_dia.collect()

        total_erro_dia = '\n'
        for date_count in qtd_erro_data:
            total_erro_dia += '%s: %d\n' % (self.date_to_str(date_count[0]), date_count[1])
		
		##self.print('qtd de erros 404 p/dia: ', total_erro_dia)
		
 
#top 5 de url erro 		 
        url_erro = url_dt.map(lambda l: l[0]).take(5)
        top5_url_erro = ''.join('\n    %s ' % url for url in url_erro)
		
		##self.print('5 url q tem mais erros 404: ',top5_url_erro)
		


        self.print('(1) Numero de hosts unicos: ', n_host)
        self.print('(2) Numero total de erros 404: ', qtd_erro404)
        self.print('(3) Os 5 URLs que mais causaram erros 404: ',top5_url_erro)
        self.print('(4) Quantidade de erros 404 por dia: ', total_erro_dia)
        return 0

#Chamando classe LogNasa
def main() -> int:
    return LogNasa().run()

if __name__ == '__main__':
    main()