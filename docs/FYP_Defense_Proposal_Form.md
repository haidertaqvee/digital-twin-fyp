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

### D. Project Summary *(strictly < 200 words)*
> Coordinating autonomous Unmanned Aerial Vehicle (UAV) swarms for search and rescue, disaster assessment, and tactical surveillance in dense urban topographies presents severe trajectory and collision challenges. Physical multi-drone testing is prohibitively expensive, safety-critical, and non-repeatable across hazardous disaster events. This project develops an AI-enabled Geospatial Digital Twin that reconstructs simulation-ready, watertight 3D operational environments from sub-meter optical satellite imagery (SpaceNet 2) and normalized Digital Surface Models (nDSM). 
> 
> Operating within this physics-accurate twin, a Multi-Agent Deep Reinforcement Learning (MADRL) architecture—leveraging Multi-Agent PPO (MAPPO) with Centralized Training and Decentralized Execution (CTDE)—is trained to coordinate 6-DOF autonomous UAV swarms. Drone agents utilize simulated 32-beam LiDAR and GPS-degraded kinematic state estimation to learn cooperative area coverage, dynamic obstacle avoidance, catenary powerline traversal, and acoustic beacon localization. Swarm performance is quantitatively benchmarked against classical 3D A* and decentralized RRT* algorithms across mission completion time, energy efficiency, and safety margins. A real-time 3D mission control HUD provides telemetry observation and spatial analytics for mission commanders.
> 
> *[Exact Word Count: 159 words | Verified strictly < 200 words]*

---

### E. Project Objectives
1. **Automated 3D Digital Twin Reconstruction:** Develop an automated geospatial reconstruction toolchain converting high-resolution optical satellite imagery (SpaceNet 2) and DEM topographic elevations into watertight, collision-ready 3D manifold meshes with localized micro-hazards (catenary powerlines and vegetation volumes).
2. **6-DOF Aerodynamic Swarm Formulation:** Formulate and simulate 6-DOF quadrotor kinematic and aerodynamic agent models subject to rotor thrust limits, gyroscopic drag, 32-beam LiDAR emulation, and acoustic rescue beacon chirps.
3. **Multi-Agent Reinforcement Learning Engine:** Design and train a scalable Multi-Agent Deep Reinforcement Learning (MADRL) framework based on Multi-Agent PPO (MAPPO) with Centralized Training and Decentralized Execution (CTDE) for cooperative swarm navigation.
4. **Dynamic Disaster Scenario Emulation:** Simulate stochastic, high-entropy environmental conditions, including moving obstacles, catenary wire entanglements, wind shear perturbations, individual motor failures, and intermittent communication loss.
5. **Quantitative Benchmarking & Safety Evaluation:** Benchmark swarm flight metrics against classical centralized 3D A* and decentralized RRT* baselines across mission completion duration, area coverage rate, collision frequency, and energy consumption.
6. **Tactical Mission Control Interface:** Construct an interactive 3D WebGL tactical HUD and mission telemetry dashboard for real-time visualization of UAV trajectories, battery states, sensor feeds, and mission progress.

---

### F. Project Implementation Method

* **Stage 1 — Satellite Semantic Extraction & Topography (`src/data_prep/`):**  
  The framework consumes 0.3m optical satellite imagery from SpaceNet 2 Las Vegas. A deep convolutional U-Net with ResNet-34 backbone is fine-tuned to extract building footprints (test IoU 0.8062, F1 0.8927). Building masks are vectorized into georeferenced polygons in WGS84 (EPSG:4326). Ground elevations are queried from AWS Terrarium DEM tiles using sub-millisecond bilinear interpolation, while normalized Digital Surface Models (nDSM) and solar shadow trigonometry validate structural building heights.

* **Stage 2 — 3D Digital Twin Mesh Manifolding & Micro-Hazards (`src/geometry/`):**  
  Extracted polygon cadastre footprints are converted into watertight, manifold 3D polygon meshes via automated Blender Python (`bpy`) extrusion and polygon triangulation. Critical micro-hazards are procedurally modeled into the airspace: catenary powerlines using hyperbolic cosine equations ($y = a \cdot [\cosh(x/a) - 1]$) between transmission poles, and vegetation canopy exclusion zones using SAVI vegetation masks.

* **Stage 3 — Real-Time Physics Simulator & 6-DOF UAV Kinematics (`src/physics_sim/`):**  
  The reconstructed geospatial environment is imported into a real-time simulation engine (Unreal Engine 5 Chaos Physics / lightweight headless 3D simulation). Heterogeneous quadrotor agents are modeled under full 6-DOF rigid-body kinematics (rotor thrust, aerodynamic drag, gravitational torque, and battery energy discharge). Each UAV is instrumented with an emulated 32-beam spherical LiDAR rangefinder and an omnidirectional acoustic receiver detecting emergency chirps.

* **Stage 4 — Multi-Agent Deep Reinforcement Learning Swarm Engine (`src/models/`):**  
  Autonomous swarm coordination is governed by Multi-Agent Proximal Policy Optimization (MAPPO) with Centralized Training and Decentralized Execution (CTDE). During training, a centralized value network observes the global spatial state of the digital twin; during execution, decentralized actor networks generate continuous rotor velocity commands based strictly on local 32-beam LiDAR range vectors and inter-agent relative telemetry. A Pareto multi-objective reward function optimizes mission completion, formation cohesion, and collision avoidance.

* **Stage 5 — Benchmarking & Tactical Mission HUD:**  
  The converged MAPPO swarm policy is benchmarked against centralized 3D A* and decentralized RRT* algorithms under dynamic scenarios (moving obstacles, catenary powerlines, motor dropouts, and communication packet loss). An interactive WebGL 3D Mission Control HUD renders real-time UAV trajectories, telemetry cards, and quantitative safety reports.

---

### G. Key Milestones of the Project with Dates

| S.No. | Elapsed Time & Dates | Milestone | Key Deliverables |
| :---: | :--- | :--- | :--- |
| **1.** | **Month 1**<br>*(Sep 2026)* | **Literature Review, System Requirements & Mathematical Modeling** | Comprehensive literature review, 6-DOF kinematic formulations, and system architecture specification document. |
| **2.** | **Months 2–3**<br>*(Oct–Nov 2026)* | **Satellite Extraction Pipeline & 3D Geospatial Digital Twin** | Trained U-Net footprint segmentation model, vectorized building cadastre, nDSM height model, and automated watertight 3D mesh generator. |
| **3.** | **Months 4–5**<br>*(Dec 2026–Jan 2027)* | **Physics-Based Multi-UAV Simulation & MAPPO RL Training** | Multi-agent simulation engine with 32-beam LiDAR emulation, converged MAPPO policy weights, and acoustic beacon search behavior. |
| **4.** | **Months 6–7**<br>*(Feb–Mar 2027)* | **Dynamic Scenario Stress-Testing & Algorithmic Benchmarking** | Empirical test results across moving obstacles, wire entanglements, and UAV failures; quantitative comparisons vs 3D A* and RRT*. |
| **5.** | **Month 8**<br>*(Apr–May 2027)* | **Tactical HUD Integration, Final Demonstration & Thesis Defense** | Interactive 3D WebGL mission control interface, complete software repository, finalized BS Space Science thesis dissertation, and oral defense. |

---

### H. Final Deliverable of the Project
1. **End-to-End Software System:** Fully automated software toolchain for satellite building extraction, 3D mesh manifold reconstruction, and multi-agent flight simulation.
2. **Autonomous Swarm Policy Checkpoints:** Converged PyTorch neural network checkpoints implementing decentralized cooperative navigation and hazard avoidance.
3. **Quantitative Simulation & Comparative Study:** Comprehensive comparative benchmarking dataset validating swarm flight performance against 3D A* and decentralized RRT*.
4. **High-Fidelity Simulator & Tactical HUD:** 3D simulation environment and interactive WebGL Mission Control HUD for real-time mission telemetry and spatial analytics.

---

### I. Please Specify Technical Details of Final Deliverable
1. **Virtual Geospatial Environment:** Cadastre-grade 3D environment generated from SpaceNet 2 satellite tiles, georeferenced in WGS84 (EPSG:4326), featuring accurate building geometries, terrain topography, and restricted flight volumes.
2. **Digital Twin State Engine:** Real-time spatial state manager synchronizing environmental changes, multi-agent position histories, and dynamic threat boundaries.
3. **Multi-UAV Simulation Module:** Physics-based kinematic engine simulating heterogeneous quadrotor agents under 6-DOF rigid-body dynamics, aerodynamic rotor drag, and battery discharge curves.
4. **AI Swarm-Control Module:** MAPPO multi-agent reinforcement learning architecture utilizing Centralized Training with Decentralized Execution (CTDE) for collision-free cooperative navigation.
5. **Dynamic Scenario Generator:** Simulation module injecting moving obstacles, localized wind gusts, catenary wire obstacles, and UAV communication packet dropouts.
6. **Mission Management Module:** Mission coordinator managing search patterns, acoustic rescue beacon homing, formation tracking, and automated return-to-base protocols.
7. **Performance Evaluation Module:** Automated logging engine tracking mission completion duration, area coverage rate, collision frequency, and energy consumption (Wh).
8. **Tactical Visualization Interface:** Interactive 3D WebGL HUD rendering swarm trajectories, drone health telemetries, and operational status cycling.
9. **Experimental Benchmark Suite:** Standardized evaluation framework executing head-to-head performance comparisons against centralized 3D A* and decentralized RRT* algorithms.

---

### J. Equipment Required for Making Prototype / Working Model
1. **Development Workstation:** Standard research workstation or laptop equipped with a multi-core processor (Intel Core i7/i9 or AMD Ryzen) and 16+ GB RAM.
2. **GPU Compute Capability:** Dedicated NVIDIA GPU (GeForce RTX/GTX series, CUDA 12.x compatible) for accelerated deep neural network training and real-time 3D simulation physics.
3. **GIS & Simulation Software Toolchain:** Python 3.10+ virtual environment, PyTorch deep learning framework, GDAL/Rasterio/GeoPandas geospatial libraries, Blender 4.x (`bpy`), and Unreal Engine 5.4.
4. **Earth Observation Datasets & Connectivity:** High-speed internet connectivity for streaming AWS Terrarium DEM tiles and SpaceNet 2 satellite imagery.
5. **Hardware-in-the-Loop Demonstration (Optional):** An optional physical quadrotor or Pixhawk flight controller telemetry link may be incorporated for ground station telemetry playback if laboratory hardware is made available.

---

### K. Benefits of the Project
1. **Risk-Free, Low-Cost Swarm Development:** Enables rapid prototyping and verification of multi-UAV swarm control policies without incurring drone crash costs or flight-safety hazards.
2. **Scientific Repeatability:** Provides a deterministic, repeatable operational environment for rigorous scientific comparison across disparate multi-agent algorithms under identical environmental states.
3. **Robustness in High-Entropy & GPS-Degraded Environments:** Enables evaluation of swarm adaptability under communication outages, moving obstacles, micro-hazards (catenary powerlines), and individual agent motor failures.
4. **Direct Fusion of Space Science & Autonomous Robotics:** Demonstrates seamless integration of satellite remote sensing, photogrammetric DEMs, and GIS spatial analytics directly into autonomous robotic navigation pipelines.
5. **Search and Rescue (SAR) & Disaster Assessment:** Directly applicable to post-disaster reconnaissance (earthquake structural collapse, flood assessment, acoustic survivor locator homing).
6. **Quantitative Multi-Objective Benchmarking:** Establishes empirical baselines comparing cooperative reinforcement learning against classical centralized 3D A* and decentralized RRT* algorithms.
7. **Foundation for Physical Hardware-in-the-Loop (HIL):** Establishes standard MAVLink telemetry and control interfaces readily transferable to physical multi-UAV platforms in future research.

---

## 4. Certification & Formal Undertaking

It is certified that the FYP titled **“Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin”** has been approved and is being undertaken by the above-mentioned students (**Mashaf Majeed Janjua**, Reg. No. **230601017**, and **Haider Taqveen**, Reg. No. **230601020**) as their Final Year Project.

It is undertaken that the undersigned have understood the **“terms & conditions”** of the program, and further reiterate that, if the subject FYP is approved for funding, the disbursed funds shall be utilized as per **“terms & conditions”** and the undersigned will be liable to reimburse/refund the unutilized amount and other cost not approved by the IST, if any.

It is further undertaken that after utilization of funds, the said **“Fund Utilization Report”** shall be furnished along with the other required deliverables as and when required by the IST.

<br>

| 1. Name, Designation & Signature of Supervisor | 2. Name & Signatures of HoD |
| :--- | :--- |
| **Dr. Munawar Ali Shah**<br>Assistant Professor, Department of Space Science<br>Institute of Space Technology, Islamabad<br><br><br>Signature: __________________________ &nbsp;&nbsp;&nbsp; Date: ________ | **Head of Department**<br>Department of Space Science<br>Institute of Space Technology, Islamabad<br><br><br>Signature: __________________________ &nbsp;&nbsp;&nbsp; Date: ________ |
