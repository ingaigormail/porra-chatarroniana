# utils/banderas.py
import flag

# Diccionario de códigos de países
CODIGOS_PAISES = {
    "Espana": "ES", "Argentina": "AR", "Brasil": "BR", "Francia": "FR",
    "Alemania": "DE", "Portugal": "PT", "Inglaterra": "GB", "Reino Unido": "GB",
    "Mexico": "MX", "Canada": "CA", "Estados Unidos": "US", "USA": "US",
    "Paises Bajos": "NL", "Países Bajos": "NL", "Holanda": "NL",
    "Uruguay": "UY", "Colombia": "CO", "Ecuador": "EC",
    "Croacia": "HR", "Marruecos": "MA", "Japon": "JP", "Japón": "JP",
    "Belgica": "BE", "Bélgica": "BE", "Suiza": "CH",
    "Australia": "AU", "Corea del Sur": "KR", "Senegal": "SN",
    "Noruega": "NO", "Panama": "PA", "Paraguay": "PY",
    "Ghana": "GH", "Costa de Marfil": "CI", "Egipto": "EG",
    "Escocia": "GB", "Turquia": "TR", "Turquía": "TR",
    "Suecia": "SE", "Nueva Zelanda": "NZ", "Catar": "QA",
    "Arabia Saudita": "SA", "Irak": "IQ", "Jordania": "JO",
    "Austria": "AT", "Argelia": "DZ", "Tunez": "TN",
    "Sudafrica": "ZA", "Sudáfrica": "ZA", "Republica Checa": "CZ",
    "Cabo Verde": "CV", "Curazao": "CW", "Haiti": "HT",
    "Uzbekistan": "UZ", "Republica del Congo": "CG",
    "Bosnia y Herzegovina": "BA", "Iran": "IR",
    "Peru": "PE", "Chile": "CL", "Italia": "IT",
    "PaisesBajos": "NL"
}

def con_bandera(pais):
    """Devuelve la bandera de un país o ⚽ si no se encuentra"""
    p_limpio = str(pais).strip()
    if p_limpio == "" or p_limpio.lower() == "nan":
        return "🏳️"
    codigo = CODIGOS_PAISES.get(p_limpio, None)
    if codigo:
        try:
            return flag.flag(codigo)
        except:
            return "⚽"
    return "⚽"