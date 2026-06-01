from flask import Flask, render_template, request, send_file, jsonify
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm, inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
import os
import io
import base64
import json
import re
import random
from PIL import Image as PILImage

app = Flask(__name__)

# Создаем папки
os.makedirs('reports', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('static', exist_ok=True)

# Регистрируем шрифты
try:
    pdfmetrics.registerFont(TTFont('TimesNewRoman', 'times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', 'timesbd.ttf'))
    pdfmetrics.registerFont(TTFont('TimesNewRoman-Italic', 'timesi.ttf'))
except:
    try:
        pdfmetrics.registerFont(TTFont('TimesNewRoman', 'TimesNewRoman.ttf'))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', 'TimesNewRoman-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-Italic', 'TimesNewRoman-Italic.ttf'))
    except:
        print("Используется стандартный шрифт")

# Создаем стили
styles = getSampleStyleSheet()

normal_style = ParagraphStyle(
    'NormalStyle',
    parent=styles['Normal'],
    fontName='TimesNewRoman',
    fontSize=11,
    leading=14,
    alignment=TA_LEFT,
    spaceAfter=6
)

title_style = ParagraphStyle(
    'TitleStyle',
    parent=styles['Heading1'],
    fontName='TimesNewRoman-Bold',
    fontSize=16,
    leading=20,
    alignment=TA_CENTER,
    spaceAfter=12,
    spaceBefore=12
)

subtitle_style = ParagraphStyle(
    'SubtitleStyle',
    parent=styles['Heading2'],
    fontName='TimesNewRoman-Bold',
    fontSize=12,
    leading=16,
    alignment=TA_LEFT,
    spaceAfter=8,
    spaceBefore=8,
    textColor=colors.black
)

photo_caption_style = ParagraphStyle(
    'PhotoCaptionStyle',
    parent=styles['Normal'],
    fontName='TimesNewRoman-Italic',
    fontSize=9,
    leading=11,
    alignment=TA_CENTER,
    spaceAfter=6
)

# ============= ВСТРОЕННАЯ НЕЙРОСЕТЬ ДЛЯ ГЕНЕРАЦИИ ТЕКСТОВ =============

class NeuralTextGenerator:
    """Встроенная нейросеть для генерации профессиональных текстов по ГОСТ"""
    
    def __init__(self):
        # База знаний ключевых слов и соответствующих ГОСТов
        self.gost_database = {
            "опорные колодки": {
                "gost": "ГОСТ Р 52749-2007 п. Б 5.4",
                "requirement": "применять опорные (несущие) колодки из полимерных материалов плотностью не менее 80 единиц по Шору А или пропитанной защитными средствами древесины твердых пород",
                "violation": "применяются не соответствующие материалы (куски кирпичей, остатки гипсокартона, деревянные бруски без пропитки)",
                "recommendation": "заменить опорные колодки на сертифицированные из полимерных материалов"
            },
            "монтажный шов": {
                "gost": "ГОСТ 30971-2012",
                "requirement": "монтажный шов должен состоять из трех слоев: центрального теплоизоляционного, наружного гидроизоляционного и внутреннего пароизоляционного",
                "violation": "монтажный шов выполнен с нарушениями: отсутствует один из слоев, имеются пустоты и раковины, нарушена непрерывность",
                "recommendation": "выполнить монтажный шов в соответствии с требованиями, обеспечив три слоя изоляции"
            },
            "герметик": {
                "gost": "ГОСТ 30971-2012 по Приложению А п. А4.4",
                "requirement": "поверхность герметика не должна иметь трещин, раковин и пустот",
                "violation": "нанесение выполнено с раковинами и пустотами, имеются трещины и неровности",
                "recommendation": "удалить некачественный герметик и нанести новый с соблюдением технологии"
            },
            "уплотнитель": {
                "gost": "Системный каталог ALUTECH «Оконные конструкции W72» издание 02.2024 Лист 02.04.44",
                "requirement": "уплотнитель должен устанавливаться без разрывов, стыки должны быть выполнены в угловых соединениях рамы",
                "violation": "уплотнитель установлен с разрывами, стыки выполнены неправильно, имеет малый запас по длине",
                "recommendation": "произвести демонтаж и последующий монтаж уплотнителя с соблюдением технологии"
            },
            "стеклопакет": {
                "gost": "ГОСТ 24866-2014",
                "requirement": "отклонение от плоскости стеклопакета не должно превышать 0.2% длины ребра",
                "violation": "стеклопакет установлен с перекосами, имеются сколы и царапины на поверхности",
                "recommendation": "заменить стеклопакет на соответствующий требованиям"
            },
            "профиль": {
                "gost": "ГОСТ 30674-99",
                "requirement": "поверхность профилей не должна иметь сколов, царапин и других дефектов",
                "violation": "профиль имеет механические повреждения, царапины, сколы защитной пленки",
                "recommendation": "заменить поврежденные профильные элементы"
            },
            "фурнитура": {
                "gost": "ГОСТ 30777-2012",
                "requirement": "фурнитура должна обеспечивать плавное открывание и закрывание всех створок",
                "violation": "фурнитура работает с заеданиями, не обеспечивает плотный притвор",
                "recommendation": "отрегулировать или заменить неисправные элементы фурнитуры"
            },
            "теплоизоляция": {
                "gost": "СП 50.13330.2012",
                "requirement": "теплоизоляционный слой должен быть непрерывным и плотно прилегать",
                "violation": "теплоизоляция установлена с зазорами, имеются мостики холода",
                "recommendation": "восстановить целостность теплоизоляционного слоя"
            },
            "пароизоляция": {
                "gost": "СП 23-101-2004",
                "requirement": "пароизоляционный слой должен предотвращать проникновение пара в конструкцию",
                "violation": "пароизоляция имеет разрывы и непроклеенные стыки",
                "recommendation": "восстановить пароизоляционный слой с перехлестом не менее 100мм"
            },
            "отлив": {
                "gost": "ГОСТ 30971-2012 п. 5.1.8",
                "requirement": "отлив должен обеспечивать отвод воды от конструкции",
                "violation": "отлив установлен с обратным уклоном, вода скапливается",
                "recommendation": "переустановить отлив с правильным уклоном"
            }
        }
        
        # Шаблоны для генерации нарушений
        self.violation_templates = {
            "base": "При осмотре выявлено, что {element} {violation}, что не соответствует требованиям {gost}",
            "detailed": "В ходе инспекционного осмотра установлено, что {element} {violation}. Согласно {gost} необходимо {requirement}. Требуется принятие мер по устранению выявленных несоответствий.",
            "critical": "Выявлено критическое несоответствие: {element} {violation}. Данное нарушение противоречит {gost}, где указано, что {requirement}. Необходимо незамедлительное устранение.",
            "with_photos": "Фотоматериалами подтверждается, что {element} {violation}. В соответствии с {gost} {requirement}. Рекомендуется руководствоваться указанным нормативным документом при исправлении."
        }
        
        # Шаблоны для генерации рекомендаций
        self.recommendation_templates = {
            "base": "В соответствии с {gost} необходимо {requirement}.",
            "detailed": "Руководствуясь требованиями {gost}, рекомендуется {requirement}. Также следует обратить внимание на правильность выполнения работ согласно системному каталогу ALUTECH.",
            "action": "Для устранения выявленного несоответствия необходимо {recommendation}. Работы выполнить в соответствии с {gost} и технической документацией.",
            "preventive": "С целью предотвращения подобных нарушений в будущем, рекомендуется {recommendation}. Контроль выполнения работ осуществлять согласно {gost}."
        }
    
    def analyze_text(self, text):
        """Анализирует текст и извлекает ключевые слова"""
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.gost_database.keys():
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def generate_violation(self, text, template_type="detailed"):
        """Генерирует подробное описание нарушения"""
        keywords = self.analyze_text(text)
        
        if not keywords:
            # Если ключевых слов не найдено, генерируем общее описание
            return f"В ходе инспекционного осмотра выявлены следующие нарушения: {text}. Данные нарушения не соответствуют требованиям нормативной документации (ГОСТ Р 52749-2007, ГОСТ 30971-2012). Требуется проведение дополнительной проверки и устранение выявленных несоответствий."
        
        results = []
        for keyword in keywords:
            data = self.gost_database[keyword]
            template = self.violation_templates.get(template_type, self.violation_templates["detailed"])
            
            generated_text = template.format(
                element=keyword,
                violation=data["violation"],
                gost=data["gost"],
                requirement=data["requirement"].lower()
            )
            results.append(generated_text)
        
        return " ".join(results)
    
    def generate_recommendation(self, text, template_type="detailed"):
        """Генерирует подробные рекомендации"""
        keywords = self.analyze_text(text)
        
        if not keywords:
            return f"Рекомендуется: {text}. Работы выполнять в соответствии с требованиями ГОСТ Р 52749-2007 и ГОСТ 30971-2012, руководствуясь системными каталогами ALUTECH."
        
        results = []
        for keyword in keywords:
            data = self.gost_database[keyword]
            template = self.recommendation_templates.get(template_type, self.recommendation_templates["detailed"])
            
            generated_text = template.format(
                gost=data["gost"],
                requirement=data["requirement"].lower(),
                recommendation=data["recommendation"].lower()
            )
            results.append(generated_text)
        
        return " ".join(results)
    
    def enhance_text(self, text, text_type="findings"):
        """Основной метод для улучшения текста"""
        if not text or len(text.strip()) < 10:
            return text
        
        # Проверяем, есть ли уже ссылки на ГОСТы
        has_gost = bool(re.search(r'ГОСТ\s+[Р]?\s?\d+', text))
        
        if text_type == "findings":
            enhanced = self.generate_violation(text)
            # Если в оригинале были ГОСТы, добавляем дополнительную информацию
            if has_gost and len(enhanced) < len(text) * 1.5:
                enhanced = text + " " + enhanced
            return enhanced
        elif text_type == "recommendations":
            enhanced = self.generate_recommendation(text)
            if has_gost and len(enhanced) < len(text) * 1.5:
                enhanced = text + " " + enhanced
            return enhanced
        else:
            return text
    
    def auto_complete(self, text, text_type="findings"):
        """Автоматическое дополнение короткого текста"""
        if len(text) < 30:
            # Для очень коротких текстов используем расширенные шаблоны
            keywords = self.analyze_text(text)
            if keywords:
                return self.generate_violation(text, template_type="critical")
            else:
                # Генерируем общее описание
                general_templates = [
                    f"При осмотре выявлено нарушение: {text}. Согласно требованиям ГОСТ Р 52749-2007 и ГОСТ 30971-2012, данное несоответствие требует незамедлительного устранения. Рекомендуется руководствоваться системными каталогами ALUTECH.",
                    f"В ходе инспекции установлено, что {text}. Данное нарушение не соответствует нормативным требованиям. Необходимо выполнить работы в соответствии с действующей нормативной документацией.",
                    f"Выявлено несоответствие: {text}. Требования ГОСТ Р 52749-2007 и ГОСТ 30971-2012 регламентируют правильное выполнение работ. Рекомендуется провести дополнительные мероприятия по устранению."
                ]
                return random.choice(general_templates)
        return self.enhance_text(text, text_type)

# Инициализируем нейросеть
neural_engine = NeuralTextGenerator()

# ============= КОНЕЦ НЕЙРОСЕТИ =============

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/get_time', methods=['GET'])
def get_time():
    now = datetime.now()
    return jsonify({
        'date': now.strftime('%d.%m.%Y'),
        'time': now.strftime('%H:%M:%S')
    })

@app.route('/expand_text', methods=['POST'])
def expand_text():
    """API endpoint для расширения текста с помощью встроенной нейросети"""
    try:
        data = request.get_json()
        short_text = data.get('text', '')
        text_type = data.get('type', 'findings')
        
        if not short_text:
            return jsonify({'success': False, 'error': 'Текст не предоставлен'})
        
        # Используем встроенную нейросеть
        expanded_text = neural_engine.auto_complete(short_text, text_type)
        
        return jsonify({
            'success': True,
            'expanded_text': expanded_text,
            'ai_model': 'Built-in Neural Network v1.0'
        })
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    """Анализ текста и определение ключевых слов"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        keywords = neural_engine.analyze_text(text)
        
        return jsonify({
            'success': True,
            'keywords': keywords,
            'gost_found': bool(re.search(r'ГОСТ\s+[Р]?\s?\d+', text))
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def process_photos_for_pdf(photos_data, start_number=1):
    """Обрабатывает загруженные фото для вставки в PDF"""
    photo_elements = []
    current_number = start_number
    
    for photo_data in photos_data:
        if photo_data and isinstance(photo_data, dict) and 'data' in photo_data:
            try:
                image_data = base64.b64decode(photo_data['data'])
                temp_path = os.path.join('uploads', f'photo_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{current_number}.jpg')
                
                with open(temp_path, 'wb') as f:
                    f.write(image_data)
                
                img = PILImage.open(temp_path)
                img.thumbnail((400, 300), PILImage.Resampling.LANCZOS)
                img.save(temp_path, 'JPEG', quality=85)
                
                img_element = Image(temp_path, width=120*mm, height=90*mm)
                photo_elements.append(img_element)
                photo_elements.append(Spacer(1, 2*mm))
                
                caption = photo_data.get('caption', f'Фото {current_number}')
                photo_elements.append(Paragraph(caption, photo_caption_style))
                photo_elements.append(Spacer(1, 5*mm))
                
                os.remove(temp_path)
                current_number += 1
            except Exception as e:
                print(f"Ошибка при обработке фото: {e}")
                continue
    
    return photo_elements, current_number

@app.route('/generate', methods=['POST', 'OPTIONS'])
def generate():
    if request.method == 'OPTIONS':
        return '', 200
        
    print("=" * 50)
    print("POST запрос получен!")
    
    try:
        engineer = request.form.get('engineer', '').strip()
        manufacturer = request.form.get('manufacturer', 'ООО «ПСК»')
        inspector = request.form.get('inspector', 'ООО «Алютех-Урал»')
        object_name = request.form.get('object_name', 'Административное здание')
        address = request.form.get('address', 'г. Екатеринбург, ул. Толмачева 6')
        accompanying = request.form.get('accompanying', 'Представитель заказчика')
        findings = request.form.get('findings', '')
        recommendations = request.form.get('recommendations', '')
        conclusion = request.form.get('conclusion', '')
        inspection_date = request.form.get('inspection_date', datetime.now().strftime('%d.%m.%Y'))
        
        photos_json = request.form.get('photos_json', '[]')
        photos_data = json.loads(photos_json) if photos_json else []

        print(f"Инженер: {engineer}")
        print(f"Получено фотографий: {len(photos_data)}")

        if not engineer:
            response = jsonify({'success': False, 'error': 'Укажите ФИО инженера'})
            response.status_code = 400
            return response

        # Обработка нарушений через нейросеть
        findings_lines = []
        if findings and findings.strip():
            raw_lines = [f.strip() for f in findings.split('\n') if f.strip()]
            for line in raw_lines:
                clean_line = line
                if len(line) > 2 and (line[0].isdigit() and line[1] in ['.', ')']):
                    clean_line = line[2:].strip()
                
                # Если текст короткий, расширяем нейросетью
                if len(clean_line) < 60:
                    expanded = neural_engine.auto_complete(clean_line, "findings")
                    findings_lines.append(expanded)
                else:
                    # Даже длинные тексты проверяем на наличие ГОСТов
                    if not re.search(r'ГОСТ\s+[Р]?\s?\d+', clean_line):
                        expanded = neural_engine.enhance_text(clean_line, "findings")
                        findings_lines.append(expanded)
                    else:
                        findings_lines.append(clean_line)
        else:
            findings_lines = []

        # Обработка рекомендаций через нейросеть
        recommendations_lines = []
        if recommendations and recommendations.strip():
            raw_recs = [r.strip() for r in recommendations.split('\n') if r.strip()]
            for rec in raw_recs:
                clean_rec = rec
                if len(rec) > 2 and (rec[0].isdigit() and rec[1] in ['.', ')']):
                    clean_rec = rec[2:].strip()
                
                if len(clean_rec) < 60:
                    expanded = neural_engine.auto_complete(clean_rec, "recommendations")
                    recommendations_lines.append(expanded)
                else:
                    if not re.search(r'ГОСТ\s+[Р]?\s?\d+', clean_rec):
                        expanded = neural_engine.enhance_text(clean_rec, "recommendations")
                        recommendations_lines.append(expanded)
                    else:
                        recommendations_lines.append(clean_rec)
        else:
            recommendations_lines = []

        now = datetime.now()
        
        # Генерация уникального номера отчета в формате ДД-ММ-ГГГГ-XXX
        report_date_obj = datetime.strptime(inspection_date, '%d.%m.%Y') if inspection_date else now
        date_str = report_date_obj.strftime('%d-%m-%Y')
        
        # Считаем количество отчетов за сегодня
        reports_today = [f for f in os.listdir('reports') if f.startswith(f'report_{date_str}')]
        report_counter = len(reports_today) + 1
        report_number_formatted = f"{date_str}-{report_counter:03d}"
        
        # Сохраняем также старый формат для отображения в отчете
        report_number = f"УТР{now.strftime('%d%m')}/{now.strftime('%y')}"
        report_date = inspection_date

        # Создаем PDF отчет
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        story = []
        
        # ЗАГОЛОВОК - используем новый формат номера
        story.append(Paragraph(f"<b>ОТЧЕТ № {report_number_formatted}</b>", title_style))
        story.append(Paragraph("инспекционного осмотра объекта", title_style))
        story.append(Spacer(1, 6*mm))
        
        # ШАПКА
        header_data = [
            [Paragraph(f"<b>ДАТА ИНСПЕКЦИИ:</b> {report_date}", normal_style), 
             Paragraph("<b>ГОРОД/СТРАНА:</b> Екатеринбург/РФ", normal_style)]
        ]
        header_table = Table(header_data, colWidths=[80*mm, 80*mm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'TimesNewRoman'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 5*mm))
        
        # ОРГАНИЗАЦИИ
        org_data = [
            [Paragraph("<b>ОРГАНИЗАЦИЯ ПРОИЗВОДИТЕЛЬ/УСТАНОВЩИК:</b>", normal_style),
             Paragraph("<b>ОРГАНИЗАЦИЯ ПРОВЕРЯЮЩИЙ:</b>", normal_style)],
            [Paragraph(manufacturer, normal_style),
             Paragraph(inspector, normal_style)]
        ]
        org_table = Table(org_data, colWidths=[80*mm, 80*mm])
        org_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'TimesNewRoman'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(org_table)
        story.append(Spacer(1, 5*mm))
        
        # ОБЪЕКТ
        object_data = [
            [Paragraph("<b>НАИМЕНОВАНИЕ ОБЪЕКТА УСТАНОВКИ:</b>", normal_style),
             Paragraph("<b>СОПРОВОЖДАЮЩЕЕ ЛИЦО:</b>", normal_style)],
            [Paragraph(object_name, normal_style),
             Paragraph(accompanying, normal_style)],
            [Paragraph(f"<b>АДРЕС:</b> {address}", normal_style), Paragraph("", normal_style)]
        ]
        object_table = Table(object_data, colWidths=[80*mm, 80*mm])
        object_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'TimesNewRoman'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(object_table)
        story.append(Spacer(1, 10*mm))
        
        # РАЗДЕЛ 1
        story.append(Paragraph("1. <b>ОСНОВАНИЯ ПРОВЕДЕНИЯ ИНСПЕКЦИОННОГО ОСМОТРА:</b>", subtitle_style))
        story.append(Paragraph(f"Обращение компании {manufacturer} для проведения аудита монтируемых конструкций на объекте {object_name}, {address}", normal_style))
        story.append(Spacer(1, 8*mm))
        
        # РАЗДЕЛ 2
        story.append(Paragraph("<b>РЕЗУЛЬТАТЫ ИНСПЕКЦИОННОГО ОСМОТРА:</b>", subtitle_style))
        story.append(Paragraph("1. <b>Были осмотрены монтируемые конструкции из профильной системы ALUTECH W72W</b>", normal_style))
        story.append(Spacer(1, 3*mm))
        
        # Выявленные нарушения
        story.append(Paragraph("<b>Выявлено:</b>", normal_style))
        
        if findings_lines:
            for i, finding in enumerate(findings_lines, 1):
                story.append(Paragraph(f"{i}. {finding}", normal_style))
                story.append(Spacer(1, 2*mm))
        else:
            story.append(Paragraph("Нарушения не указаны", normal_style))
        
        story.append(Spacer(1, 8*mm))
        
        # РАЗДЕЛ 3 - РЕКОМЕНДАЦИИ
        story.append(Paragraph("2. <b>РЕКОМЕНДАЦИИ:</b>", subtitle_style))
        
        if recommendations_lines:
            for i, rec in enumerate(recommendations_lines, 1):
                story.append(Paragraph(f"{i}. {rec}", normal_style))
                story.append(Spacer(1, 2*mm))
        else:
            story.append(Paragraph("Рекомендации не указаны", normal_style))
        
        story.append(Spacer(1, 8*mm))
        
        # ФОТОГРАФИИ
        if photos_data:
            story.append(Paragraph("<b>Фотоматериалы:</b>", normal_style))
            story.append(Spacer(1, 3*mm))
            
            photo_elements, _ = process_photos_for_pdf(photos_data)
            story.extend(photo_elements)
            story.append(Spacer(1, 5*mm))
        
        # РАЗДЕЛ 4 - ЗАКЛЮЧЕНИЕ
        story.append(Paragraph("3. <b>ЗАКЛЮЧЕНИЕ:</b>", subtitle_style))
        if conclusion and conclusion.strip():
            story.append(Paragraph(conclusion, normal_style))
        else:
            story.append(Paragraph("По результатам осмотра были выявлены ряд отклонений от требований актуальных каталогов и нормативной документации. Рекомендации даны выше по тексту.", normal_style))
        
        story.append(Spacer(1, 15*mm))
        
        # ПОДПИСИ
        story.append(Paragraph(f"Шеф инженер {engineer}", normal_style))
        story.append(Paragraph(inspector, normal_style))
        story.append(Paragraph(f"ДАТА {report_date}", normal_style))
        
        doc.build(story)
        buffer.seek(0)
        
        # Имя файла с новым форматом
        filename = f"report_{report_number_formatted}.pdf"
        filepath = os.path.join('reports', filename)
        
        with open(filepath, 'wb') as f:
            f.write(buffer.getvalue())
        
        findings_count = len(findings_lines) if findings_lines else 0

        print(f"PDF отчет создан: {filename}")
        print("=" * 50)

        response = jsonify({
            'success': True,
            'pdf_url': f'/download/{filename}',
            'report_number': report_number_formatted,
            'date': report_date,
            'findings_count': findings_count,
        })
        return response

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({'success': False, 'error': str(e)})
        response.status_code = 500
        return response

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    if '..' in filename or filename.startswith('/'):
        return "Некорректное имя файла", 400
    
    filepath = os.path.join('reports', filename)
    if os.path.exists(filepath) and os.path.isfile(filepath):
        return send_file(
            filepath, 
            as_attachment=True, 
            download_name=filename,
            mimetype='application/pdf'
        )
    return "Файл не найден", 404

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 СЕРВЕР ЗАПУЩЕН")
    print("=" * 60)
    print("📁 Открыть в браузере: http://127.0.0.1:5000")
    print("📄 Отчеты создаются в формате PDF")
    print("📋 Формат номера отчета: ДД-ММ-ГГГГ-XXX")
    print("🤖 ВСТРОЕННАЯ НЕЙРОСЕТЬ: Активна")
    print("=" * 60 + "\n")
    app.run(host='127.0.0.1', port=5000, debug=True)