# Institute of Space Technology
### Department of Space Science · Dean Office
**Form No:** `IST-Dean-F-23/00` · **FYP Selection Form** · **Issue Date:** Fall 2026  
**Policy:** Grading Policy on Final Year Projects

---

# Final Year Project (FYP) Defense Proposal Form

## 1. University / Institute Detail

| Parameter | Details | Parameter | Details |
| :--- | :--- | :--- | :--- |
| **Name of University / Institution:** | Institute of Space Technology (IST) | **Physical Address:** | 1, Islamabad Highway, Islamabad, 44000, Pakistan |
| **Telephone & Fax No:** | +92-51-9075100<br>+92-51-9273310 | **Department Name:** | Department of Space Science |
| **City:** | Islamabad | **Province:** | Islamabad Capital Territory (ICT) |

---

## 2. Nominated Project Details

| Parameter | Details | Parameter | Details |
| :--- | :--- | :--- | :--- |
| **Project Supervisor Name & Designation:** | **Dr. Munawar Ali Shah**<br>Assistant Professor | **Contact Details:** | `munawar.shah@ist.edu.pk` |
| **Project Supervisor Qualification:** | Ph.D. in Geodesy and GNSS | **No. of Publications of Supervisor:** | Over 100 peer-reviewed journal & conference publications |
| **Students Name(s):** | 1. **Mashaf Majeed Janjua**<br>2. **Haider Taqveen** | **Students Mobile No:** | 1. +92-320-5409300<br>2. +92-325-9514052 |
| **Students CGPA:** | 1. 2.31<br>2. 2.65 | **Students Email:** | 1. `230601017@ist.edu.pk`<br>2. `230601020@ist.edu.pk` |
| **Degree Program / Title:** | BS Space Science | **Area of Specialization:** | Remote Sensing & GIS (RS/GIS) |

---

## 3. Final Year Project Details

### A. Project Title
**Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin**

### B. Project Start Date
**September 01, 2026** (Fall Semester 2026)

### C. Project Finish Date
**June 30, 2027** (Spring Semester 2027)

---

### D. Project Summary *(less than 200 words)*
> Drones are increasingly vital for disaster management, search and rescue, and environmental monitoring. However, flying a team of multiple autonomous drones (a swarm) in crowded cities is challenging because drones can easily collide with buildings, power lines, or each other. Testing real drones in physical cities is also expensive and dangerous. 
> 
> This project creates a **'Geospatial Digital Twin'**—a realistic 3D computer model of a real city built directly from satellite images and ground elevation data. Inside this virtual world, we use Artificial Intelligence (Multi-Agent Reinforcement Learning) to teach a team of drones how to fly together autonomously. The drones learn by practice how to coordinate search patterns, avoid obstacles like buildings and overhead wires, and locate emergency rescue sound beacons without human pilots. 
> 
> We evaluate swarm performance by measuring mission completion time, area coverage, battery efficiency, and collision-free safety. Finally, an interactive 3D computer dashboard is developed so mission operators can observe the drones and track flight telemetry in real time.
> 
> *[Word Count: 161 words | Verified strictly < 200 words]*

---

### E. Project Objectives
1. **Build a 3D Virtual City (Digital Twin):** Automatically convert high-resolution optical satellite imagery and elevation data into a realistic 3D virtual environment with accurate building shapes, terrain heights, and low-altitude hazards such as power lines.
2. **Simulate Realistic Drone Flight:** Simulate multiple quadcopter drones with realistic physical movement, motor thrust, battery energy limits, distance-measuring laser sensors (LiDAR), and emergency sound detectors.
3. **Train AI for Drone Teamwork:** Train an artificial intelligence framework (Multi-Agent Deep Reinforcement Learning) where drones learn to fly together as a cooperative team without colliding with obstacles or each other.
4. **Test Under Challenging Scenarios:** Test the drone swarm under difficult disaster conditions, including moving obstacles, windy weather, single-drone motor failures, and weak communication signals.
5. **Measure and Compare Performance:** Evaluate swarm success using clear practical metrics (search speed, area covered, battery usage, and zero crashes) and compare the AI against traditional flight navigation methods.
6. **Build a 3D Mission Control Screen:** Develop an interactive 3D visual dashboard where operators can see drone locations, watch live flight paths, and monitor mission progress in real time.

---

### F. Project Implementation Method

* **Stage 1 — Satellite Image Processing & Terrain Mapping (`src/data_prep/`):**  
  We take high-resolution satellite imagery from SpaceNet 2 and train an AI computer-vision model (U-Net) to detect and trace rooftop outlines. These outlines are turned into digital map shapes tagged with real GPS coordinates. Next, we use ground elevation maps (DEM) and calculate building heights from satellite shadows so each building sits accurately on the ground at its true real-world height.

* **Stage 2 — Creating the 3D Virtual City & Hazards (`src/geometry/`):**  
  Using 3D modeling tools (Blender and Python scripts), we extrude the flat 2D building outlines into solid 3D structures. We ensure the 3D models are "watertight"—meaning they have clean, solid walls with no gaps so simulated drones cannot accidentally fly through them. We also place common low-altitude flight hazards into the air, including curved overhead electrical power lines and tall trees.

* **Stage 3 — Realistic Drone Flight Physics & Sensors (`src/physics_sim/`):**  
  We place quadcopter drones into the virtual 3D city using a physics simulation engine (Unreal Engine 5). The drones obey natural physics, including motor lift, air resistance, gravity, and battery discharge. Each drone is fitted with virtual distance sensors (32-beam laser LiDAR) that scan 360 degrees around the drone to detect walls, and an audio sensor that listens for emergency rescue chirps.

* **Stage 4 — Teaching the Drones with AI (`src/models/`):**  
  We train the drone swarm using Multi-Agent Reinforcement Learning (MAPPO). In this approach, drones learn by trial and error: they get positive points for searching new areas and reaching targets, and heavy negative penalty points for crashing into walls or other drones. During training, a central computer monitors the entire area to guide learning. Once trained, each drone makes its own independent flight decisions using only its onboard sensors and short-range radio signals.

* **Stage 5 — Comparison Testing & 3D Visual Interface:**  
  We test the trained AI drone swarm against standard textbook pathfinding methods (such as A* and RRT* algorithms) to demonstrate that our AI flies smoother, safer, and completes missions faster. Finally, we display the live drone flights on an interactive 3D web dashboard so operators can easily observe drone positions, battery levels, and mission progress.

---

### G. Key Milestones of the Project with Dates

| S.No. | Elapsed Time & Dates | Milestone | Key Deliverables |
| :---: | :--- | :--- | :--- |
| **1.** | **Month 1**<br>*(Sep 2026)* | **Literature Review & System Design** | Summary of existing research papers, drone flight equations, and overall system design plan. |
| **2.** | **Months 2–3**<br>*(Oct–Nov 2026)* | **Satellite Image Processing & 3D Virtual City** | Trained building detection AI, digitized building map, height model, and completed 3D virtual city. |
| **3.** | **Months 4–5**<br>*(Dec 2026–Jan 2027)* | **Drone Simulation & AI Swarm Training** | Flight physics simulation with sensor rangefinders and a trained AI model for multi-drone coordination. |
| **4.** | **Months 6–7**<br>*(Feb–Mar 2027)* | **Challenging Scenario Testing & Performance Study** | Experimental flight tests under wind, obstacle, and failure conditions; comparison against standard methods. |
| **5.** | **Month 8**<br>*(Apr–May 2027)* | **3D Visual Dashboard & Final Thesis Defense** | Live 3D mission control dashboard, complete software codebase, final thesis report, and presentation defense. |

---

### H. Final Deliverable of the Project
1. **Complete Simulation Software:** A software program that converts satellite imagery into 3D city models and simulates multi-drone flight.
2. **Trained AI Flight Models:** Saved artificial intelligence models that allow multiple drones to fly autonomously as a coordinated team.
3. **Comparative Performance Report:** A structured experimental study comparing our AI drone swarm against standard flight path methods.
4. **Interactive 3D Visual Dashboard:** A user-friendly 3D web screen showing real-time drone locations, flight paths, and mission statistics.

---

### I. Please Specify Technical Details of Final Deliverable
1. **Virtual 3D City Environment:** Accurate 3D city map created from satellite photos with realistic building shapes, ground elevation, and no-fly zones.
2. **Digital Twin State Manager:** Software module that continuously tracks building changes, weather, and real-time drone coordinates.
3. **Multi-Drone Flight Simulator:** Physics-based flight engine that simulates quadcopter movement, motor lift, drag, and battery drain.
4. **AI Swarm Controller:** Multi-agent reinforcement learning algorithm (MAPPO) that controls individual drone speed, direction, and team spacing.
5. **Dynamic Hazard Module:** Scenario tool that adds moving obstacles, wind gusts, thin overhead power lines, and drone motor dropouts.
6. **Mission Planning Module:** Sets search-and-rescue mission goals, distributes search zones among drones, and manages return-to-base.
7. **Automatic Evaluation Module:** Automatically logs flight duration, search area covered, battery consumed, and safety metrics.
8. **3D Visual Control Dashboard:** Interactive web screen displaying 3D flight paths, individual drone status cards, and live mission progress.
9. **Standard Comparison Test Suite:** Test suite comparing our AI drone swarm against standard textbook algorithms (like A* and RRT*).

---

### J. Equipment Required for Making Prototype / Working Model
1. **Standard Computer / Laptop:** A development laptop or desktop computer with a multi-core processor and 16 GB of RAM.
2. **Graphics Card (NVIDIA GPU):** Dedicated NVIDIA graphics card (GeForce RTX/GTX series) to run AI training and smooth 3D simulation.
3. **Free & Open-Source Software:** Python, PyTorch (AI library), GIS mapping tools, Blender, and Unreal Engine simulation tools.
4. **Public Datasets & Internet:** Internet access to download free public satellite imagery (SpaceNet 2) and ground elevation data.
5. **Physical Drone Demonstration (Optional):** If laboratory drone hardware is available, real flight telemetry can be connected to the simulation for demonstration.

---

### K. Benefits of the Project
1. **Zero Risk and Low Cost:** Allows developing and testing drone swarm coordination safely on a computer without risking expensive drone crashes or physical injuries.
2. **Repeatable Testing:** Allows running the exact same disaster mission dozens of times under controlled conditions to systematically test and improve the AI.
3. **Prepares Drones for Real Hazards:** Trains drones to safely handle unexpected emergencies like sudden wind gusts, moving obstacles, thin overhead power lines, and motor failures.
4. **Connects Satellite Data with Robotics:** Demonstrates a practical way to use Space Science satellite photos and elevation maps directly in autonomous drone navigation.
5. **Useful for Disaster Relief & Search and Rescue:** Helps search-and-rescue teams locate survivors, map earthquake damage, or assess flooded areas quickly.
6. **Saves Flight Time and Battery:** Teaches drones to pick efficient flight paths, helping them complete missions faster and extend battery life.
7. **Foundation for Future IST Projects:** Creates a reusable 3D simulation platform that future students and faculty at IST can use for subsequent drone and AI research.

---

## 4. Certification & Formal Undertaking

It is certified that the FYP titled **“Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin”** has been approved and is being undertaken by the above-mentioned students (**Mashaf Majeed Janjua**, Reg. No. **230601017**, and **Haider Taqveen**, Reg. No. **230601020**) as their Final Year Project.

It is undertaken that the undersigned have understood the **“terms & conditions”** of the program, and further reiterate that, if the subject FYP is approved for funding, the disbursed funds shall be utilized as per **“terms & conditions”** and the undersigned will be liable to reimburse/refund the unutilized amount and other cost not approved by the IST, if any.

It is further undertaken that after utilization of funds, the said **“Fund Utilization Report”** shall be furnished along with the other required deliverables as and when required by the IST.

<br>

| 1. Name, Designation & Signature of Supervisor | 2. Name & Signatures of HoD |
| :--- | :--- |
| **Dr. Munawar Ali Shah**<br>Assistant Professor, Department of Space Science<br>Institute of Space Technology, Islamabad<br><br><br>Signature: __________________________ &nbsp;&nbsp;&nbsp; Date: ________ | **Head of Department**<br>Department of Space Science<br>Institute of Space Technology, Islamabad<br><br><br>Signature: __________________________ &nbsp;&nbsp;&nbsp; Date: ________ |
