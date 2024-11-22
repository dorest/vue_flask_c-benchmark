from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import matplotlib.pyplot as plt
import base64

class ReportService:
    @staticmethod
    def generate_test_report(test_result):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # 标题
        title_style = styles['Heading1']
        story.append(Paragraph(f"性能测试报告 - {test_result.test_case.name}", title_style))
        story.append(Spacer(1, 12))

        # 基本信息
        basic_info = [
            ['测试用例名称', test_result.test_case.name],
            ['开始时间', test_result.start_time.strftime('%Y-%m-%d %H:%M:%S')],
            ['结束时间', test_result.end_time.strftime('%Y-%m-%d %H:%M:%S')],
            ['执行状态', test_result.status],
            ['执行命令', test_result.test_case.command]
        ]
        
        basic_table = Table(basic_info, colWidths=[2*inch, 4*inch])
        basic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (-1, -1), colors.beige),
            ('TEXTCOLOR', (1, 0), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(basic_table)
        story.append(Spacer(1, 20))

        # 性能数据图表
        story.append(Paragraph("性能数据分析", styles['Heading2']))
        story.append(Spacer(1, 12))

        # CPU使用率图表
        if test_result.perf_data.get('cpu'):
            plt.figure(figsize=(8, 4))
            cpu_data = test_result.perf_data['cpu']
            plt.plot([d['timestamp'] for d in cpu_data], [d['value'] for d in cpu_data])
            plt.title('CPU使用率趋势')
            plt.xlabel('时间')
            plt.ylabel('CPU使用率(%)')
            
            cpu_img_buffer = BytesIO()
            plt.savefig(cpu_img_buffer, format='png')
            plt.close()
            
            cpu_img = Image(cpu_img_buffer)
            cpu_img.drawHeight = 3*inch
            cpu_img.drawWidth = 6*inch
            story.append(cpu_img)
            story.append(Spacer(1, 12))

        # 内存使用图表
        if test_result.perf_data.get('memory'):
            plt.figure(figsize=(8, 4))
            memory_data = test_result.perf_data['memory']
            plt.plot([d['timestamp'] for d in memory_data], [d['value'] for d in memory_data])
            plt.title('内存使用趋势')
            plt.xlabel('时间')
            plt.ylabel('内存使用(MB)')
            
            memory_img_buffer = BytesIO()
            plt.savefig(memory_img_buffer, format='png')
            plt.close()
            
            memory_img = Image(memory_img_buffer)
            memory_img.drawHeight = 3*inch
            memory_img.drawWidth = 6*inch
            story.append(memory_img)
            story.append(Spacer(1, 12))

        # 基准线比较
        if test_result.benchmark_data:
            story.append(Paragraph("基准线比较", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            benchmark_data = [['指标', '当前值', '基准值', '差异']]
            for metric, data in test_result.benchmark_data.items():
                benchmark_data.append([
                    metric,
                    f"{data['current']:.2f}",
                    f"{data['baseline']:.2f}",
                    f"{data['diff']:.2f}%"
                ])
            
            benchmark_table = Table(benchmark_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
            benchmark_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(benchmark_table)

        # 生成PDF
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data 