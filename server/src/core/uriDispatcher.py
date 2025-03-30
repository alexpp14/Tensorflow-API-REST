from os import getcwd, chdir, listdir
from importlib import import_module
from re import search

from src.http.parser import Parser
from src.http.response import Response
from src.dao.dao import DAO

class URI_Dispatcher:

    def __init__(self, path : str = "src/rest") -> None:
        
       
        self.__restClasses : list[type] = []
        #chdir("Server")
        currentDir = getcwd()
      
        chdir(path)
        
        package = path.replace("/",".")

        for file in listdir():

            if file.endswith("Rest.py"):

                file = file[:-3]

                module = import_module(package + "." + file)
                self.__restClasses.append(getattr(module,module.__dir__()[-1]))

        chdir(currentDir)

    def dispatch(self, parser : Parser, dao : DAO) -> Response:

        for classes in self.__restClasses:

            instance = classes(dao,parser)

            if hasattr(instance,"map"):

                restMap : dict[tuple[str,str],str] = getattr(instance,"map")

                for method_uri, callback in restMap.items():

                    method, uri = method_uri

                    if method == parser.method and (matches := search(uri,parser.uri)) is not None:

                       

                        return getattr(instance,callback)(*matches.groupdict().values())


        return Response(400,body="URL couldn't be dispatched")