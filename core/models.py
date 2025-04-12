from django.db import models
from .utils import FKWS
from django.conf import settings
from datetime import datetime

# Create your models here.
class Invoice(models.Model):
    """Modelo para las facturas"""
    #upload = models.ForeignKey('Upload', on_delete=models.CASCADE)
    invoice_type = models.CharField(max_length=1, default="I", null=True)
    fecha_emision = models.DateTimeField(null=True)
    fecha_timbrado = models.DateTimeField(null=True)
    forma_pago = models.CharField(max_length=2, null=True)
    uuid = models.CharField(max_length=40)
    taxpayer_id = models.CharField(max_length=15)
    rtaxpayer_id = models.CharField(max_length=15)
    total = models.CharField(max_length=200)
    codigo_status = models.CharField(max_length=100,blank=True, null=True) #  'S - Comprobante obtenido satisfactoriamente.'
    es_cancelable = models.CharField(max_length=50, blank=True,null=True) #  'Cancelable sin aceptación'
    estado = models.CharField(max_length=20,blank=True, null=True) # 'Vigente'
    estatus_cancelacion = models.CharField(max_length=50,blank=True, null=True) #  ''
    validacion_efos = models.CharField(max_length=10,blank=True, null=True)# '200'
    ultima_verificacion = models.DateField(null=True,blank=True)
    folio_sustitucion = models.CharField(max_length=40, null=True)
    related_cfdi = models.JSONField(default=dict)
    motivo = models.CharField(max_length=2, null=True)# '200'
    created  = models.DateTimeField(auto_now_add=True)
    fecha_pago = models.DateField(null=True)


    class Meta:
        # index_together = (
        #     ('uuid', 'upload')
        # )
        ordering = ['-created']

    def __str__(self):
        return '''{} - {} - {} - {}'''.format(
            self.uuid,
            self.taxpayer_id,
            self.rtaxpayer_id,
            self.total
        )

    def get_rep_impresa(self):
        return f'?re={self.taxpayer_id}&rr={self.rtaxpayer_id}&tt={self.total}&id={self.uuid}'

    def get_status(self):
        # breakpoint()
        fkws = FKWS(settings.FK_USERNAME, settings.FK_PASSWORD, True)
        representacion_impresa = self.get_rep_impresa()
        # if settings.DEBUG is True:
        #     response = fkws.consulta_qr(self.taxpayer_id, self.rtaxpayer_id, self.uuid, self.total, True)
        #     print(response)
        # else:
        response = fkws.consulta_qr_sat(representacion_impresa)
        print(
                "{Rfc} - {UUID} - {CodigoEstatus} - {EsCancelable} - {Estado} - {EstatusCancelacion} - {ValidacionEFOS}".format(
                Rfc=self.taxpayer_id, UUID=self.uuid, **dict(response.__values__)
                )
            )
        # if response['EstatusCancelacion'] and 'rechaz' in response['EstatusCancelacion'].lower():
        #     raise Exception('Detente')
        try:
            print(response['sat'])
            self.codigo_status = response['sat']['CodigoEstatus']
            self.es_cancelable = response['sat']['EsCancelable']
            self.estado = response['sat']['Estado']
            self.estatus_cancelacion = response['sat']['EstatusCancelacion']
            self.validacion_efos = response['sat']['ValidacionEFOS']
            self.ultima_verificacion = datetime.now()
            self.save()
        except Exception as e:    
            print(f"Ocurrio un error en get_status: {e}")
        return response

    # def cancel(self, force=False):
    #     fkws = FKWS(username=self.upload.business.username_fk, password=self.upload.business.password_fk)
    #     if force or self.estado == 'Vigente' and (
    #         'Cancelable con' in self.es_cancelable or
    #         'Cancelable sin' in self.es_cancelable):
    #         response = fkws.cancel(self.taxpayer_id, self.uuid, motivo=self.motivo, folio_sustitucion=self.folio_sustitucion, serial=self.upload.business.serial)
    #         try:
    #             response.Folios.Folio[0].EstatusUUID
    #             cancel_obj = Cancel.objects.create(invoice=self)
    #             cancel_obj.estatus_uuid = response.Folios.Folio[0].EstatusUUID
    #             cancel_obj.acuse = response.Acuse
    #             cancel_obj.fecha = response.Fecha
    #             cancel_obj.save()
    #             print("{Rfc} - {UUID} - {EstatusUUID} - {Fecha}".format(
    #                 Rfc=self.taxpayer_id, UUID=self.uuid, EstatusUUID=cancel_obj.estatus_uuid, Fecha=cancel_obj.fecha
    #             ))
    #         except Exception as e:
    #             print(f'Ocurrio error en cancel =>{e}')    
    #         save_log(response)
    #         return response

    # def async_cancel(self, queue_name='celery'):
    #     from .tasks import cancel
    #     cancel.apply_async([self.id,], queue=queue_name)

    # def get_async_status(self, queue_name='celery'):
    #     from .tasks import verify_status
    #     verify_status.apply_async([self.id], queue=queue_name)

    # def get_real_total(self):
    #     fkws = FKWS(username=self.upload.business.username_fk, password=self.upload.business.password_fk)
    #     xml_string = fkws.get_xml(self.uuid, self.taxpayer_id)
    #     print(xml_string)
    #     xml_etree = etree.fromstring(xml_string)
    #     self.invoice_type = xml_etree.get("TipoDeComprobante")
    #     self.save()
    #     if True or self.total != xml_etree.get('Total'):
    #         print("{Rfc} - {UUID} - {Total} - {NewTotal}".format(
    #             Rfc=self.taxpayer_id, UUID=self.uuid, Total=self.total, NewTotal=xml_etree.get('Total')
    #         ))
    #         self.fecha_emision = xml_etree.get("Fecha")
    #         self.forma_pago = xml_etree.get("FormaPago")
    #         self.fecha_timbrado = xml_etree.xpath('string(.//tfd:TimbreFiscalDigital/@FechaTimbrado)', namespaces={"tfd": "http://www.sat.gob.mx/TimbreFiscalDigital"})
    #         self.taxpayer_id = xml_etree.xpath('string(.//cfdi:Emisor/@Rfc)', namespaces=xml_etree.nsmap)
    #         self.rtaxpayer_id = xml_etree.xpath('string(.//cfdi:Receptor/@Rfc)', namespaces=xml_etree.nsmap)
    #         self.total = xml_etree.get('Total')
    #         relacionados = defaultdict(list)
    #         for cfdirelacionados in xml_etree.xpath('.//cfdi:CfdiRelacionados', namespaces=xml_etree.nsmap):
    #             relacionados.setdefault(cfdirelacionados.get("TipoRelacion"), []).append(cfdirelacionados.xpath('./cfdi:CfdiRelacionado/@UUID', namespaces=xml_etree.nsmap))
    #         self.related_cfdi = relacionados
    #         self.save()
    #         self.get_async_status()
    #     else:
    #         self.get_async_status()

    # def get_async_total(self, queue_name='celery'):
    #     from .tasks import update_total
    #     update_total.apply_async([self.id], queue=queue_name)

    # def get_async_related(self, queue_name='celery'):
    #     from .tasks import get_related
    #     get_related.apply_async([self.id], queue=queue_name)

    # def get_related(self):
    #     fkws = FKWS(username=self.upload.business.username_fk, password=self.upload.business.password_fk)
    #     relacionados = fkws.get_related(self.uuid, self.taxpayer_id)
    #     if relacionados.Padres:
    #         for padre in relacionados.Padres.Padre:
    #             padre_obj, created = RRelatedInvoice.objects.get_or_create(
    #                 upload=self.upload,
    #                 invoice=self,
    #                 uuid=padre.uuid
    #             )
    #             padre_obj.taxpayer_id = padre.emisor
    #             padre_obj.rtaxpayer_id = padre.receptor
    #             padre_obj.save()
    #             related_invoice, created = RelatedInvoice.objects.get_or_create(
    #                 invoice = self,
    #                 padre = padre_obj
    #             )
    #             related_invoice.save()
    #             related_invoice.padre.get_real_total()
    #             print("{Rfc} - {UUID} - Padre: {Padre}".format(
    #                 Rfc=self.taxpayer_id, UUID=self.uuid, Padre=padre_obj.uuid
    #             ))
    #     if relacionados.Hijos:
    #         for hijo in relacionados.Hijos.Hijo:
    #             hijo_obj, created = RRelatedInvoice.objects.get_or_create(
    #                 upload=self.upload,
    #                 invoice=self,
    #                 uuid=hijo.uuid
    #             )
    #             hijo_obj.taxpayer_id = hijo.emisor
    #             hijo_obj.rtaxpayer_id = hijo.receptor
    #             hijo_obj.save()
    #             related_invoice, created = RelatedInvoice.objects.get_or_create(
    #                 invoice = self,
    #                 hijo = hijo_obj
    #             )
    #             related_invoice.hijo.get_real_total()
    #             related_invoice.save()
    #             print("{Rfc} - {UUID} - Hijo: {Hijo}".format(
    #                 Rfc=self.taxpayer_id, UUID=self.uuid, Hijo=hijo_obj.uuid
    #             ))
        # if relacionados.error and "2001 - No Existen cfdi relacionados" in relacionados.error:
        #     self.cancel(True)

    # def get_report_value(self, new_line=False):
    #     from django.db.models.functions import Upper
    #     total_cancel = 4
    #     # set_trace()
    #     try:
    #         total_cancel = Invoice.objects.get(uuid=self.uuid.upper()).cancel_set.count()
    #     except:
    #         try:
    #             total_cancel = Invoice.objects.get(uuid=self.uuid.upper()).cancel_set.count()
    #         except:
    #             total_cancel = '?'
    #             print(self.uuid)
    #     return '''{}, {}, {}, {}, {}, {}, {},{}{}'''.format(
    #         self.uuid.strip(),
    #         self.invoice_type,
    #         self.taxpayer_id.strip(),
    #         self.rtaxpayer_id.strip(),
    #         self.total.strip(),
    #         self.es_cancelable or '',
    #         self.estado or '',
    #         self.estatus_cancelacion or '',
    #         total_cancel,
    #         ',' if not new_line else '\n',
    #     )
    
    # def get_data_json(self):
    #     """function to get upload data json"""
    #     result =  {
    #         "id":  self.id,
    #         "rtaxpayerid": self.rtaxpayer_id,
    #         "uuid": self.uuid,
    #         "total": self.total,
    #         "estatus": self.estado,
    #         "es_cancelable": self.es_cancelable,
    #         "actions": ""
    #     }
       
    #     return result
