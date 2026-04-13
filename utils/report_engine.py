import os
import datetime
from PySide6.QtGui import QPainter, QFont, QColor, QPen, QImage, QPixmap, QPageLayout
from PySide6.QtCore import Qt, QRect, QMarginsF
from PySide6.QtPrintSupport import QPrinter

class ExecutiveReportEngine:
    """
    High-fidelity clinical PDF generation engine.
    Utilizes native QtPrintSupport for professional typesetting and vector-quality reporting.
    """
    def __init__(self, parent=None):
        self.parent = parent
        # Colors - Match Dashboard MissionControl Branding
        self._red = QColor("#EF4444")
        self._green = QColor("#10B981")
        self._blue = QColor("#3B82F6")
        self._text = QColor("#1F2937")
        self._muted = QColor("#6B7280")
        self._border = QColor("#E5E7EB")
        
    def generate_dossier(self, output_path, data_summary, leaderboard, audit_logs=None, charts=None):
        """
        Produce a multi-page, executive-grade clinical audit report.
        """
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(output_path)
        
        # 🧪 CROSS-VERSION STABILITY: Force Portrait (0) using the Orientation enum
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setFullPage(True)
        
        print(f"🚀 INITIALIZING DOSSIER GENERATION: {os.path.basename(output_path)}")
        painter = QPainter()
        try:
            if not painter.begin(printer):
                return False, "Failed to initiate PDF Painter Engine."

            # Setup Page Metrics
            rect = painter.viewport()
            w, h = rect.width(), rect.height()
            margin_x = int(w * 0.05)
            margin_y = int(h * 0.05)
            content_w = w - (2 * margin_x)
            
            # ─── PAGE 1: EXECUTIVE SUMMARY ───
            print(f"  └── Rendering Executive Page Header...")
            self._draw_header(painter, w, margin_x, margin_y, data_summary)
            
            current_y = margin_y + 1400 
            
            print(f"  └── Computing Metadata Grids...")
            current_y = self._draw_section_title(painter, "I. CLINICAL AUDIT OVERVIEW", margin_x, current_y)
            current_y = self._draw_summary_grid(painter, data_summary, margin_x, current_y, content_w)
            
            print(f"  └── Building Algorithm Leaderboard...")
            current_y += 400
            current_y = self._draw_section_title(painter, "II. ALGORITHM RANKING & SENSITIVITY", margin_x, current_y)
            current_y = self._draw_leaderboard_table(painter, leaderboard, margin_x, current_y, content_w)
            
            print(f"  └── Syncing Committee Consensus...")
            current_y += 400
            current_y = self._draw_section_title(painter, "III. COMMITTEE CONSENSUS LOG", margin_x, current_y)
            summary_text = (
                f"Threshold Detection: The clinical forensic committee calibrated a total of {data_summary.get('Total_Patients', 0)} "
                f"patient records. A detected cohort of {data_summary.get('High_Risk_Count', 0)} individuals showed high biomarker "
                f"variance consistent with malignant patterns."
            )
            current_y = self._draw_wrapped_text(painter, summary_text, margin_x, current_y, content_w)

            # ─── PAGE 2: FORENSIC VISUALIZATIONS (If charts provided) ───
            if charts:
                print(f"  └── Orchestrating Forensic Multi-Page Visuals...")
                printer.newPage()
                current_y = margin_y
                current_y = self._draw_section_title(painter, "IV. BIOMARKER SPATIAL DISTRIBUTION & XAI", margin_x, current_y)
                
                chart_h = int(h * 0.3)
                chart_w = int(content_w * 0.48)
                
                items = list(charts.items())[:4]
                for i, (name, img_data) in enumerate(items):
                    row = i // 2
                    col = i % 2
                    px = margin_x + (col * (chart_w + int(content_w * 0.04)))
                    py = current_y + (row * (chart_h + 200))
                    self._draw_chart_frame(painter, name, img_data, px, py, chart_w, chart_h)

            # ─── FOOTER & SIGN-OFF (Global) ───
            print(f"  └── Finalizing Executive Sign-off...")
            self._draw_footer(painter, w, h, margin_x, margin_y)
            
        finally:
            # 🛡️ SYSTEM PURGE: Ensure the paint device is released even on failure
            print(f"🏁 Dossier Engine Deactivated. Releasing QPaintDevice.")
            if painter.isActive():
                painter.end()
                
        return True, f"Dossier successfully compiled: {output_path}"

    def _draw_header(self, painter, w, mx, my, summary):
        # 1. Indigo Branding - Clinical Intelligence Badge
        self._indigo = QColor("#4F46E5")
        painter.setBrush(self._indigo)
        painter.setPen(Qt.NoPen)
        logo_rect = QRect(mx, my, 800, 480)
        painter.drawRoundedRect(logo_rect, 100, 100)
        
        painter.setPen(Qt.white)
        f_logo = QFont("Arial", 16, QFont.Bold)
        painter.setFont(f_logo)
        painter.drawText(logo_rect, Qt.AlignCenter, "XAI")
        
        # 2. Primary Narrative Executive Title
        painter.setPen(self._text)
        painter.setFont(QFont("Arial", 26, QFont.Bold))
        painter.drawText(mx + 950, my + 100, w - (2*mx) - 950, 400, Qt.AlignLeft, "EXECUTIVE CLINICAL FORENSIC DOSSIER")
        
        # 3. Dynamic Clinical Subheader (The Live Intelligence Strip)
        painter.setFont(QFont("Arial", 11, QFont.Normal))
        painter.setPen(self._muted)
        time_str = datetime.datetime.now().strftime("%Y-%m-%d | %H:%M")
        
        # Calculate summary highlights
        total_p = summary.get('Total_Patients', 0)
        avg_r = summary.get('Avg_Risk', 0.0)
        risk_label = "HIGH RISK" if avg_r > 0.5 else "CALIBRATED"
        status_color = self._red if avg_r > 0.5 else self._blue
        
        info_text = (
            f"AI COMMITTEE STATUS: <b style='color: {status_color.name()}'>{risk_label}</b> | "
            f"COHORT SCOPE: {total_p} SAMPLES | "
            f"GENERATED: {time_str} UTC"
        )
        
        # Note: painter.drawText doesn't support HTML, so we compile a flat string for it
        flat_info = f"AI STATUS: {risk_label}  |  COHORT: {total_p} PATIENTS  |  PRINT TIME: {time_str}"
        painter.drawText(mx + 950, my + 450, w - (2*mx) - 950, 200, Qt.AlignLeft, flat_info)
        
        # 4. Premium Structural Divider
        painter.setPen(QPen(self._border, 30))
        painter.drawLine(mx, my + 800, w - mx, my + 800)
        
        # 5. Strategic Calibration Note
        f_note = QFont("Arial", 9)
        f_note.setItalic(True)
        painter.setFont(f_note)
        painter.setPen(self._muted)
        painter.drawText(mx, my + 1050, w - (2*mx), 200, Qt.AlignRight, "SECURE V1.2.0 | CLINICAL AUDIT PROTOCOL: ACTIVE")
        
    def _draw_section_title(self, painter, title, x, y):
        painter.setPen(self._indigo) # Consistent Indigo Theme
        painter.setFont(QFont("Arial", 13, QFont.Bold))
        painter.drawText(x, y, 5000, 200, Qt.AlignLeft, title)
        return y + 350

    def _draw_summary_grid(self, painter, summary, x, y, width):
        painter.setPen(self._border)
        painter.setBrush(Qt.NoBrush)
        
        box_w = width // 3
        box_h = 600
        
        metrics = [
            ("TOTAL PATIENTS", str(summary.get('Total_Patients', '0'))),
            ("COHORT RISK", f"{summary.get('Avg_Risk', 0):.1%}"),
            ("THRESHOLD", f"{summary.get('Threshold', 'N/A')}")
        ]
        
        for i, (label, val) in enumerate(metrics):
            px = x + (i * box_w)
            rect = QRect(px, y, box_w - 100, box_h)
            painter.setPen(QPen(self._border, 5))
            painter.drawRoundedRect(rect, 20, 20)
            
            painter.setPen(self._muted)
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.drawText(rect.adjusted(50, 50, -50, -300), Qt.AlignCenter, label)
            
            painter.setPen(self._text)
            painter.setFont(QFont("Arial", 16, QFont.Bold))
            painter.drawText(rect.adjusted(50, 250, -50, -50), Qt.AlignCenter, val)
            
        return y + box_h + 200

    def _draw_leaderboard_table(self, painter, leaderboard, x, y, width):
        # Header Row
        row_h = 350
        painter.setBrush(QColor("#F9FAFB"))
        painter.setPen(Qt.NoPen)
        header_rect = QRect(x, y, width, row_h)
        painter.drawRect(header_rect)
        
        painter.setPen(self._muted)
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        headers = ["RANK", "ALGORITHM", "ACCURACY", "F1 SCORE", "STABILITY"]
        col_w = [int(width*0.1), int(width*0.4), int(width*0.15), int(width*0.15), int(width*0.2)]
        
        cx = x + 100
        for i, h_text in enumerate(headers):
            painter.drawText(cx, y, col_w[i], row_h, Qt.AlignVCenter, h_text)
            cx += col_w[i]
            
        cy = y + row_h
        painter.setFont(QFont("Arial", 9, QFont.Normal))
        
        for i, row in enumerate(leaderboard[:5]):
            if i % 2 == 1:
                painter.setBrush(QColor("#FFFFFF"))
            else:
                painter.setBrush(QColor("#F9FAFB"))
            
            row_rect = QRect(x, cy, width, row_h)
            painter.drawRect(row_rect)
            
            painter.setPen(self._text)
            cx = x + 100
            
            # Rank
            painter.drawText(cx, cy, col_w[0], row_h, Qt.AlignVCenter, f"#{i+1}")
            cx += col_w[0]
            # Name
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(cx, cy, col_w[1], row_h, Qt.AlignVCenter, str(row.get('model', 'Unknown')))
            painter.setFont(QFont("Arial", 9, QFont.Normal))
            cx += col_w[1]
            # Accuracy
            painter.drawText(cx, cy, col_w[2], row_h, Qt.AlignVCenter, f"{row.get('accuracy', 0):.1%}")
            cx += col_w[2]
            # F1
            painter.drawText(cx, cy, col_w[3], row_h, Qt.AlignVCenter, f"{row.get('f1', 0):.1%}")
            cx += col_w[3]
            # Stability
            cv = f"{row.get('cv_mean', 0):.1%} (+/- {row.get('cv_std', 0):.2f})"
            painter.drawText(cx, cy, col_w[4], row_h, Qt.AlignVCenter, cv)
            
            cy += row_h
            
            cy += row_h
            
        return cy + 200

    def _draw_wrapped_text(self, painter, text, x, y, width):
        painter.setPen(self._text)
        painter.setFont(QFont("Arial", 10, QFont.Normal))
        rect = QRect(x, y, width, 1500)
        painter.drawText(rect, Qt.AlignLeft | Qt.TextWordWrap, text)
        return y + 800

    def _draw_chart_frame(self, painter, title, img_path_or_bytes, x, y, w, h):
        # Draw Label
        painter.setPen(self._muted)
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.drawText(x, y - 50, w, 100, Qt.AlignLeft, title.upper())
        
        # Draw Chart Box
        frame_rect = QRect(x, y, w, h)
        painter.setPen(QPen(self._border, 2))
        painter.drawRoundedRect(frame_rect, 10, 10)
        
        # Load and Draw Image
        try:
            if isinstance(img_path_or_bytes, str) and os.path.exists(img_path_or_bytes):
                img = QImage(img_path_or_bytes)
                painter.drawImage(frame_rect.adjusted(20, 20, -20, -20), img)
        except:
            painter.drawText(frame_rect, Qt.AlignCenter, "[Visualization Render Error]")

    def _draw_footer(self, painter, w, h, mx, my):
        fy = h - my - 1500
        
        # Divider
        painter.setPen(QPen(self._border, 10))
        painter.drawLine(mx, fy, w - mx, fy)
        
        # Disclaimer
        painter.setPen(self._muted)
        painter.setFont(QFont("Arial", 8, QFont.Normal))
        disclaimer = (
            "DISCLAIMER: This report is generated by a multi-modal AI committee for research and experimental purposes only. "
            "Algorithms should be validated against gold-standard biopsy results. Not for standalone clinical diagnosis."
        )
        painter.drawText(mx, fy + 200, w - (2*mx), 400, Qt.AlignCenter | Qt.TextWordWrap, disclaimer)
        
        # Signature Line
        sy = h - my - 500
        painter.setPen(QPen(self._text, 15))
        sig_w = 2500
        painter.drawLine(w - mx - sig_w, sy, w - mx, sy)
        painter.setPen(self._text)
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(w - mx - sig_w, sy + 100, sig_w, 200, Qt.AlignCenter, "CERTIFIED PHYSICIAN SIGNATURE")
        
        # Branding
        painter.setPen(self._muted)
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(mx, sy + 100, 4000, 200, Qt.AlignLeft, "CANCER DETECTION | FORENSIC HUD 1.0.4")
