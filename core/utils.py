import re
import logging
# from pdb import set_trace
# from lxml import etree
from zeep import Client
from zeep.plugins import HistoryPlugin
from django.core.cache import cache
from django.utils import timezone
from sequences import get_next_value


from django.conf import settings

history = HistoryPlugin()

cancel_url = settings.FK_WSDL_CANCEL
client_cancel = Client(wsdl=cancel_url, plugins=[history])

consulta_qr = settings.CONSULTA_QR_WSDL
client_consultaqr = Client(wsdl=settings.FK_WSDL_CANCEL, plugins=[history])

utilities_url = settings.FK_UTILITIES_URL

client_utilities = Client(wsdl=utilities_url, plugins=[history])

class FKWS(object):

    def __init__(self, username=None, password=None, verbose=False):
        self.verbose = verbose
        self.username = username
        self.password = password

    def stamp(self, taxpayer_id, xml_string, basic_info):
        response = None
        stamp_url = settings.FK_WSDL_STAMP

        try:
            if isinstance(xml_string, str):
                xml_string = xml_string.encode()
            xml_string = xml_string.replace(b'Antig&#252;edad', bytes(bytearray('Antigüedad', encoding='UTF-8')))

            history = HistoryPlugin()
            client = Client(wsdl=stamp_url, plugins=[history])
            auth = client.get_type("ns1:Authentication")(user=self.username, password=self.password)
            infobasica = client.get_type("ns1:InfoBasic")(refID=basic_info.get("refID"), rfcEmisor=taxpayer_id, folio=basic_info.get("folio"), serie=basic_info.get("serie"))
            document = client.get_type("ns1:Document")(Archivo=xml_string)
            response = client.service.generaCFDi(infobasica, document, auth)
            if self.verbose:
                logging.info(response)
        except Exception as e:
            logging.error(f"FKWS[stamp] exception => {str(e)}")

        return response

    def cancel(self, taxpayer_id, uuid, folio_sustitucion="", motivo="", serial=""):
        response = None
        try:
            client_cancel.set_ns_prefix('ns0', 'apps.services.soap.core.views')
            uuids_factory = client_cancel.get_type('ns0:UUID')
            uuids_obj = uuids_factory(uuid, folio_sustitucion, motivo)
            print(uuids_obj)
            uuids_array_factory = client_cancel.get_type('ns0:UUIDArray')
            uuids_array_obj = uuids_array_factory([uuids_obj])
            response = client_cancel.service.sign_cancel(
                uuids_array_obj,
                self.username,
                self.password,
                taxpayer_id,
                serial,
                store_pending=False
            )          
            print(response)  
        except Exception as e:
            logging.error(f"FKWS[cancel] exception => {str(e)}")

        return response

    def cancel_liverpool(self, taxpayer_id, uuid, basic_info):
        response = None
        try:

            auth = client_cancel.get_type("ns1:Authentication")(user=self.username, password=self.password)
            uuid__ = client_cancel.get_type("ns1:UUID")(UUID=uuid, FolioSustitucion='', Motivo='03')
            uuids = client_cancel.get_type("ns1:UUIDArray")([uuid__])
            response = client_cancel.service.cancelaCFDi(uuids, taxpayer_id, auth)
        except Exception as e:
            logging.error(f"FKWS[cancel] exception => {str(e)}")

        return response

    def inc(self, taxpayer_id, verbose=False):
        success = False
        result = {
            'taxpayer_id': taxpayer_id,
            'exists': False,
            'name': None,
            'zipcode': None,
        }
        try:
            history = HistoryPlugin()
            client = Client(wsdl=settings.FK_WSDL_INC, plugins=[history])

            taxpayer_id_regex = r"[A-Z,Ñ,&]{3,4}[0-9]{2}[0-1][0-9][0-3][0-9][A-Z,0-9][A-Z,0-9][0-9,A-Z]?"
            if re.match(taxpayer_id_regex, taxpayer_id):
                response = client.service.check(taxpayer_id, self.username, self.password)
                if verbose:
                    print('FKWS inc', taxpayer_id, response)
                if response.exists:
                    result.update({'exists': True})
                if response.nombre:
                    result.update({'name': response.nombre.strip().upper()})
                if response.cp:
                    result.update({'zipcode': response.cp.strip()})
                success = True
        except Exception as e:
            print(f"FKWS[inc] exception => {str(e)}")
            logging.error(f"FKWS[inc] exception => {str(e)}")

        return success, result

    def consulta_qr(self, taxpayer_id="", rtaxpayer_id="", uuid="", total="", verbose=True):

        response = None

        try:
            response =  client_consultaqr.service.get_sat_status(
                self.username, self.password, taxpayer_id, rtaxpayer_id, uuid, total
            )
            if verbose:
                print(response)
        except Exception as e:
            logging.error(f"FKWS[consulta_qr] exception -> {e}")
        return response

    @staticmethod
    def consulta_qr_sat(expresion_impresa, verbose=True):

        response = None
        consulta_qr_url = settings.CONSULTA_QR_WSDL
        try:
            history = HistoryPlugin()
            # print(expresion_impresa)
            response = client_consultaqr.service.Consulta(expresion_impresa)
            print(response)
        except Exception as e:
            logging.error(f"FKWS[consulta_qr] exception -> {e}")
        return response

    def get_xml(self, uuid, taxpayer_id, invoice_type='I'):
        response = None
        client = None
        history = HistoryPlugin()
        response = client_utilities.service.get_xml(self.username,self.password, uuid, taxpayer_id, invoice_type)
        xml = response.xml
        try:
            xml = xml.encode('UTF-8')
        except:
            pass
        return xml

    def get_related(self, uuid, taxpayer_id):
        response = None
        related_url = settings.FK_WSDL_STAMP

        try:
            history = HistoryPlugin()
            response = client_cancel.service.get_related(
                username=self.username,
                password=self.password,
                uuid=uuid,
                taxpayer_id=taxpayer_id,
                cer=settings.CER_PEM,
                key=settings.KEY_PEM,
            )
            print(response)
        except Exception as e:
            logging.error(f"FKWS[cancel] exception => {str(e)}")

        return response


    def get_related_liverpool(self, uuid, taxpayer_id):
        response = None
        related_url = settings.FK_WSDL_STAMP

        try:
            history = HistoryPlugin()
            client = Client(wsdl=related_url, plugins=[history])

            auth = client.get_type("ns1:Authentication")(user=self.username, password=self.password)
            # uuid__ = client.get_type("ns1:UUID")(UUID=uuid, FolioSustitucion='', Motivo='02')
            # uuids = client.get_type("ns1:UUIDArray")([uuid__])
            response = client.service.obtenerCFDIRelacionados(Auth=auth, uuid=uuid, taxpayer_id=taxpayer_id)
            print(response)
        except Exception as e:
            logging.error(f"FKWS[cancel] exception => {str(e)}")

        return response

def save_log(message):
    """Save log in memcache"""
    key = get_next_value('logs')
    print(message)
    cache.set(key,
              {"time": timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
               "message": str(message)}, timeout=86400)
    add_key_to_indice(key)

def add_key_to_indice(key):
    """Añade una clave al índice maestro."""
    claves = cache.get("cache_keys") or set()
    claves.add(key)
    cache.set("cache_keys", claves)

def get_keys():
    """Obtiene todas las claves rastreadas."""
    return cache.get("cache_keys") or set()

def get_all_info():
    """Obtiene la información completa de todas las claves rastreadas."""
    claves = get_keys()
    data = []
    for key in claves:
        data.append(cache.get(key))
    if data:
        data = data[::-1]
    return data
