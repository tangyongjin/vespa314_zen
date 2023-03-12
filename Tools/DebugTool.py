import pandas 
from colorama import Fore, Back, Style
import pprint

def cprint(pobj, pcolor = Fore.GREEN):
      from IPython.display import Markdown
      
      if type(pobj).__name__ != 'str':
        print(  "类型:"+ type(pobj).__name__ )
      
      if type(pobj).__name__ == 'str':
          print(pcolor )
          print(pobj)
          print(pcolor) 
          print(Style.RESET_ALL)

          
      else:
          if isinstance(pobj, pandas.core.frame.DataFrame):
                print(pcolor )
                print(pobj.head(10).to_string())  
                print(pcolor) 
                print(Style.RESET_ALL)
                
          if type(pobj) is list:
                print("是个列表")
                print( pcolor )
                print(  len(pobj))
                print ('\n'.join([ str(myelement) for myelement in pobj ]))
         
          if  type(pobj).__name__ == 'KLineOrginal':
                print("KLineOrginal")
                print(vars(pobj))
          
          if  type(pobj).__name__ == 'Seg_meta':
                print(vars(pobj))

          if  type(pobj).__name__ == 'BuySel_Point':
                print("BuySel_Point")
                print(vars(pobj))
 
                      