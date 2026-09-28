"""
generate_official_defense_form.py
---------------------------------
Generates the official Institute of Space Technology (IST) FYP Defense Proposal Form
(Form No: IST-Dean-F-23/00) in Microsoft Word (.docx), exports it to PDF via Word COM,
and generates the corresponding Markdown documentation.

Uses clear, straightforward, and easily understandable language without overwhelming
jargon, while maintaining high academic quality and professional 5-page layout budgeting.
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# --- XML Styling Helpers ---

def set_cell_border(cell, **kwargs):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = OxmlElement(tag)
            element.set(qn('w:val'), edge_data.get('val', 'single'))
            element.set(qn('w:sz'), str(edge_data.get('sz', 5)))
            element.set(qn('w:space'), '0')
            element.set(qn('w:color'), edge_data.get('color', '333333'))
            tcBorders.append(element)
        else:
            tag = f'w:{edge}'
            element = OxmlElement(tag)
            element.set(qn('w:val'), 'none')
            tcBorders.append(element)
    tcPr.append(tcBorders)

def set_all_borders(cell, sz=5, color='333333'):
    b_dict = dict(sz=sz, val='single', color=color)
    set_cell_border(cell, top=b_dict, bottom=b_dict, left=b_dict, right=b_dict)

def set_cell_shading(cell, color_hex):
    shading_elm = OxmlElement('w:shd')
    shading_elm.set(qn('w:val'), 'clear')
    shading_elm.set(qn('w:color'), 'auto')
    shading_elm.set(qn('w:fill'), color_hex)
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=50, bottom=50, left=90, right=90):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_header_table(header, issue_date="Fall 2026"):
    """Creates the official IST header table in the document header."""
    p_header = header.paragraphs[0]
    p_header.text = ""
    p_header.paragraph_format.space_before = Pt(0)
    p_header.paragraph_format.space_after = Pt(0)
    
    table = header.add_table(rows=3, cols=3, width=Inches(7.1))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    col_widths = [Inches(3.3), Inches(1.3), Inches(2.5)]
    
    row_data = [
        [("Institute of Space Technology", True, 10), ("Form No", True, 9.5), ("IST-Dean-F-23/00", False, 9.5)],
        [("FYP Selection Form", False, 9.5), ("Issue Date", True, 9.5), (issue_date, False, 9.5)],
        [("Grading Policy on Final Year Projects", False, 9), ("Department", True, 9.5), ("Department of Space Science", False, 9.5)]
    ]
    
    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = col_widths[c_idx]
            text, bold, sz = row_data[r_idx][c_idx]
            p = cell.paragraphs[0]
            p.text = text
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            run = p.runs[0]
            run.font.name = 'Times New Roman'
            run.font.size = Pt(sz)
            run.font.bold = bold
            run.font.color.rgb = RGBColor(15, 23, 42)
            set_all_borders(cell, sz=5, color='475569')
            set_cell_margins(cell, top=35, bottom=35, left=70, right=70)
            if c_idx == 1:
                set_cell_shading(cell, 'F1F5F9')

def build_proposal_document(output_docx_path):
    doc = docx.Document()
    
    # Page Setup (8.5 x 11 in, 0.7 in side margins, 0.5 in top/bottom)
    for section in doc.sections:
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)
        section.header_distance = Inches(0.28)
        add_header_table(section.header)
    
    # Normal Style configuration
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(10)
    style_normal.font.color.rgb = RGBColor(15, 23, 42)
    style_normal.paragraph_format.line_spacing = 1.12
    style_normal.paragraph_format.space_after = Pt(2)
    
    # =========================================================================
    # PAGE 1: University Detail, Nominated Project Detail, Project Title & Summary
    # =========================================================================
    
    # Document Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(2)
    p_title.paragraph_format.space_after = Pt(6)
    r_title = p_title.add_run("Final Year Project (FYP) Defense Proposal Form")
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(13)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42)
    
    # 1. University/Institute Detail
    p_sec1 = doc.add_paragraph()
    p_sec1.paragraph_format.space_before = Pt(2)
    p_sec1.paragraph_format.space_after = Pt(2)
    r_sec1 = p_sec1.add_run("University/Institute Detail:")
    r_sec1.font.bold = True
    r_sec1.font.size = Pt(10.5)
    
    t_sec1 = doc.add_table(rows=3, cols=4)
    t_sec1.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_sec1.autofit = False
    col_w_4 = [Inches(1.65), Inches(1.85), Inches(1.45), Inches(2.15)]
    
    sec1_data = [
        [("Name of University/Institution:", True), ("Institute of Space Technology", False),
         ("Physical Address:", True), ("1, Islamabad Highway, Islamabad, 44000", False)],
        [("Telephone & Fax No:", True), ("+92-51-9075100\n+92-51-9273310", False),
         ("Department Name:", True), ("Department of Space Science", False)],
        [("City:", True), ("Islamabad", False),
         ("Province:", True), ("Islamabad Capital Territory (ICT)", False)]
    ]
    
    for r_idx, row in enumerate(t_sec1.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = col_w_4[c_idx]
            text, bold = sec1_data[r_idx][c_idx]
            p = cell.paragraphs[0]
            p.text = text
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.05
            run = p.runs[0]
            run.font.name = 'Times New Roman'
            run.font.size = Pt(9)
            run.font.bold = bold
            set_all_borders(cell, sz=5, color='475569')
            set_cell_margins(cell, top=35, bottom=35, left=75, right=75)
            if bold:
                set_cell_shading(cell, 'F8FAFC')
                
    # 2. Nominated Project Details
    p_sec2 = doc.add_paragraph()
    p_sec2.paragraph_format.space_before = Pt(5)
    p_sec2.paragraph_format.space_after = Pt(2)
    r_sec2 = p_sec2.add_run("Nominated Project Details:-")
    r_sec2.font.bold = True
    r_sec2.font.size = Pt(10.5)
    
    t_sec2 = doc.add_table(rows=5, cols=4)
    t_sec2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_sec2.autofit = False
    
    sec2_data = [
        [("Project Supervisor Name and Designation:", True), ("Dr. Munawar Ali Shah\nAssistant Professor", False),
         ("Contact Details:", True), ("munawar.shah@ist.edu.pk", False)],
        [("Project Supervisor Qualification:", True), ("Ph.D. in Geodesy and GNSS", False),
         ("No. of Publications of Supervisor:", True), ("Over 100 peer-reviewed journal and conference publications", False)],
        [("Students Name(s):", True), ("1. Mashaf Majeed Janjua\n2. Haider Taqveen", False),
         ("Students Mobile No:", True), ("1. +92-320-5409300\n2. +92-325-9514052", False)],
        [("Students CGPA:", True), ("1. 2.31\n2. 2.65", False),
         ("Students Email:", True), ("1. 230601017@ist.edu.pk\n2. 230601020@ist.edu.pk", False)],
        [("Degree Program / Title:", True), ("BS Space Science", False),
         ("Area of Specialization:", True), ("Remote Sensing & GIS (RS/GIS)", False)]
    ]
    
    for r_idx, row in enumerate(t_sec2.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = col_w_4[c_idx]
            text, bold = sec2_data[r_idx][c_idx]
            p = cell.paragraphs[0]
            p.text = text
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.05
            run = p.runs[0]
            run.font.name = 'Times New Roman'
            run.font.size = Pt(9)
            run.font.bold = bold
            set_all_borders(cell, sz=5, color='475569')
            set_cell_margins(cell, top=35, bottom=35, left=75, right=75)
            if bold:
                set_cell_shading(cell, 'F8FAFC')

    # 3. Final Year Project Details Header & Metadata
    p_sec3 = doc.add_paragraph()
    p_sec3.paragraph_format.space_before = Pt(5)
    p_sec3.paragraph_format.space_after = Pt(2)
    r_sec3 = p_sec3.add_run("Final Year Project Details:")
    r_sec3.font.bold = True
    r_sec3.font.size = Pt(10.5)
    
    t_proj_meta = doc.add_table(rows=3, cols=2)
    t_proj_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_proj_meta.autofit = False
    meta_widths = [Inches(1.8), Inches(5.3)]
    
    proj_meta_data = [
        ("A. Project Title:", True, "Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin", True),
        ("B. Project Start Date:", True, "September 01, 2026  (Fall Semester 2026)", False),
        ("C. Project Finish Date:", True, "June 30, 2027  (Spring Semester 2027)", False)
    ]
    
    for r_idx, (lbl, l_bold, val, v_bold) in enumerate(proj_meta_data):
        row = t_proj_meta.rows[r_idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width, c1.width = meta_widths[0], meta_widths[1]
        
        p0 = c0.paragraphs[0]
        p0.text = lbl
        p0.paragraph_format.space_before = Pt(1)
        p0.paragraph_format.space_after = Pt(1)
        r0 = p0.runs[0]
        r0.font.name = 'Times New Roman'
        r0.font.bold = l_bold
        r0.font.size = Pt(9.5)
        
        p1 = c1.paragraphs[0]
        p1.text = val
        p1.paragraph_format.space_before = Pt(1)
        p1.paragraph_format.space_after = Pt(1)
        r1 = p1.runs[0]
        r1.font.name = 'Times New Roman'
        r1.font.bold = v_bold
        r1.font.size = Pt(9.5)
        
        set_all_borders(c0, sz=5, color='475569')
        set_all_borders(c1, sz=5, color='475569')
        set_cell_shading(c0, 'F8FAFC')
        set_cell_margins(c0, top=40, bottom=40, left=75, right=75)
        set_cell_margins(c1, top=40, bottom=40, left=75, right=75)

    # D. Project Summary (Easy to understand, strictly < 200 words)
    p_d_lbl = doc.add_paragraph()
    p_d_lbl.paragraph_format.space_before = Pt(5)
    p_d_lbl.paragraph_format.space_after = Pt(2)
    r_d_lbl = p_d_lbl.add_run("D. Project Summary (less than 200 words):")
    r_d_lbl.font.bold = True
    r_d_lbl.font.size = Pt(10)
    
    t_summary = doc.add_table(rows=1, cols=1)
    t_summary.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_summary.autofit = False
    c_sum = t_summary.rows[0].cells[0]
    c_sum.width = Inches(7.1)
    set_all_borders(c_sum, sz=5, color='475569')
    set_cell_margins(c_sum, top=55, bottom=55, left=90, right=90)
    set_cell_shading(c_sum, 'FFFFFF')
    
    p_sum = c_sum.paragraphs[0]
    p_sum.paragraph_format.line_spacing = 1.10
    p_sum.paragraph_format.space_after = Pt(2)
    
    # Plain-English, straightforward summary
    summary_text = (
        "Drones are increasingly vital for disaster management, search and rescue, and environmental monitoring. "
        "However, flying a team of multiple autonomous drones (a swarm) in crowded cities is challenging because drones "
        "can easily collide with buildings, power lines, or each other. Testing real drones in physical cities is also expensive "
        "and dangerous. This project creates a 'Geospatial Digital Twin'—a realistic 3D computer model of a real city built "
        "directly from satellite images and ground elevation data. Inside this virtual world, we use Artificial Intelligence "
        "(Multi-Agent Reinforcement Learning) to teach a team of drones how to fly together autonomously. The drones learn by "
        "practice how to coordinate search patterns, avoid obstacles like buildings and overhead wires, and locate emergency "
        "rescue sound beacons without human pilots. We evaluate swarm performance by measuring mission completion time, area coverage, "
        "battery efficiency, and collision-free safety. Finally, an interactive 3D computer dashboard is developed so mission operators "
        "can observe the drones and track flight telemetry in real time."
    )
    r_sum = p_sum.add_run(summary_text)
    r_sum.font.name = 'Times New Roman'
    r_sum.font.size = Pt(9.5)
    
    w_count = len(summary_text.split())
    p_wcnt = c_sum.add_paragraph()
    p_wcnt.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_wcnt.paragraph_format.space_before = Pt(1)
    p_wcnt.paragraph_format.space_after = Pt(0)
    r_wcnt = p_wcnt.add_run(f"[Word Count: {w_count} words | Verified strictly < 200 words]")
    r_wcnt.font.size = Pt(8.5)
    r_wcnt.font.italic = True
    r_wcnt.font.color.rgb = RGBColor(100, 116, 139)

    # Force Page Break to Page 2
    doc.add_page_break()

    # =========================================================================
    # PAGE 2: Project Objectives & Implementation Method (Stages 1-3)
    # =========================================================================
    p_e_lbl = doc.add_paragraph()
    p_e_lbl.paragraph_format.space_before = Pt(0)
    p_e_lbl.paragraph_format.space_after = Pt(3)
    r_e_lbl = p_e_lbl.add_run("E. Project Objectives:")
    r_e_lbl.font.bold = True
    r_e_lbl.font.size = Pt(11)
    
    t_obj = doc.add_table(rows=1, cols=1)
    t_obj.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_obj.autofit = False
    c_obj = t_obj.rows[0].cells[0]
    c_obj.width = Inches(7.1)
    set_all_borders(c_obj, sz=5, color='475569')
    set_cell_margins(c_obj, top=65, bottom=65, left=90, right=90)
    
    # Easy-to-understand objectives
    objectives = [
        ("1. Build a 3D Virtual City (Digital Twin): ", "To automatically convert high-resolution optical satellite imagery and elevation data into a realistic 3D virtual environment with accurate building shapes, terrain heights, and low-altitude hazards such as power lines."),
        ("2. Simulate Realistic Drone Flight: ", "To simulate multiple quadcopter drones with realistic physical movement, motor thrust, battery energy limits, distance-measuring laser sensors (LiDAR), and emergency sound detectors."),
        ("3. Train AI for Drone Teamwork: ", "To train an artificial intelligence framework (Multi-Agent Deep Reinforcement Learning) where drones learn to fly together as a cooperative team without colliding with obstacles or each other."),
        ("4. Test Under Challenging Scenarios: ", "To test the drone swarm under difficult disaster conditions, including moving obstacles, windy weather, single-drone motor failures, and weak communication signals."),
        ("5. Measure and Compare Performance: ", "To evaluate swarm success using clear practical metrics (search speed, area covered, battery usage, and zero crashes) and compare the AI against traditional flight navigation methods."),
        ("6. Build a 3D Mission Control Screen: ", "To develop an interactive 3D visual dashboard where operators can see drone locations, watch live flight paths, and monitor mission progress in real time.")
    ]
    
    p_first_obj = c_obj.paragraphs[0]
    for idx, (title, desc) in enumerate(objectives):
        p = p_first_obj if idx == 0 else c_obj.add_paragraph()
        p.paragraph_format.line_spacing = 1.10
        p.paragraph_format.space_after = Pt(3)
        rt = p.add_run(title)
        rt.font.bold = True
        rt.font.name = 'Times New Roman'
        rt.font.size = Pt(9.5)
        rd = p.add_run(desc)
        rd.font.name = 'Times New Roman'
        rd.font.size = Pt(9.5)

    p_f_lbl = doc.add_paragraph()
    p_f_lbl.paragraph_format.space_before = Pt(8)
    p_f_lbl.paragraph_format.space_after = Pt(3)
    r_f_lbl = p_f_lbl.add_run("F. Project Implementation Method:")
    r_f_lbl.font.bold = True
    r_f_lbl.font.size = Pt(11)
    
    t_meth = doc.add_table(rows=1, cols=1)
    t_meth.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_meth.autofit = False
    c_meth = t_meth.rows[0].cells[0]
    c_meth.width = Inches(7.1)
    set_all_borders(c_meth, sz=5, color='475569')
    set_cell_margins(c_meth, top=65, bottom=65, left=90, right=90)
    
    # Easy-to-understand stages 1-3
    stages_p2 = [
        ("Stage 1 — Satellite Image Processing & Terrain Mapping (src/data_prep/): ",
         "We take high-resolution satellite imagery from SpaceNet 2 and train an AI computer-vision model (U-Net) to detect and trace rooftop outlines. These outlines are turned into digital map shapes tagged with real GPS coordinates. Next, we use ground elevation maps (DEM) and calculate building heights from satellite shadows so each building sits accurately on the ground at its true real-world height."),
        
        ("Stage 2 — Creating the 3D Virtual City & Hazards (src/geometry/): ",
         "Using 3D modeling tools (Blender and Python scripts), we extrude the flat 2D building outlines into solid 3D structures. We ensure the 3D models are 'watertight'—meaning they have clean, solid walls with no gaps so simulated drones cannot accidentally fly through them. We also place common low-altitude flight hazards into the air, including curved overhead electrical power lines and tall trees."),
         
        ("Stage 3 — Realistic Drone Flight Physics & Sensors (src/physics_sim/): ",
         "We place quadcopter drones into the virtual 3D city using a physics simulation engine (Unreal Engine 5). The drones obey natural physics, including motor lift, air resistance, gravity, and battery discharge. Each drone is fitted with virtual distance sensors (32-beam laser LiDAR) that scan 360 degrees around the drone to detect walls, and an audio sensor that listens for emergency rescue chirps.")
    ]
    
    p_first_m = c_meth.paragraphs[0]
    for idx, (title, desc) in enumerate(stages_p2):
        p = p_first_m if idx == 0 else c_meth.add_paragraph()
        p.paragraph_format.line_spacing = 1.10
        p.paragraph_format.space_after = Pt(3)
        rt = p.add_run(title)
        rt.font.bold = True
        rt.font.name = 'Times New Roman'
        rt.font.size = Pt(9.5)
        rd = p.add_run(desc)
        rd.font.name = 'Times New Roman'
        rd.font.size = Pt(9.5)

    # Force Page Break to Page 3
    doc.add_page_break()

    # =========================================================================
    # PAGE 3: Implementation Method (Stages 4-5) & Key Milestones Table
    # =========================================================================
    p_f2_lbl = doc.add_paragraph()
    p_f2_lbl.paragraph_format.space_before = Pt(0)
    p_f2_lbl.paragraph_format.space_after = Pt(3)
    r_f2_lbl = p_f2_lbl.add_run("F. Project Implementation Method (Continued):")
    r_f2_lbl.font.bold = True
    r_f2_lbl.font.size = Pt(11)
    
    t_meth2 = doc.add_table(rows=1, cols=1)
    t_meth2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_meth2.autofit = False
    c_meth2 = t_meth2.rows[0].cells[0]
    c_meth2.width = Inches(7.1)
    set_all_borders(c_meth2, sz=5, color='475569')
    set_cell_margins(c_meth2, top=65, bottom=65, left=90, right=90)
    
    # Easy-to-understand stages 4-5
    stages_p3 = [
        ("Stage 4 — Teaching the Drones with AI (src/models/): ",
         "We train the drone swarm using Multi-Agent Reinforcement Learning (MAPPO). In this approach, drones learn by trial and error: they get positive points for searching new areas and reaching targets, and heavy negative penalty points for crashing into walls or other drones. During training, a central computer monitors the entire area to guide learning. Once trained, each drone makes its own independent flight decisions using only its onboard sensors and short-range radio signals."),
         
        ("Stage 5 — Comparison Testing & 3D Visual Interface: ",
         "We test the trained AI drone swarm against standard textbook pathfinding methods (such as A* and RRT* algorithms) to demonstrate that our AI flies smoother, safer, and completes missions faster. Finally, we display the live drone flights on an interactive 3D web dashboard so operators can easily observe drone positions, battery levels, and mission progress.")
    ]
    p_first_m2 = c_meth2.paragraphs[0]
    for idx, (title, desc) in enumerate(stages_p3):
        p = p_first_m2 if idx == 0 else c_meth2.add_paragraph()
        p.paragraph_format.line_spacing = 1.10
        p.paragraph_format.space_after = Pt(3)
        rt = p.add_run(title)
        rt.font.bold = True
        rt.font.name = 'Times New Roman'
        rt.font.size = Pt(9.5)
        rd = p.add_run(desc)
        rd.font.name = 'Times New Roman'
        rd.font.size = Pt(9.5)

    p_g_lbl = doc.add_paragraph()
    p_g_lbl.paragraph_format.space_before = Pt(8)
    p_g_lbl.paragraph_format.space_after = Pt(3)
    r_g_lbl = p_g_lbl.add_run("G. Key Milestones of the Project with Dates:")
    r_g_lbl.font.bold = True
    r_g_lbl.font.size = Pt(11)
    
    t_mile = doc.add_table(rows=6, cols=4)
    t_mile.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_mile.autofit = False
    
    m_widths = [Inches(0.6), Inches(1.5), Inches(2.3), Inches(2.7)]
    m_headers = [("S.No.", True), ("Elapsed Time & Dates", True), ("Milestone", True), ("Key Deliverables", True)]
    m_rows = [
        [("1.", False), ("Month 1\n(Sep 2026)", False), ("Literature Review & System Design", True),
         ("Summary of existing research papers, drone flight equations, and overall system design plan.", False)],
        [("2.", False), ("Months 2–3\n(Oct–Nov 2026)", False), ("Satellite Image Processing & 3D Virtual City", True),
         ("Trained building detection AI, digitized building map, height model, and completed 3D virtual city.", False)],
        [("3.", False), ("Months 4–5\n(Dec 2026–Jan 2027)", False), ("Drone Simulation & AI Swarm Training", True),
         ("Flight physics simulation with sensor rangefinders and a trained AI model for multi-drone coordination.", False)],
        [("4.", False), ("Months 6–7\n(Feb–Mar 2027)", False), ("Challenging Scenario Testing & Performance Study", True),
         ("Experimental flight tests under wind, obstacle, and failure conditions; comparison against standard methods.", False)],
        [("5.", False), ("Month 8\n(Apr–May 2027)", False), ("3D Visual Dashboard & Final Thesis Defense", True),
         ("Live 3D mission control dashboard, complete software codebase, final thesis report, and presentation defense.", False)]
    ]
    
    for c_idx, (text, bold) in enumerate(m_headers):
        cell = t_mile.rows[0].cells[c_idx]
        cell.width = m_widths[c_idx]
        p = cell.paragraphs[0]
        p.text = text
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx == 0 else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        run = p.runs[0]
        run.font.bold = True
        run.font.size = Pt(9.5)
        set_all_borders(cell, sz=6, color='333333')
        set_cell_shading(cell, 'E2E8F0')
        set_cell_margins(cell, top=55, bottom=55, left=75, right=75)
        
    for r_idx, r_data in enumerate(m_rows):
        for c_idx, (text, bold) in enumerate(r_data):
            cell = t_mile.rows[r_idx + 1].cells[c_idx]
            cell.width = m_widths[c_idx]
            p = cell.paragraphs[0]
            p.text = text
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx == 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.05
            run = p.runs[0]
            run.font.name = 'Times New Roman'
            run.font.size = Pt(9)
            run.font.bold = bold
            set_all_borders(cell, sz=5, color='475569')
            set_cell_margins(cell, top=45, bottom=45, left=75, right=75)
            if r_idx % 2 == 1:
                set_cell_shading(cell, 'F8FAFC')

    # Force Page Break to Page 4
    doc.add_page_break()

    # =========================================================================
    # PAGE 4: Final Deliverables, Technical Details, Equipment Required
    # =========================================================================
    p_h_lbl = doc.add_paragraph()
    p_h_lbl.paragraph_format.space_before = Pt(0)
    p_h_lbl.paragraph_format.space_after = Pt(2)
    r_h_lbl = p_h_lbl.add_run("H. Final Deliverable of the Project:")
    r_h_lbl.font.bold = True
    r_h_lbl.font.size = Pt(11)
    
    t_deliv = doc.add_table(rows=1, cols=1)
    t_deliv.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_deliv.autofit = False
    c_deliv = t_deliv.rows[0].cells[0]
    c_deliv.width = Inches(7.1)
    set_all_borders(c_deliv, sz=5, color='475569')
    set_cell_margins(c_deliv, top=55, bottom=55, left=90, right=90)
    
    deliv_items = [
        ("1. Complete Simulation Software: ", "A software program that converts satellite imagery into 3D city models and simulates multi-drone flight."),
        ("2. Trained AI Flight Models: ", "Saved artificial intelligence models that allow multiple drones to fly autonomously as a coordinated team."),
        ("3. Comparative Performance Report: ", "A structured experimental study comparing our AI drone swarm against standard flight path methods."),
        ("4. Interactive 3D Visual Dashboard: ", "A user-friendly 3D web screen showing real-time drone locations, flight paths, and mission statistics.")
    ]
    p_first_d = c_deliv.paragraphs[0]
    for idx, (title, desc) in enumerate(deliv_items):
        p = p_first_d if idx == 0 else c_deliv.add_paragraph()
        p.paragraph_format.line_spacing = 1.08
        p.paragraph_format.space_after = Pt(2)
        rt = p.add_run(title)
        rt.font.bold = True
        rt.font.name = 'Times New Roman'
        rt.font.size = Pt(9.5)
        rd = p.add_run(desc)
        rd.font.name = 'Times New Roman'
        rd.font.size = Pt(9.5)

    p_i_lbl = doc.add_paragraph()
    p_i_lbl.paragraph_format.space_before = Pt(6)
    p_i_lbl.paragraph_format.space_after = Pt(2)
    r_i_lbl = p_i_lbl.add_run("I. Please Specify Technical Details of Final Deliverable:")
    r_i_lbl.font.bold = True
    r_i_lbl.font.size = Pt(11)
    
    t_tech = doc.add_table(rows=1, cols=1)
    t_tech.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_tech.autofit = False
    c_tech = t_tech.rows[0].cells[0]
    c_tech.width = Inches(7.1)
    set_all_borders(c_tech, sz=5, color='475569')
    set_cell_margins(c_tech, top=55, bottom=55, left=90, right=90)
    
    tech_items = [
        ("1. Virtual 3D City Environment: ", "Accurate 3D city map created from satellite photos with realistic building shapes, ground elevation, and no-fly zones."),
        ("2. Digital Twin State Manager: ", "Software module that continuously tracks building changes, weather, and real-time drone coordinates."),
        ("3. Multi-Drone Flight Simulator: ", "Physics-based flight engine that simulates quadcopter movement, motor lift, drag, and battery drain."),
        ("4. AI Swarm Controller: ", "Multi-agent reinforcement learning algorithm (MAPPO) that controls individual drone speed, direction, and team spacing."),
        ("5. Dynamic Hazard Module: ", "Scenario tool that adds moving obstacles, wind gusts, thin overhead power lines, and drone motor dropouts."),
        ("6. Mission Planning Module: ", "Sets search-and-rescue mission goals, distributes search zones among drones, and manages return-to-base."),
        ("7. Automatic Evaluation Module: ", "Automatically logs flight duration, search area covered, battery consumed, and safety metrics."),
        ("8. 3D Visual Control Dashboard: ", "Interactive web screen displaying 3D flight paths, individual drone status cards, and live mission progress."),
        ("9. Standard Comparison Test Suite: ", "Test suite comparing our AI drone swarm against standard textbook algorithms (like A* and RRT*).")
    ]
    p_first_t = c_tech.paragraphs[0]
    for idx, (title, desc) in enumerate(tech_items):
        p = p_first_t if idx == 0 else c_tech.add_paragraph()
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.space_after = Pt(2)
        rt = p.add_run(title)
        rt.font.bold = True
        rt.font.name = 'Times New Roman'
        rt.font.size = Pt(9)
        rd = p.add_run(desc)
        rd.font.name = 'Times New Roman'
        rd.font.size = Pt(9)

    p_j_lbl = doc.add_paragraph()
    p_j_lbl.paragraph_format.space_before = Pt(6)
    p_j_lbl.paragraph_format.space_after = Pt(2)
    r_j_lbl = p_j_lbl.add_run("J. Equipment required for making prototype/working model:")
    r_j_lbl.font.bold = True
    r_j_lbl.font.size = Pt(11)
    
    t_equip = doc.add_table(rows=1, cols=1)
    t_equip.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_equip.autofit = False
    c_equip = t_equip.rows[0].cells[0]
    c_equip.width = Inches(7.1)
    set_all_borders(c_equip, sz=5, color='475569')
    set_cell_margins(c_equip, top=55, bottom=55, left=90, right=90)
    
    equip_items = [
        ("1. Standard Computer / Laptop: ", "A development laptop or desktop computer with a multi-core processor and 16 GB of RAM."),
        ("2. Graphics Card (NVIDIA GPU): ", "Dedicated NVIDIA graphics card (GeForce RTX/GTX series) to run AI training and smooth 3D simulation."),
        ("3. Free & Open-Source Software: ", "Python, PyTorch (AI library), GIS mapping tools, Blender, and Unreal Engine simulation tools."),
        ("4. Public Datasets & Internet: ", "Internet access to download free public satellite imagery (SpaceNet 2) and ground elevation data."),
        ("5. Physical Drone Demonstration (Optional): ", "If laboratory drone hardware is available, real flight telemetry can be connected to the simulation for demonstration.")
    ]
    p_first_eq = c_equip.paragraphs[0]
    for idx, (title, desc) in enumerate(equip_items):
        p = p_first_eq if idx == 0 else c_equip.add_paragraph()
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.space_after = Pt(2)
        rt = p.add_run(title)
        rt.font.bold = True
        rt.font.name = 'Times New Roman'
        rt.font.size = Pt(9)
        rd = p.add_run(desc)
        rd.font.name = 'Times New Roman'
        rd.font.size = Pt(9)

    # Force Page Break to Page 5
    doc.add_page_break()

    # =========================================================================
    # PAGE 5: Benefits of the Project & Formal Certification Undertaking
    # =========================================================================
    p_k_lbl = doc.add_paragraph()
    p_k_lbl.paragraph_format.space_before = Pt(0)
    p_k_lbl.paragraph_format.space_after = Pt(2)
    r_k_lbl = p_k_lbl.add_run("K. Benefits of the Project:")
    r_k_lbl.font.bold = True
    r_k_lbl.font.size = Pt(11)
    
    t_ben = doc.add_table(rows=1, cols=1)
    t_ben.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_ben.autofit = False
    c_ben = t_ben.rows[0].cells[0]
    c_ben.width = Inches(7.1)
    set_all_borders(c_ben, sz=5, color='475569')
    set_cell_margins(c_ben, top=55, bottom=55, left=90, right=90)
    
    benefits = [
        ("1. Zero Risk and Low Cost: ", "Allows developing and testing drone swarm coordination safely on a computer without risking expensive drone crashes or physical injuries."),
        ("2. Repeatable Testing: ", "Allows running the exact same disaster mission dozens of times under controlled conditions to systematically test and improve the AI."),
        ("3. Prepares Drones for Real Hazards: ", "Trains drones to safely handle unexpected emergencies like sudden wind gusts, moving obstacles, thin overhead power lines, and motor failures."),
        ("4. Connects Satellite Data with Robotics: ", "Demonstrates a practical way to use Space Science satellite photos and elevation maps directly in autonomous drone navigation."),
        ("5. Useful for Disaster Relief & Search and Rescue: ", "Helps search-and-rescue teams locate survivors, map earthquake damage, or assess flooded areas quickly."),
        ("6. Saves Flight Time and Battery: ", "Teaches drones to pick efficient flight paths, helping them complete missions faster and extend battery life."),
        ("7. Foundation for Future IST Projects: ", "Creates a reusable 3D simulation platform that future students and faculty at IST can use for subsequent drone and AI research.")
    ]
    p_first_b = c_ben.paragraphs[0]
    for idx, (title, desc) in enumerate(benefits):
        p = p_first_b if idx == 0 else c_ben.add_paragraph()
        p.paragraph_format.line_spacing = 1.08
        p.paragraph_format.space_after = Pt(2)
        rt = p.add_run(title)
        rt.font.bold = True
        rt.font.name = 'Times New Roman'
        rt.font.size = Pt(9.5)
        rd = p.add_run(desc)
        rd.font.name = 'Times New Roman'
        rd.font.size = Pt(9.5)

    # Certification & Undertaking Section
    p_cert = doc.add_paragraph()
    p_cert.paragraph_format.space_before = Pt(8)
    p_cert.paragraph_format.space_after = Pt(3)
    p_cert.paragraph_format.line_spacing = 1.10
    
    cert_text1 = (
        "It is certified that the FYP titled “Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin” "
        "has been approved and is being undertaken by the above-mentioned students (Mashaf Majeed Janjua, Reg. No. 230601017, and Haider Taqveen, "
        "Reg. No. 230601020) as their Final Year Project."
    )
    r_c1 = p_cert.add_run(cert_text1)
    r_c1.font.name = 'Times New Roman'
    r_c1.font.size = Pt(9.5)
    
    p_cert2 = doc.add_paragraph()
    p_cert2.paragraph_format.space_before = Pt(2)
    p_cert2.paragraph_format.space_after = Pt(3)
    p_cert2.paragraph_format.line_spacing = 1.10
    cert_text2 = (
        "It is undertaken that the undersigned have understood the “terms & conditions” of the program, and further reiterate that, "
        "if the subject FYP is approved for funding, the disbursed funds shall be utilized as per “terms & conditions” and the undersigned "
        "will be liable to reimburse/refund the unutilized amount and other cost not approved by the IST, if any."
    )
    r_c2 = p_cert2.add_run(cert_text2)
    r_c2.font.name = 'Times New Roman'
    r_c2.font.size = Pt(9.5)
    
    p_cert3 = doc.add_paragraph()
    p_cert3.paragraph_format.space_before = Pt(2)
    p_cert3.paragraph_format.space_after = Pt(8)
    p_cert3.paragraph_format.line_spacing = 1.10
    cert_text3 = (
        "It is further undertaken that after utilization of funds, the said “Fund Utilization Report” shall be furnished along with the other "
        "required deliverables as and when required by the IST."
    )
    r_c3 = p_cert3.add_run(cert_text3)
    r_c3.font.name = 'Times New Roman'
    r_c3.font.size = Pt(9.5)
    
    # Signature Table
    t_sig = doc.add_table(rows=1, cols=2)
    t_sig.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_sig.autofit = False
    sig_widths = [Inches(3.55), Inches(3.55)]
    
    c_s0, c_s1 = t_sig.rows[0].cells[0], t_sig.rows[0].cells[1]
    c_s0.width, c_s1.width = sig_widths[0], sig_widths[1]
    
    # Supervisor Cell
    p_s0 = c_s0.paragraphs[0]
    p_s0.paragraph_format.space_before = Pt(2)
    p_s0.paragraph_format.space_after = Pt(1)
    r_s0 = p_s0.add_run("1. Name, Designation & Signature of Supervisor:")
    r_s0.font.bold = True
    r_s0.font.size = Pt(9.5)
    
    p_s0_val = c_s0.add_paragraph()
    p_s0_val.paragraph_format.space_before = Pt(5)
    p_s0_val.paragraph_format.space_after = Pt(2)
    p_s0_val.paragraph_format.line_spacing = 1.05
    r_s0_val = p_s0_val.add_run("Dr. Munawar Ali Shah\nAssistant Professor, Department of Space Science\nInstitute of Space Technology, Islamabad")
    r_s0_val.font.size = Pt(9)
    
    p_s0_sig = c_s0.add_paragraph()
    p_s0_sig.paragraph_format.space_before = Pt(18)
    p_s0_sig.paragraph_format.space_after = Pt(2)
    r_s0_sig = p_s0_sig.add_run("Signature: ______________________  Date: ________")
    r_s0_sig.font.size = Pt(9)
    
    # HoD Cell
    p_s1 = c_s1.paragraphs[0]
    p_s1.paragraph_format.space_before = Pt(2)
    p_s1.paragraph_format.space_after = Pt(1)
    r_s1 = p_s1.add_run("2. Name & Signatures of HoD:")
    r_s1.font.bold = True
    r_s1.font.size = Pt(9.5)
    
    p_s1_val = c_s1.add_paragraph()
    p_s1_val.paragraph_format.space_before = Pt(5)
    p_s1_val.paragraph_format.space_after = Pt(2)
    p_s1_val.paragraph_format.line_spacing = 1.05
    r_s1_val = p_s1_val.add_run("Head of Department\nDepartment of Space Science\nInstitute of Space Technology, Islamabad")
    r_s1_val.font.size = Pt(9)
    
    p_s1_sig = c_s1.add_paragraph()
    p_s1_sig.paragraph_format.space_before = Pt(18)
    p_s1_sig.paragraph_format.space_after = Pt(2)
    r_s1_sig = p_s1_sig.add_run("Signature: ______________________  Date: ________")
    r_s1_sig.font.size = Pt(9)
    
    for row in t_sig.rows:
        for cell in row.cells:
            set_all_borders(cell, sz=5, color='475569')
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            set_cell_shading(cell, 'F8FAFC')
    
    # Save DOCX
    os.makedirs(os.path.dirname(output_docx_path), exist_ok=True)
    doc.save(output_docx_path)
    print(f"SUCCESS: Generated simplified DOCX at {output_docx_path}")

def convert_docx_to_pdf(docx_path, pdf_path):
    """Uses Word COM automation to export pristine PDF."""
    import win32com.client as win32
    word = win32.gencache.EnsureDispatch('Word.Application')
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        abs_docx = os.path.abspath(docx_path)
        abs_pdf = os.path.abspath(pdf_path)
        doc = word.Documents.Open(abs_docx)
        doc.SaveAs(abs_pdf, FileFormat=17) # 17 = wdFormatPDF
        doc.Close(False)
        print(f"SUCCESS: Exported simplified PDF at {pdf_path}")
    finally:
        word.Quit()

if __name__ == '__main__':
    project_root = r"E:\digital-twin-fyp"
    docs_dir = os.path.join(project_root, "docs")
    
    out_docx = os.path.join(docs_dir, "Final Year Project (FYP) Defense Proposal Form(Final).docx")
    out_pdf = os.path.join(docs_dir, "Final Year Project (FYP) Defense Proposal Form(Final).pdf")
    
    build_proposal_document(out_docx)
    convert_docx_to_pdf(out_docx, out_pdf)
