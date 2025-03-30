
class HTTPCode:

    def __init__(self) -> None:
        
        self.__codes : dict[int, str] = {
            
            200 : "OK",
            201 : "Created",
            204 : "No Content",
            
            400: "Bad Request",
            404: "Not Found",

            500: "Server Internal Error"
        }

    def code(self, code : int = 200) -> tuple[int, str]:

        code_text = self.__codes.get(code)

        if code_text is None:

            return (200, self.__codes.get(200))
        
        return (code,code_text)