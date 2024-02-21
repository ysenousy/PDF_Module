"""A dummy docstring."""
import io
import base64
import json
from collections import OrderedDict
from json import JSONDecoder
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from PyPDF2.generic import BooleanObject, NameObject, IndirectObject, NumberObject
from PyPDF2 import PdfFileReader, PdfFileWriter


class PdfFormsGenerator:
    """A dummy docstring."""

    def get_base_64_pdf(self, clinic_id, form_name, json_object):
        """A dummy docstring."""
        json_handler = JsonHandler()
        pdf_template_handler = PdfTemplatesHandler()
        json_var = json_handler.get_final_json(json_object)
        pdftemplate = pdf_template_handler.pdf_templates_stream(
            clinic_id, form_name)
        flagimage = json_handler.check_json_has_image(json_var)

        if flagimage is True:
            addimageonpdf = AddImagesOnPDF()
            pdf_template_handler = PdfTemplatesHandler()
            fillingpdf = PdfFileFiller(
                addimageonpdf.adding_images(json_var, clinic_id, form_name))
            finalpdf = pdf_template_handler.convert_bytes_base64(
                fillingpdf.update_form_values(newvals=json_var))
        else:
            fillingpdf = PdfFileFiller(pdftemplate)
            finalpdf = pdf_template_handler.convert_bytes_base64(
                fillingpdf.update_form_values(newvals=json_var))

        return finalpdf

    def get_bytes_pdf(self, clinic_id, form_name, json_object):
        """A dummy docstring."""
        json_handler = JsonHandler()
        json_var = json_handler.get_final_json(json_object)
        pdf_template_handler = PdfTemplatesHandler()
        pdftemplate = pdf_template_handler.pdf_templates_stream(
            clinic_id, form_name)
        flagimage = json_handler.check_json_has_image(json_var)

        if flagimage is True:
            addimageonpdf = AddImagesOnPDF()
            fillingpdf = PdfFileFiller(
                addimageonpdf.adding_images(json_var, clinic_id, form_name))
            finalpdf = fillingpdf.update_form_values(newvals=json_var)
        else:
            fillingpdf = PdfFileFiller(pdftemplate)
            finalpdf = fillingpdf.update_form_values(newvals=json_var)

        return finalpdf

# Class JsonHandler to Clean JsonObject and Convert It to Basic Dictionary


class JsonHandler:
    """A dummy docstring."""

    def replace_json(self, json_object):
        """A dummy docstring."""
        with open(json_object, 'r', encoding="utf-8") as file_open:
            json_data = json.load(file_open)
        json_data_replaced = (str(json_data).replace(
            "'", '"').replace('/[', '').replace('/]', ''))
        return json_data_replaced

    # Replace Single Quoats with Double and Remove Brackets from the JsonObject
    def get_keys(self, data_list, curr_key=None):
        """A dummy docstring."""
        if curr_key is None:
            curr_key = []
        for k, variable_list in data_list.items():
            if isinstance(variable_list, dict):
                yield from self.get_keys(variable_list, curr_key + [k])
            elif isinstance(variable_list, list):
                for i in variable_list:
                    yield from self.get_keys(i, curr_key + [k])
            else:
                yield '_'.join(curr_key + [k] + [':'+variable_list]).replace("_:", '":"')

    def make_unique(self, key, dct):
        """A dummy docstring."""
        counter = 0
        unique_key = key

        while unique_key in dct:
            counter += 1
            unique_key = f'{key}_{counter}'
        return unique_key

    def parse_object_pairs(self, pairs):
        """A dummy docstring."""
        dct = OrderedDict()
        for key, value in pairs:
            if key in dct:
                key = self.make_unique(key, dct)
            dct[key] = value
        return dct

    def get_final_json(self, json_data_replaced):
        """A dummy docstring."""
        json_response = (str(json.dumps([*self.get_keys(json.loads(self.replace_json(
            json_data_replaced)))])).replace('\\', '').replace('[', '{').replace(']', '}'))
        decoder = JSONDecoder(object_pairs_hook=self.parse_object_pairs)
        final_json_obj = decoder.decode(str(json_response))
        return final_json_obj

    def check_json_has_image(self, json_object):
        """A dummy docstring."""
        flag = False
        for key in json_object:
            value = json_object[key]
            if 'data:image/png;base64,' in value:
                flag = True
                return flag


class PdfFileFiller(object):
    """A dummy docstring."""

    def __init__(self, in_file):

        self.pdf = PdfFileReader(in_file, strict=False)
        self.pdf2 = MyPdfFileWriter()
        if "/AcroForm" in self.pdf.trailer["/Root"]:
            self.pdf.trailer["/Root"]["/AcroForm"].update(
                {NameObject("/NeedAppearances"): BooleanObject(True)})

    def set_need_appearances_writer(self, writer):
        """A dummy docstring."""
        try:
            catalog = writer._root_object
            # get the AcroForm tree and add "/NeedAppearances attribute
            if "/AcroForm" not in catalog:
                writer._root_object.update({
                    NameObject("/AcroForm"): IndirectObject(len(writer._objects), 0, writer)})

            need_appearances = NameObject("/NeedAppearances")
            writer._root_object["/AcroForm"][need_appearances] = BooleanObject(
                True)
            return writer
        except ValueError:
            print('set_need_appearances_writer() catch : ', repr())
            return writer

    # newvals and newchecks have keys have to be filled. '' is not accepted
    def update_form_values(self, newvals=None):
        """A dummy docstring."""
        newchecks = {}
        self.pdf2 = MyPdfFileWriter()
        trailer = self.pdf.trailer['/Root'].get('/AcroForm', None)
        if trailer:
            self.pdf2._root_object.update({
                NameObject('/AcroForm'): trailer})

        self.set_need_appearances_writer(self.pdf2)
        if "/AcroForm" in self.pdf2._root_object:
            self.pdf2._root_object["/AcroForm"].update(
                {NameObject("/NeedAppearances"): BooleanObject(True)})

        for i in range(self.pdf.getNumPages()):
            self.pdf2.addPage(self.pdf.getPage(i))

            self.pdf2.updatePageFormFieldValues(self.pdf2.getPage(i), newvals)
            for j in range(0, len(self.pdf.getPage(i)['/Annots'])):
                writer_annot = self.pdf.getPage(i)['/Annots'][j].getObject()
                for _ in newvals:
                    writer_annot.update({NameObject("/Ff"): NumberObject(1)})

            self.pdf2.update_page_form_checkbox_values(
                self.pdf2.getPage(i), newchecks)

        final_pdf = io.BytesIO()
        self.pdf2.write(final_pdf)
        return final_pdf


class MyPdfFileWriter(PdfFileWriter):
    """A dummy docstring."""

    def __init__(self):
        super().__init__()

    def update_page_form_checkbox_values(self, page, fields):
        """A dummy docstring."""
        for j in range(0, len(page['/Annots'])):
            writer_annot = page['/Annots'][j].getObject()
            for _ in fields:
                writer_annot.update({NameObject("/Ff"): NumberObject(1)})


class PdfTemplatesHandler:
    """A dummy docstring."""

    def pdf_templates_reader(self, clinic_id, form_name):
        """A dummy docstring."""
        with open('clinic_'+clinic_id+'_pdf_temp'+'/'+form_name+'.pdf', "rb") as f_h:
            bytes_stream = BytesIO(f_h.read())
        # Read from bytes_stream
        pdf_template = PdfFileReader(bytes_stream)
        return pdf_template

    def pdf_templates_stream(self, clinic_id, form_name):
        """A dummy docstring."""
        with open('clinic_'+clinic_id+'_pdf_temp'+'/'+form_name+'.pdf', "rb") as f_h:
            bytes_stream = BytesIO(f_h.read())
        # Read from bytes_stream
        # pdf_template = PdfFileReader(bytes_stream)
        return bytes_stream

    def convert_bytes_base64(self, stream):
        """A dummy docstring."""
        return base64.b64encode(stream.getvalue())


class AddImagesOnPDF:
    """A dummy docstring."""

    def get_image_coordinates(self, clinic_id, form_name):
        """A dummy docstring."""
        clinic_id = {'ParentalConsent': {"signature_parent": "10, 300, 150"},
                     'ReleseMedicalInfo': {"question2": "20, 180, 150"},
                     'FinancialBillingInfo': {"financially_responsible_signature": "28, 180, 480",
                                              "question5": "28, 180, 100",
                                              "Initials": "28, 180, 40"},
                     'HipaaRelese': {"parent_signature": "10, 120, 200"},
                     'Policies': {"question2": "30, 650, 50",
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
                                  "Initials": "20, 25, 50"}}
        return clinic_id.get(form_name, "InvalidFormName")

    def get_x_y_size(self, image_name, form_image_list):
        """A dummy docstring."""
        if image_name in form_image_list:
            image_coordinates = form_image_list[image_name]
            image_coordinate_list = image_coordinates.split(',')
        return image_coordinate_list

    def adding_images(self, json_object, clinic_id, form_name):
        """A dummy docstring."""
        output = PdfFileWriter()
        json_handler = JsonHandler()
        pdf_template_handler = PdfTemplatesHandler()
        add_image_on_pdf = AddImagesOnPDF()
        pdf_template = pdf_template_handler.pdf_templates_reader(
            clinic_id, form_name)
        form_image_list = self.get_image_coordinates(clinic_id, form_name)
        has_image = json_handler.check_json_has_image(json_object)
        if ((has_image is True) and (form_image_list != "InvalidFormName")):
            for key in json_object:
                value = json_object[key]
                if 'data:image/png;base64,' in value:
                    decoded_image = base64.b64decode(
                        str(json_object[''+key+'']).replace('data:image/png;base64,', ''))
                    tempfile = BytesIO()
                    tempfile.write(decoded_image)
                    tempfile.seek(0)
                    tempimage = Image.open(tempfile)
                    finalimage = ImageReader(tempimage)
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet)

                    image_coordinate_list = add_image_on_pdf.get_x_y_size(
                        key, form_image_list)
                    can.drawImage(finalimage, int(image_coordinate_list[0]),
                                  int(image_coordinate_list[1]),
                                  width=int(image_coordinate_list[2]),
                                  preserveAspectRatio=True, mask='auto')

                    can.save()
                    packet.seek(0)

                    new_pdf = PdfFileReader(packet)
                    tempimage.close()

                    for i in range(len(pdf_template.pages)):
                        page = pdf_template.getPage(i)
                        page.mergePage(new_pdf.getPage(i))

        output.addPage(page)
        pdfimagesadded = io.BytesIO()
        output.write(pdfimagesadded)
        return pdfimagesadded


# Consuming PDF Generator Class
PdfGen = PdfFormsGenerator()

base64pdf = PdfGen.get_base_64_pdf(
    '1', 'Policies', 'clinic_1_pdf_temp/Policies.json')
bytespdf = PdfGen.get_bytes_pdf(
    '1', 'Policies', 'clinic_1_pdf_temp/Policies.json')

print(base64pdf)
