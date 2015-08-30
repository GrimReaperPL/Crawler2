# -- coding: utf-8 --
import web
import AktyWandalizmu

render = web.template.render('templates/')

urls = ('/', 'index', '/results', 'crawl')

class index:
    def GET(self):
      return render.index()

class crawl:
    def GET(self):
        akty = AktyWandalizmu.AktyWandalizmu()
        results = akty.crawl()
        #return render.display(results)
        return results     
      
if __name__ == "__main__": 
    app = web.application(urls, globals())
    app.run()