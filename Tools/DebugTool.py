import pandas 
from colorama import Fore, Back, Style
import pprint

def cprint(pobj):
      from IPython.display import Markdown
      
      if type(pobj).__name__ != 'str':
        print(  "类型:"+ type(pobj).__name__ )
      
      if type(pobj).__name__ == 'str':
          display (Markdown('<span style="color: #3fbf72">'+pobj+'</span>'))
      else:
          
        
          if isinstance(pobj, pandas.core.frame.DataFrame):
                print(Fore.GREEN )
                print(pobj.head(10).to_string())  
                print(Fore.GREEN) 
                print(Style.RESET_ALL)
                
          if type(pobj) is list:
                print("是个列表")
                print(Fore.GREEN )
                print(  len(pobj))
                print ('\n'.join([ str(myelement) for myelement in pobj ]))
         
         
         
          if  type(pobj).__name__ == 'CSeg_meta':
                print("CSeg_meta")
                print(vars(pobj))
 
          if  type(pobj).__name__ == 'CBS_Point':
                print("CBS_Point")
                print(vars(pobj))
 
                      
        
         
          
 

    