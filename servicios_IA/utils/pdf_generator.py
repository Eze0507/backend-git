"""
Generador de reportes en formato PDF usando ReportLab (más simple y compatible)
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime


def generar_pdf_tabla(titulo, subtitulo, encabezados, datos, datos_adicionales=None):
    """
    Genera un PDF con una tabla de datos
    
    Args:
        titulo: Título del reporte
        subtitulo: Subtítulo o descripción
        encabezados: Lista de nombres de columnas
        datos: Lista de listas con los datos
        datos_adicionales: Dict con información extra (opcional)
    
    Returns:
        BytesIO con el contenido del PDF
    """
    buffer = BytesIO()
    
    # Crear el documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.5*inch
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_RIGHT
    )
    
    # Elementos del PDF
    elements = []
    
    # Título
    elements.append(Paragraph(titulo, titulo_style))
    elements.append(Paragraph(subtitulo, subtitulo_style))
    
    # Fecha de generación
    fecha_hora = datetime.now().strftime('%d/%m/%Y %H:%M')
    elements.append(Paragraph(f"Generado: {fecha_hora}", info_style))
    
    # Información adicional
    if datos_adicionales:
        for key, value in datos_adicionales.items():
            elements.append(Paragraph(f"{key}: {value}", info_style))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Preparar datos de la tabla
    tabla_data = [encabezados] + datos
    
    # Crear la tabla
    tabla = Table(tabla_data, repeatRows=1)
    
    # Estilo de la tabla
    tabla.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Datos
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        
        # Bordes
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        
        # Filas alternadas
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))
    
    elements.append(tabla)
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Sistema de Gestión de Taller - Reporte Automático", footer_style))
    
    # Generar el PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer


def generar_pdf_simple(datos_reporte):
    """
    Wrapper simplificado para generar PDF
    
    Args:
        datos_reporte: Dict con titulo, subtitulo, encabezados, datos, info_adicional
    
    Returns:
        BytesIO con el contenido del PDF
    """
    return generar_pdf_tabla(
        titulo=datos_reporte.get('titulo', 'Reporte'),
        subtitulo=datos_reporte.get('subtitulo', ''),
        encabezados=datos_reporte.get('encabezados', []),
        datos=datos_reporte.get('datos', []),
        datos_adicionales=datos_reporte.get('info_adicional')
    )


# CSS base para los reportes
CSS_BASE = """
@page {
    size: letter;
    margin: 2cm;
}

body {
    font-family: Arial, sans-serif;
    font-size: 10pt;
    color: #333;
}

h1 {
    color: #2c3e50;
    border-bottom: 3px solid #3498db;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

h2 {
    color: #34495e;
    border-bottom: 1px solid #bdc3c7;
    padding-bottom: 5px;
    margin-top: 20px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
}

th {
    background-color: #3498db;
    color: white;
    padding: 10px;
    text-align: left;
    font-weight: bold;
}

td {
    padding: 8px;
    border-bottom: 1px solid #ecf0f1;
}

tr:nth-child(even) {
    background-color: #f8f9fa;
}

.total {
    font-weight: bold;
    background-color: #e8f4f8;
}

.header {
    text-align: center;
    margin-bottom: 30px;
}

.footer {
    text-align: center;
    font-size: 8pt;
    color: #7f8c8d;
    margin-top: 30px;
}

.metric {
    display: inline-block;
    padding: 10px 20px;
    margin: 10px;
    background-color: #ecf0f1;
    border-radius: 5px;
}

.alerta-urgente {
    background-color: #ffebee;
    color: #c62828;
}

.alerta-atencion {
    background-color: #fff9c4;
    color: #f57f17;
}

.alerta-normal {
    background-color: #e8f5e9;
    color: #2e7d32;
}
"""
