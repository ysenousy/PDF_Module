from PyPDF2 import PdfFileReader, PdfFileWriter
from PyPDF2.generic import BooleanObject, NameObject, IndirectObject, TextStringObject, NumberObject
from collections import OrderedDict, MutableMapping
from json import JSONDecoder
from reportlab.pdfgen import canvas
from collections import defaultdict
import io, base64 
import json
import os
import shutil

# use .py files
# use class instead of functions
# use snake case for define variable except class name
# seperate code to lower functionl units
# use clinic_id as a new variable
# check if we can avoid file creation and use memory files
# get file using functions use clinic id and form name
# avoid nesting functions and classes

class MyPdfFileWriter(PdfFileWriter):

            def __init__(self):
                super().__init__()

            def updatePageFormCheckboxValues(self, page, fields):

                for j in range(0, len(page['/Annots'])):
                    writer_annot = page['/Annots'][j].getObject()
                    for field in fields:
                        writer_annot.update({NameObject("/Ff"): NumberObject(1)})


class PdfFormsGenerator:
    def __init__(self, clinic_id, form_name, json_object ) -> None:
        self.clinic_id = clinic_id
        self.form_name = form_name
        self.json_object = json_object
        
    def remove_special_characters(self, string):
        formated_string = ''.join(e for e in string if e.isalnum())
        return formated_string
    #def PdfFormsGenerator (formName, self.json_object): 
    def generate_pdf (self): 
        formName = self.remove_special_characters(self.form_name)
        #Some Json keys are duplicated to the following function to add counter in the end of key parameter if duplicated.
        FinalJsonObj = self.json_object

        # pdfsourcecopy = formName+'_'+FinalJsonObj['patient_name']['patient_fname']+'_'+FinalJsonObj['patient_name']['patient_lname']+'_Copy.pdf'
        pdfsourcecopy = formName+'_Copy.pdf'
        shutil.copyfile(formName+'.pdf', pdfsourcecopy)  

        pdf_template = PdfFileReader(open(pdfsourcecopy, "rb"))
        output = PdfFileWriter()  

        #Step2: Adding Images in PDF if the form have images
        #flag for pdf that have images
        flagImage = 0
        for key in FinalJsonObj:
            value = FinalJsonObj[key]
            if ('data:image/png;base64,' not in value):
        
                ParentalConsentImages = {"signature_parent":"10, 300, 150"}

                ReleseMedicalInfoImages = {"question2":"20, 180, 150"}

                FinancialBillingInfoImages = {"financially_responsible_signature":"28, 180, 480",
                                            "question5":"28, 180, 100",
                                            "Initials":"28, 180, 40"}

                HipaaReleseImages = {"parent_signature":"10, 120, 200"}

                PoliciesImages = {"question2":"30, 650, 50",
                "question16": "30, 623, 50",
                "question15": "30, 600, 50",
                "question14": "30, 568, 50",
                "question13": "30, 550, 50",
                "question12": "30, 522, 50",
                "question11": "30, 504, 50",
                "question10": "30, 486, 50",
                "question9": "30, 460, 50",
                "question8": "30, 445, 50",
                "question7": "30, 425, 50",
                "question6": "30, 400, 50",
                "question5": "30, 383, 50",
                "question4": "30, 360, 50",
                "question3": "30, 340, 50",
                "question20": "30, 322, 50",
                "parent_guardian_signature": "50, 248, 80",
                "financially_responsible_signature": "60, 160, 60",
                "Initials": "20, 25, 50"}

                def imageListReturn(formname):
                        argument={'ParentalConsent':ParentalConsentImages,
                                'ReleseMedicalInfo':ReleseMedicalInfoImages,
                                'FinancialPoliciesBilling':FinancialBillingInfoImages,
                                'HipaaRelese':HipaaReleseImages,
                                'Policies':PoliciesImages}
                        return argument.get(formname,"InvalidFormName")

                FormImageList = imageListReturn(formName)

                if (FormImageList != "InvalidFormName"):
                    for key in FinalJsonObj:
                        value = FinalJsonObj[key]
                        if ('data:image/png;base64,' in value):  
                            decodedImage = base64.b64decode(str(FinalJsonObj[''+key+'']).replace('data:image/png;base64,',''))
                            imageFile = open(''+key+".png", "wb")
                            imageFile.write(decodedImage)
                            imageFile.close()
                                
                            packet = io.BytesIO()
                            can = canvas.Canvas(packet)
                            
                            #Get Coordinates for Images          
                            if (key in FormImageList):
                                imageCoordinates  = FormImageList[key]
                                
                            imageCoordinateList = imageCoordinates.split(',')

                            can.drawImage(''+key+".png", int(imageCoordinateList[0]), int(imageCoordinateList[1]),
                                        width=int(imageCoordinateList[2]), preserveAspectRatio=True, mask='auto')

                            can.save()
                            packet.seek(0)

                            new_pdf = PdfFileReader(packet)
                            os.remove(''+key+".png")
                            for i in range(len(pdf_template.pages)):
                                page = pdf_template.getPage(i)
                                page.mergePage(new_pdf.getPage(i))
                            
                        #for page_number in range(page_count):
                    output.addPage(page)    
                    outputStream = open(formName+'_Edited.pdf', "wb")
                    output.write(outputStream)
                    outputStream.close()
                    flagImage = 1
                break
        # Go through all the input file pages

        # outputStream = open(formName+'_'+FinalJsonObj['patient_name']['patient_fname']+'_'+FinalJsonObj['patient_name']['patient_lname']+'_Edited.pdf', "wb")
        # output.write(outputStream)
        # outputStream.close()
        
        # if (flagImage == 1):
        #     origin = formName+'_'+FinalJsonObj['patient_name']['patient_fname']+'_'+FinalJsonObj['patient_name']['patient_lname']+'_Edited.pdf'
        # elif (flagImage == 0):
        #     origin = formName+'_'+FinalJsonObj['patient_name']['patient_fname']+'_'+FinalJsonObj['patient_name']['patient_lname']+'_Copy.pdf'   
        
        # destination = formName+'_'+FinalJsonObj['patient_name']['patient_fname']+'_'+FinalJsonObj['patient_name']['patient_lname']+'.pdf'


        if (flagImage == 1):
            origin = formName+'_Edited.pdf'
        elif (flagImage == 0):
            origin = formName+'_Copy.pdf'  
        
        destination = formName+'Filled.pdf'
        
        
        openfile = open(origin, "rb")
        

        def set_need_appearances_writer(writer):

            try:
                catalog = writer._root_object
                # get the AcroForm tree and add "/NeedAppearances attribute
                if "/AcroForm" not in catalog:
                    writer._root_object.update({
                        NameObject("/AcroForm"): IndirectObject(len(writer._objects), 0, writer)})

                need_appearances = NameObject("/NeedAppearances")
                writer._root_object["/AcroForm"][need_appearances] = BooleanObject(True)
                return writer
            except Exception as e:
                print('set_need_appearances_writer() catch : ', repr(e))
                return writer

        class PdfFileFiller(object):
                
            def __init__(self, infile):
                
                openfile = open(infile, "rb")
                self.pdf = PdfFileReader(openfile, strict=False)
                
                if "/AcroForm" in self.pdf.trailer["/Root"]:
                    self.pdf.trailer["/Root"]["/AcroForm"].update(
                    {NameObject("/NeedAppearances"): BooleanObject(True)})
                    

            # newvals and newchecks have keys have to be filled. '' is not accepted
            def update_form_values(self, outfile, newvals=None, newchecks=None):

                self.pdf2 = MyPdfFileWriter()
                trailer = self.pdf.trailer['/Root'].get('/AcroForm', None)
                if trailer:
                    self.pdf2._root_object.update({
                        NameObject('/AcroForm'): trailer})

                set_need_appearances_writer(self.pdf2)
                if "/AcroForm" in self.pdf2._root_object:
                    self.pdf2._root_object["/AcroForm"].update(
                    {NameObject("/NeedAppearances"): BooleanObject(True)})

                for i in range(self.pdf.getNumPages()):
                    self.pdf2.addPage(self.pdf.getPage(i))

                    self.pdf2.updatePageFormFieldValues(self.pdf2.getPage(i), newvals)
                    for j in range(0, len(self.pdf.getPage(i)['/Annots'])):
                        writer_annot = self.pdf.getPage(i)['/Annots'][j].getObject()
                        for field in newvals:
                            writer_annot.update({NameObject("/Ff"): NumberObject(1)})

                    self.pdf2.updatePageFormCheckboxValues(self.pdf2.getPage(i), newchecks)

                with open(outfile, 'wb') as out:
                    self.pdf2.write(out)
                    out.close()
            
        
        
        
        newvals = self.flatten(FinalJsonObj)

        newchecks = {} # A dict with all checkbox values that need to be changed

        c = PdfFileFiller(origin)
        c.update_form_values(outfile=destination, newvals=newvals, newchecks=newchecks)

        with open(destination, "rb") as pdf1_file:
            encoded_string = base64.b64encode(pdf1_file.read())
            pdf1_file.close()

        if (flagImage == 1):
            # os.remove(pdfsourcecopy)
            # os.remove(origin)    
            # os.remove(destination)
            os.remove(destination)
            os.remove(pdfsourcecopy)
            os.remove(origin)   
        elif (flagImage == 0):
            os.remove(origin)    
            os.remove(destination)

        return  encoded_string   
    
    def flatten(self, d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, list):
                for i in v:
                    # return get_keys(i, curr_key + [k])
                    items.extend(self.flatten(i, new_key, sep=sep).items())
            elif isinstance(v, MutableMapping):
                items.extend(self.flatten(v, new_key, sep=sep).items())
            # if isinstance(v, MutableMapping):
            #     items.extend(flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
