# Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin

### Final Year Project Proposal — BS Space Science
**Department of Space Science, Institute of Space Technology (IST), Islamabad**  
**Authors / Team:** Haider Taqveen (Reg. No. 230601020), Mashaf Majeed (Reg. No. 230601017) · **Supervisor:** Dr. Munawar Ali Shah  
**Academic Year:** 2026–2027 · **Version:** 2.0 (Engineering Architecture Revision)  
**Repository:** `E:\digital-twin-fyp` · **Target Simulators:** Blender 4.x / Unreal Engine 5.4 (Chaos Physics)  

---

## Table of Contents

1. [Abstract](#1-abstract)
2. [Introduction & Problem Statement](#2-introduction--problem-statement)
   - 2.1 [Context & Motivation](#21-context--motivation)
   - 2.2 [Problem Statement](#22-problem-statement)
   - 2.3 [Research Questions](#23-research-questions)
3. [Aims & Measurable Objectives](#3-aims--measurable-objectives)
4. [Literature Review & Theoretical Background](#4-literature-review--theoretical-background)
   - 4.1 [Satellite Semantic Feature Extraction & Foundation Models](#41-satellite-semantic-feature-extraction--foundation-models)
   - 4.2 [Topographic Extraction, nDSM & Shadow Trigonometry](#42-topographic-extraction-ndsm--shadow-trigonometry)
   - 4.3 [Micro-Hazard Identification & Physical Modeling](#43-micro-hazard-identification--physical-modeling)
   - 4.4 [Industrial-Grade Geospatial Digital Twins (UE5 vs Traditional Simulators)](#44-industrial-grade-geospatial-digital-twins-ue5-vs-traditional-simulators)
   - 4.5 [Multi-Agent Deep Reinforcement Learning (MADRL) for UAV Swarms](#45-multi-agent-deep-reinforcement-learning-madrl-for-uav-swarms)
   - 4.6 [Identified Research Gap](#46-identified-research-gap)
5. [System Scope & Bounded Region Definition](#5-system-scope--bounded-region-definition)
6. [Methodology & Pipeline Architecture](#6-methodology--pipeline-architecture)
   - 6.1 [Stage 1 & 2: High-Precision Geospatial & Micro-Hazard Extraction](#61-stage-1--2-high-precision-geospatial--micro-hazard-extraction)
     - 6.1.1 [Branch A: Universal Instance Segmentation (Mask2Former + SAM 2 + DP Orthogonalization)](#611-branch-a-universal-instance-segmentation-mask2former--sam-2--dp-orthogonalization)
     - 6.1.2 [Branch B: Topography, nDSM & Shadow Trigonometric Validation](#612-branch-b-topography-ndsm--shadow-trigonometric-validation)
     - 6.1.3 [Branch C: Micro-Hazard Mapping (NDVI/SAVI Canopies & Catenary Powerlines)](#613-branch-c-micro-hazard-mapping-ndvisavi-canopies--catenary-powerlines)
   - 6.2 [Stage 3: Environment Compilation & Unreal Engine 5 Physics Sim](#62-stage-3-environment-compilation--unreal-engine-5-physics-sim)
     - 6.2.1 [Vector-to-Mesh Bridge & Blender Asset Optimization](#621-vector-to-mesh-bridge--blender-asset-optimization)
     - 6.2.2 [Unreal Engine 5 Ingestion & Chaos Physics Colliders](#622-unreal-engine-5-ingestion--chaos-physics-colliders)
   - 6.3 [Stage 4: Autonomous UAV Swarm Engine (MADRL Framework)](#63-stage-4-autonomous-uav-swarm-engine-madrl-framework)
     - 6.3.1 [6-DOF Quadrotor Dynamics & Flight Envelope](#631-6-dof-quadrotor-dynamics--flight-envelope)
     - 6.3.2 [Virtual Sensor Emulation (LiDAR & Swarm Telemetry)](#632-virtual-sensor-emulation-lidar--swarm-telemetry)
     - 6.3.3 [MAPPO Policy Architecture & Formulation](#633-mappo-policy-architecture--formulation)
     - 6.3.4 [Multi-Objective Reward Function Formulation](#634-multi-objective-reward-function-formulation)
7. [Data, Computational Infrastructure & Software Stack](#7-data-computational-infrastructure--software-stack)
8. [Comprehensive Evaluation Plan](#8-comprehensive-evaluation-plan)
   - 8.1 [Geospatial Extraction Benchmarks](#81-geospatial-extraction-benchmarks)
   - 8.2 [Physics Simulation & Collision Integrity](#82-physics-simulation--collision-integrity)
   - 8.3 [MADRL Swarm Navigation & Mission Metrics](#83-madrl-swarm-navigation--mission-metrics)
9. [Risk Assessment & Mitigation Matrix](#9-risk-assessment--mitigation-matrix)
10. [Work Plan, Milestone Schedule & Gantt Alignment](#10-work-plan-milestone-schedule--gantt-alignment)
    - 10.1 [Academic Phases & Milestones](#101-academic-phases--milestones)
    - 10.2 [Division of Responsibilities & Team Work Breakdown](#102-division-of-responsibilities--team-work-breakdown)
11. [Expected Academic Deliverables & Contributions](#11-expected-academic-deliverables--contributions)
12. [Ethical, Dual-Use & Environmental Considerations](#12-ethical-dual-use--environmental-considerations)
13. [References](#13-references)
14. [Appendices](#appendices)

---

## 1. Abstract

Autonomous Unmanned Aerial Vehicle (UAV) swarms operating in dense, GPS-degraded, or post-disaster urban environments face severe navigational hazards, including narrow urban canyons, unmapped tree canopies, and suspended power transmission lines. Training cooperative Multi-Agent Deep Reinforcement Learning (MADRL) policies directly in the physical world is prohibitively risky and cost-inefficient. Conversely, conventional synthetic robotics simulators rely on idealized, procedural environments that suffer from an insurmountable "sim-to-real" domain gap due to a total lack of grounding in real-world geographic morphology and physical clutter.

This BS Space Science Final Year Project presents **TerraTwin Swarm**, an end-to-end framework integrating remote sensing, automated 3D geometry reconstruction, and reinforcement learning. The system reconstructs a high-fidelity geospatial digital twin from sub-meter commercial satellite imagery (SpaceNet 2, Las Vegas) over a bounded urban corridor. The extraction methodology leverages a three-branch pipeline:
1. **Branch A:** Universal Transformer instance segmentation (**Mask2Former**) refined with the **Segment Anything Model 2 (SAM 2)** for sub-pixel boundary snapping, regularized via **Douglas-Peucker orthogonalization** into cadastre-grade polygons;
2. **Branch B:** Ground filtering applied to stereo Digital Surface Models (DSM) to compute Normalized Digital Surface Models (**nDSM**), cross-validated against solar shadow trigonometry ($h = L_{\text{shadow}} \cdot \tan \theta_s$) using ephemeris metadata;
3. **Branch C:** Environmental micro-hazard isolation separating tree canopies via Soil-Adjusted Vegetation Index (**SAVI**) and reconstructing overhead power transmission lines via **catenary curve physics** ($y = a \cdot \cosh(x/a) - a$).

Processed vector assets are optimized through automated Blender geometry pipelines and compiled into **Unreal Engine 5 (UE5)**, establishing an industrial-grade simulation environment equipped with **Chaos Physics colliders**. Within this geospatial twin, a cooperative swarm of quadrotors governed by 6-DOF kinematics and ray-cast LiDAR sensors is trained using **Multi-Agent Proximal Policy Optimization (MAPPO)**. The agents learn decentralized cooperative trajectory planning, collision avoidance, and acoustic beacon localization under severe aerodynamic and geometric constraints.

---

## 2. Introduction & Problem Statement

### 2.1 Context & Motivation

Urban aerial autonomy is transitioning from single, high-altitude UAV missions to distributed, low-altitude multi-UAV swarm operations. Critical applications—including post-seismic search and rescue (SAR), emergency medical payload delivery, and urban surveillance—require swarms to navigate through complex urban corridors below the building roofline. In these environments, standard Global Navigation Satellite System (GNSS) signals suffer from severe multipath interference, urban canyon blackouts, and complete loss of carrier lock.

To achieve autonomy without continuous GNSS availability, swarms must rely on onboard sensors (LiDAR, optical odometry) and learned spatial behaviors. MADRL offers a powerful framework for discovering decentralized cooperative policies: agents communicate locally, avoid mutual collisions, and coordinate search sweeps without requiring a central coordinator.

However, training MADRL algorithms requires millions of environmental interaction steps. Doing so on physical hardware results in frequent catastrophic crashes and hardware destruction. Simulators are therefore essential. Yet existing simulators fall into two unsatisfactory extremes:
- **Robotics simulators (Gazebo, Webots):** Possess physics engines but rely on flat planes and simple geometric primitives (boxes, cylinders), lacking real-world geographic complexity.
- **Procedural game worlds:** Provide visual fidelity but possess no semantic or geographic correspondence to any real place on Earth.

Geospatial Digital Twins—digital replicas of real-world physical environments generated from Earth observation data—bridge this divide.

### 2.2 Problem Statement

Currently, there exists **no automated, reproducible engineering pipeline** that:
1. Ingests raw sub-meter optical satellite imagery and satellite metadata;
2. Extracts high-precision building footprints, structural heights, and low-altitude micro-hazards (catenary powerlines, tree canopies);
3. Compiles these features into an industrial-grade physics engine (**Unreal Engine 5**) with accurate collision meshes; and
4. Implements and evaluates a closed-loop **Multi-Agent Deep Reinforcement Learning (MADRL)** swarm navigation policy directly inside the reconstructed geospatial digital twin.

### 2.3 Research Questions

1. **Extraction Precision:** How effectively can transformer-based foundation models (Mask2Former + SAM 2) resolve sharp building corners and structural boundaries in dense satellite imagery compared to traditional convolutional U-Nets?
2. **Topographic & Shadow Validation:** Can monocular satellite shadow geometry ($h = L_{\text{shadow}} \cdot \tan \theta_s$) successfully bound elevation estimation errors in the absence of dense airborne LiDAR ground truth?
3. **Micro-Hazard Modeling:** What is the minimum physical representation of catenary transmission lines and vegetative canopies necessary to train collision-free low-altitude UAV flight paths?
4. **MADRL Swarm Convergence:** How does training under 6-DOF kinematic constraints in a topologically faithful digital twin impact MAPPO convergence speed, inter-agent collision rates, and target localization efficiency relative to simplified Euclidean obstacle environments?

---

## 3. Aims & Measurable Objectives

### 3.1 Aim

To design, develop, and evaluate an automated pipeline that reconstructs a high-fidelity 3D geospatial digital twin from optical satellite imagery and trains an autonomous, cooperative UAV swarm using Multi-Agent Deep Reinforcement Learning (MADRL) for safe low-altitude urban navigation.

### 3.2 Measurable Objectives (Mapped to Work Breakdown Structure)

| ID | Project Stage | Objective Description | Target Metric / Acceptance Criterion |
| :---: | :--- | :--- | :--- |
| **O1** | **Stage 1 (Feature Extraction)** | Extract building footprint instances from SpaceNet 2 using Mask2Former + SAM 2 boundary refinement. | **Mask AP $\ge$ 0.58**, Boundary IoU $\ge$ 0.78 on held-out test split. |
| **O2** | **Stage 2 (Topography & Hazards)** | Compute building heights via stereo nDSM and validate via solar shadow trigonometry; map vegetation (SAVI) and catenary powerlines. | Building height MAE $\le 1.8\text{ m}$; catenary sag clearance accuracy $\ge 90\%$. |
| **O3** | **Stage 3 (Mesh Compilation)** | Vector-to-mesh extrusion in Blender and compilation into Unreal Engine 5 with Chaos Physics colliders. | Watertight manifold mesh ($\ge 99.5\%$ valid); zero non-physical collider penetrations; steady 60 FPS in UE5. |
| **O4** | **Stage 4 (Swarm Kinematics)** | Model 6-DOF quadrotor rigid-body dynamics, ray-cast LiDAR emulation, and acoustic rescue signal attenuation. | Physics stability with multi-rotor drag and rotor inertia; real-time LiDAR point-cloud generation ($\ge 10\text{ Hz}$). |
| **O5** | **Stage 4 (MADRL Policy)** | Train a cooperative UAV swarm using MAPPO for acoustic target search while avoiding terrain, buildings, and catenary hazards. | Target reach rate $\ge 92\%$; mutual collision rate $< 3\%$; zero powerline entanglement incidents. |
| **O6** | **Benchmarking & Analysis** | Conduct ablation studies against baseline heuristic planners (A* / RRT*) and traditional semantic U-Nets. | Comprehensive quantitative analysis documenting convergence, sim-to-real fidelity, and failure modes. |

---

## 4. Literature Review & Theoretical Background

### 4.1 Satellite Semantic Feature Extraction & Foundation Models

Traditional remote sensing feature extraction relied on pixel-level Convolutional Neural Networks (CNNs) such as the U-Net (Ronneberger et al., 2015). While effective for rough land-cover classification, convolutional decoders struggle with spatial sharpness: pooling layers discard high-frequency boundary information, producing rounded corners, merged adjacent structures, and jagged raster staircasing.

Recent breakthroughs in Vision Transformers (ViT) have revolutionized geospatial segmentation. **Mask2Former** (Cheng et al., 2022) introduces masked-attention mechanisms that extract localized feature queries, treating semantic, instance, and panoptic segmentation under a unified framework. Furthermore, the advent of visual foundation models such as **Segment Anything Model 2 (SAM 2)** (Ravi et al., 2024) provides promptable, high-frequency boundary refinement capable of sub-pixel zero-shot boundary tracing. Combining Mask2Former instance queries as bounding prompts for SAM 2 produces cadastre-grade building boundaries without manual intervention.

### 4.2 Topographic Extraction, nDSM & Shadow Trigonometry

Height estimation from single optical overhead imagery is fundamentally ill-posed due to projective scale ambiguity. In satellite photogrammetry, building height extraction historically relies on Digital Surface Models (DSM) generated via dense stereo image matching (SGM) or LiDAR point clouds:

$$\text{nDSM} = \text{DSM} - \text{DTM}$$

where $\text{DTM}$ is the Digital Terrain Model representing the bare ground datum.

Where stereo coverage is constrained, **shadow-geometry trigonometry** provides independent, physics-grounded validation. When sun azimuth ($\phi_s$) and sun elevation angle ($\theta_s$) are recorded in the satellite metadata XML (DigitalGlobe/Maxar ephemeris), the geometric height ($h$) of a planar building casting a shadow of length $L_{\text{shadow}}$ onto horizontal terrain is governed by:

$$h = L_{\text{shadow}} \cdot \tan(\theta_s)$$

Accounting for the satellite sensor view zenith angle ($\theta_v$) and relative azimuth ($\phi_s - \phi_v$), monocular shadow mensuration provides rigorous mathematical cross-validation against estimated nDSM values.

```
                  Sun Rays (Elevation θs)
                       \
                        \
                         \
                          +-------------------+   <-- Building Roof (Height h)
                          |                   |
                          |                   |
                          |     Building      |
                          |                   |
  ========================+                   +--------------------------
       Ground Datum       |                   |  Shadow Length Lshadow
                          +-------------------+------------------------->
                                                h = Lshadow * tan(θs)
```

### 4.3 Micro-Hazard Identification & Physical Modeling

Low-altitude UAV flight safety is heavily endangered by micro-hazards invisible on coarse land-use maps:
1. **Tree Canopies:** Soft-body collisions damage rotor blades and trigger propeller stall. Canopies are segmented using the Soil-Adjusted Vegetation Index (SAVI) to suppress desert soil background albedo:
   $$\text{SAVI} = \frac{(1 + L)(\rho_{\text{NIR}} - \rho_{\text{Red}})}{\rho_{\text{NIR}} + \rho_{\text{Red}} + L}, \quad L = 0.5$$
2. **Transmission Lines & Catenary Wires:** High-voltage overhead cables represent the single greatest hazard to low-altitude aerial robotics. Transmission towers detected along road corridors are connected via physical **catenary curve equations**. A cable suspended between two towers at horizontal distance $D$ with sag constant $a = \frac{T_0}{\mu g}$ (where $T_0$ is horizontal cable tension and $\mu$ is linear mass density) follows:
   $$y(x) = a \cdot \left[ \cosh\left(\frac{x}{a}\right) - 1 \right]$$

### 4.4 Industrial-Grade Geospatial Digital Twins (UE5 vs Traditional Simulators)

Traditional robotics platforms (Gazebo, Webots, Bullet Physics) are designed for ground rovers and simple robotic arms. They struggle to render complex geospatial meshes comprising hundreds of thousands of polygons and high-frequency collision hulls.

**Unreal Engine 5 (UE5)** provides a state-of-the-art simulation foundation:
- **Chaos Physics:** High-performance, deterministic rigid-body and soft-body solver capable of handling hundreds of concurrent convex collision hulls.
- **Nanite Virtualized Geometry:** Allows rendering billions of polygons without manual level-of-detail (LOD) degradation.
- **Large World Coordinates (LWC):** 64-bit double-precision floating-point coordinate space enabling metric georeferenced bounding regions without precision jitter.

### 4.5 Multi-Agent Deep Reinforcement Learning (MADRL) for UAV Swarms

Decentralized multi-UAV navigation in continuous state-action spaces is formulated as a **Decentralized Partially Observable Markov Decision Process (Dec-POMDP)**, defined by the tuple $\langle \mathcal{S}, \mathcal{A}, \mathcal{P}, \mathcal{R}, \Omega, \mathcal{O}, \mathcal{N}, \gamma \rangle$.

Standard single-agent reinforcement learning (e.g., standard PPO, DDPG) suffers from environmental non-stationarity when multiple agents learn simultaneously. **Multi-Agent Proximal Policy Optimization (MAPPO)** (Yu et al., 2022) implements the **Centralized Training with Decentralized Execution (CTDE)** paradigm:
- **Centralized Critic:** Has access to the global state $s_t$, evaluating team-wide value estimates during offline training.
- **Decentralized Actor:** Evaluates only the local agent observation $o_i^t$ (onboard LiDAR rays, local telemetry, target acoustic signal gradient) during online execution.

---

## 5. System Scope & Bounded Region Definition

To achieve high scientific rigor while respecting local GPU hardware constraints (GTX 1660 Super / local CUDA environment), the project explicitly bounds its operational geospatial region.

### 5.1 Area of Interest (AOI): SpaceNet 2 Las Vegas Bounded Corridor

The digital twin is constructed from **SpaceNet 2 (AOI 2 — Las Vegas)** commercial satellite imagery:
- **Sensor:** WorldView-3 optical satellite (DigitalGlobe/Maxar).
- **Spectral Resolution:** 3-channel RGB-PanSharpened (450–690 nm).
- **Ground Sampling Distance (GSD):** 0.30 m per pixel nadir resolution.
- **Bounded Geographic Footprint:** A continuous urban corridor encompassing **Sector 7 (Las Vegas)** covering approximately $4.0\text{ km}^2$:
  - Latitude: $36.1265^\circ\text{ N} \text{ to } 36.2599^\circ\text{ N}$
  - Longitude: $-115.2777^\circ\text{ W} \text{ to } -115.1583^\circ\text{ W}$
  - Structural Population: 1,016 validated building structures + 20 major road segments.
- **Rationale for Bounded Subsetting:** Restricting the digital twin to a bounded, high-density residential and commercial corridor allows generating full 3D collision geometry at millimeter precision, running high-frequency ray-cast LiDAR simulations in real time, and maintaining 60 FPS in Unreal Engine 5.

---

## 6. Methodology & Pipeline Architecture

```
====================================================================================================
                                      TERRATWIN SWARM PIPELINE
====================================================================================================

 [SpaceNet 2 Optical Imagery (0.3m)]             [WorldView-3 Ephemeris XML]     [AWS Terrarium DEM]
                   │                                          │                           │
                   ▼                                          ▼                           ▼
 ┌──────────────────────────────────┐        ┌──────────────────────────────────┐ ┌───────────────┐
 │ STAGE 1: HYBRID INSTANCE SEG     │        │ STAGE 2: TOPOGRAPHY & HAZARDS    │ │ Baseline MSL  │
 │  Branch A:                       │        │  Branch B:                       │ │ Ground Datum  │
 │   • Mask2Former Transformer      │        │   • Stereo nDSM Height Estimation│ └───────┬───────┘
 │   • SAM 2 Boundary Refinement    │        │   • Solar Shadow Validation      │         │
 │   • DP Polygon Orthogonalization │        │     h = Lshadow * tan(θs)        │         │
 └─────────────────┬────────────────┘        │  Branch C:                       │         │
                   │                         │   • SAVI Vegetation Isolation    │         │
                   │                         │   • Catenary Wire Physics Cables │         │
                   │                         └────────────────┬─────────────────┘         │
                   └───────────────────┬──────────────────────┘                           │
                                       ▼                                                  │
                      ┌─────────────────────────────────┐                                 │
                      │ STAGE 3: ENVIRONMENT COMPILATION│                                 │
                      │  • Blender Asset Optimization   │                                 │
                      │  • Watertight Manifold Check    │                                 │
                      │  • Unreal Engine 5 (UE5) Import │                                 │
                      │  • Chaos Physics Colliders      │◄────────────────────────────────┘
                      └────────────────┬────────────────┘
                                       ▼
                      ┌─────────────────────────────────┐
                      │ STAGE 4: AUTONOMOUS SWARM SIM   │
                      │  • 6-DOF Quadrotor Dynamics     │
                      │  • Multi-Beam Ray-Cast LiDAR    │
                      │  • Acoustic Rescue Beacon Sim   │
                      │  • MAPPO Decentralized Policy   │
                      └─────────────────────────────────┘
====================================================================================================
```

---

### 6.1 Stage 1 & 2: High-Precision Geospatial & Micro-Hazard Extraction

The extraction architecture operates along three parallel branches:

#### 6.1.1 Branch A: Universal Instance Segmentation (Mask2Former + SAM 2 + DP Orthogonalization)

1. **Instance Query Extraction (Mask2Former):** The WorldView-3 0.3m RGB tiles are ingested by a Swin-Transformer-backed **Mask2Former** instance segmenter fine-tuned on urban footprint topologies. Unlike semantic segmentation models that predict a single heat-map, Mask2Former extracts discrete object queries:
   $$\mathcal{L}_{\text{Mask2Former}} = \lambda_{\text{cls}}\mathcal{L}_{\text{CE}} + \lambda_{\text{bce}}\mathcal{L}_{\text{BCE}} + \lambda_{\text{dice}}\mathcal{L}_{\text{Dice}}$$
2. **Zero-Shot Boundary Refinement (SAM 2):** Bounding boxes from predicted instances initialize prompt queries into **Segment Anything Model 2 (SAM 2)**. SAM 2 processes high-frequency edge gradients to eliminate raster staircasing and snap boundary edges along physical roof gutters.
3. **Douglas-Peucker Orthogonalization:** The refined contours are vectorized via Shapely/GDAL and regularized using a modified Douglas-Peucker algorithm enforcing $90^\circ \pm \epsilon$ orthogonality on urban corners:
   $$\epsilon_{\text{ortho}} = \min_{\theta \in \{0^\circ, 90^\circ, 180^\circ, 270^\circ\}} |\theta_{\text{segment}} - \theta|$$
   This eliminates non-physical jagged vertices while preserving true footprint area.

#### 6.1.2 Branch B: Topography, nDSM & Shadow Trigonometric Validation

1. **Normalized Digital Surface Model (nDSM):** Digital Surface Models derived from stereo pairs are filtered using morphological opening to construct the bare-earth DTM. Building elevation is isolated via:
   $$z_{\text{building}} = \text{DSM}(x, y) - \text{DTM}(x, y)$$
2. **Shadow Trigonometric Cross-Validation:** For every segmented structure, the sun elevation angle $\theta_s$ and azimuth $\phi_s$ are parsed from the tile's metadata XML. The shadow profile is extracted along the anti-solar vector $\vec{v}_{\text{shadow}} = [-\sin \phi_s, -\cos \phi_s]$. The calculated height $h_{\text{shadow}} = L_{\text{shadow}} \cdot \tan \theta_s$ is used to validate and constrain the nDSM model:
   $$h_{\text{final}} = \alpha \cdot h_{\text{nDSM}} + (1 - \alpha) \cdot h_{\text{shadow}}, \quad \alpha \in [0.7, 0.9]$$

#### 6.1.3 Branch C: Micro-Hazard Mapping (NDVI/SAVI Canopies & Catenary Powerlines)

1. **Vegetation Extraction:** In arid/semi-arid urban zones, background soil brightness skews traditional NDVI. The Soil-Adjusted Vegetation Index (SAVI) with soil correction parameter $L = 0.5$ is computed across available multispectral bands. Clusters with $\text{SAVI} > 0.28$ are isolated, extruded as volumetric vegetative obstacle cylinders, and flagged with soft-body aerodynamic turbulence penalties.
2. **Transmission Lines & Catenary Cables:** Power utility corridors along roadways are identified. Towers serve as structural anchors. Cable sag profiles are computed via catenary curves:
   $$z_{\text{cable}}(x) = z_0 + a \left[ \cosh\left(\frac{x - x_{\text{mid}}}{a}\right) - 1 \right]$$
   These cables are compiled as continuous lethal collision cylinders in the flight simulator, directly addressing an urban obstacle that is completely absent from all standard datasets.

---

### 6.2 Stage 3: Environment Compilation & Unreal Engine 5 Physics Sim

#### 6.2.1 Vector-to-Mesh Bridge & Blender Asset Optimization

Raw GIS polygons cannot be imported directly into a real-time game engine without preprocessing:
1. **Automated Blender Pipeline (`bpy` headless):** A Python automation script in Blender ingests the 2.5D GeoJSON footprints, structural heights, and catenary lines.
2. **Triangulation & Watertight Validation:** Roof faces are triangulated using constrained Delaunay triangulation (`earcut`); vertical walls are extruded down to the DEM ground datum. Every mesh is verified manifold (zero non-manifold edges, zero internal intersecting faces).
3. **Decimation & LODs:** Planar walls are simplified to minimize vertex count while preserving collision boundaries.

#### 6.2.2 Unreal Engine 5 Ingestion & Chaos Physics Colliders

1. **Nanite & Landscape:** The AWS Terrarium DEM ground datum is imported as a 16-bit displacement heightmap. The ground surface is textured with high-resolution satellite imagery.
2. **Chaos Physics Convex Decomposition:** Extruded buildings are converted into static rigid bodies equipped with **Chaos Physics Convex Hull Colliders**.
3. **Lethal Wire Volumes:** Catenary cables are instantiated as thin, non-deformable capsule collision volumes capable of triggering immediate UAV rotor destruction upon intersection.

---

### 6.3 Stage 4: Autonomous UAV Swarm Engine (MADRL Framework)

```
====================================================================================================
                        MADRL CENTRALIZED TRAINING & DECENTRALIZED EXECUTION
====================================================================================================

                                       [Global State St]
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │    CENTRALIZED CRITIC V(St)     │ (Offline Training Only)
                             │     Evaluates Swarm Value       │
                             └────────────────┬────────────────┘
                                              ▲
                           TD Error / Advantage Estimation
                                              │
               ┌──────────────────────────────┼──────────────────────────────┐
               │                              │                              │
               ▼                              ▼                              ▼
     ┌───────────────────┐          ┌───────────────────┐          ┌───────────────────┐
     │  ACTOR POLICY π1  │          │  ACTOR POLICY π2  │          │  ACTOR POLICY πN  │
     │   (UAV Agent 1)   │          │   (UAV Agent 2)   │          │   (UAV Agent N)   │
     └─────────┬─────────┘          └─────────┬─────────┘          └─────────┬─────────┘
               │                              │                              │
    Local Obs  │ Action a1         Local Obs  │ Action a2         Local Obs  │ Action aN
       o1      ▼                      o2      ▼                      oN      ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │                 UNREAL ENGINE 5 GEOSPATIAL TWIN (CHAOS PHYSICS 6-DOF)                  │
  │   • 3D Building Colliders   • 6-DOF Quadrotor Dynamics   • Ray-Cast LiDAR Sweeps       │
  │   • Catenary Wire Hazards   • Inter-Agent Telemetry      • Acoustic Rescue Beacon      │
  └────────────────────────────────────────────────────────────────────────────────────────┘
====================================================================================================
```

#### 6.3.1 6-DOF Quadrotor Dynamics & Flight Envelope

Each UAV in the swarm is modeled as a 6-DOF rigid body under aerodynamic forces:
$$\mathbf{\dot{p}} = \mathbf{v}$$
$$m \mathbf{\dot{v}} = m \mathbf{g} + \mathbf{R} \mathbf{F}_{\text{thrust}} - \mathbf{D} \mathbf{v}$$
$$\mathbf{\dot{R}} = \mathbf{R} [\boldsymbol{\omega}]_{\times}$$
$$\mathbf{I} \boldsymbol{\dot{\omega}} = \boldsymbol{\tau} - \boldsymbol{\omega} \times (\mathbf{I} \boldsymbol{\omega})$$

where:
- $\mathbf{p} = [x, y, z]^T$ is the world position;
- $\mathbf{v}$ is the linear velocity vector;
- $\mathbf{R} \in SO(3)$ is the rotation matrix from body to world frame;
- $m$ is the quadrotor mass ($1.25\text{ kg}$);
- $\mathbf{F}_{\text{thrust}} = [0, 0, \sum_{i=1}^4 T_i]^T$ is the collective rotor thrust;
- $\mathbf{D} = \text{diag}(d_x, d_y, d_z)$ is the translational aerodynamic drag tensor;
- $\mathbf{I}$ is the quadrotor moment of inertia tensor;
- $\boldsymbol{\omega} = [p, q, r]^T$ is the angular velocity in the body frame;
- $\boldsymbol{\tau}$ is the control torque vector generated by differential rotor speeds.

#### 6.3.2 Virtual Sensor Emulation (LiDAR & Swarm Telemetry)

1. **Ray-Cast LiDAR:** Each agent projects $K = 32$ omnidirectional ray-casts (horizontal span $360^\circ$, vertical pitch $\pm 25^\circ$) up to a maximum range of $d_{\text{max}} = 30.0\text{ m}$. The normalized distance reading is:
   $$s_k = \frac{\min(d_k, d_{\text{max}})}{d_{\text{max}}} \in [0.0, 1.0]$$
2. **Swarm Telemetry:** Agents within an ad-hoc communication radius $R_{\text{comm}} = 50.0\text{ m}$ broadcast relative state vectors $\Delta \mathbf{p}_{ij} = \mathbf{p}_j - \mathbf{p}_i$ and relative velocities $\Delta \mathbf{v}_{ij} = \mathbf{v}_j - \mathbf{v}_i$.
3. **Acoustic Rescue Beacon:** An omnidirectional acoustic emergency beacon is located inside a damaged structure. The acoustic intensity received by agent $i$ follows an inverse-square attenuation law with environmental absorption coefficient $\mu_{\text{air}}$:
   $$\Phi_i(\mathbf{p}_i) = \frac{\Phi_0}{\|\mathbf{p}_i - \mathbf{p}_{\text{target}}\|^2} \cdot e^{-\mu_{\text{air}} \|\mathbf{p}_i - \mathbf{p}_{\text{target}}\|}$$

#### 6.3.3 MAPPO Policy Architecture & Formulation

The swarm policy is trained via **Multi-Agent Proximal Policy Optimization (MAPPO)** using a shared policy network with decentralized observations:

1. **Local Observation Space ($o_i^t \in \mathbb{R}^{58}$):**
   - Agent linear velocity: $\mathbf{v}_i \in \mathbb{R}^3$
   - Agent orientation (quaternion): $\mathbf{q}_i \in \mathbb{R}^4$
   - Agent angular velocity: $\boldsymbol{\omega}_i \in \mathbb{R}^3$
   - 32-beam normalized LiDAR depth: $\mathbf{s}_i \in \mathbb{R}^{32}$
   - Acoustic signal strength and temporal gradient: $[\Phi_i, \Delta \Phi_i] \in \mathbb{R}^2$
   - K-nearest swarm neighbors relative offsets: $[\Delta \mathbf{p}_{i,1}, \dots, \Delta \mathbf{p}_{i,4}] \in \mathbb{R}^{12}$
   - Minimum distance to nearest detected obstacle: $d_{\text{obs}} \in \mathbb{R}^1$
   - Remaining mission time fraction: $\tau \in \mathbb{R}^1$

2. **Continuous Action Space ($a_i^t \in \mathbb{R}^4$):**
   - Normalized collective thrust command: $u_T \in [-1.0, 1.0]$
   - Body roll rate command: $\omega_{x,\text{cmd}} \in [-1.0, 1.0]$
   - Body pitch rate command: $\omega_{y,\text{cmd}} \in [-1.0, 1.0]$
   - Body yaw rate command: $\omega_{z,\text{cmd}} \in [-1.0, 1.0]$

3. **PPO Clipped Objective:**
   $$\mathcal{L}(\theta) = \hat{\mathbb{E}}_t \left[ \min\left( r_t(\theta)\hat{A}_t, \, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon)\hat{A}_t \right) \right]$$
   where $r_t(\theta) = \frac{\pi_\theta(a_t|o_t)}{\pi_{\theta_{\text{old}}}(a_t|o_t)}$ and $\hat{A}_t$ is the Generalized Advantage Estimator (GAE) computed by the centralized critic $V_\phi(s_t)$.

#### 6.3.4 Multi-Objective Reward Function Formulation

The global reward $R_i^t$ balances target exploration, team cohesion, and collision avoidance:

$$R_i^t = R_{\text{beacon}} + R_{\text{cohesion}} + R_{\text{col}} + R_{\text{hazard}} + R_{\text{energy}} + R_{\text{step}}$$

| Component | Mathematical Definition | Operational Meaning |
| :--- | :--- | :--- |
| **Beacon Progress** | $R_{\text{beacon}} = \lambda_1 (\Phi_i^t - \Phi_i^{t-1}) + \mathbf{1}_{\{\lVert\mathbf{p}_i - \mathbf{p}_{\text{target}}\rVert < r_{\text{found}}\}} \cdot R_{\text{success}}$ | Rewards climbing acoustic intensity; massive bonus ($+500$) upon target localization. |
| **Swarm Cohesion** | $R_{\text{cohesion}} = -\lambda_2 \sum_{j \neq i} \max(0, \lVert\mathbf{p}_i - \mathbf{p}_j\rVert - d_{\text{max\_sep}})^2$ | Penalizes agents straying beyond communication radius. |
| **Inter-Agent Repulsion** | $R_{\text{repulse}} = -\lambda_3 \sum_{j \neq i} \max(0, d_{\text{safe}} - \lVert\mathbf{p}_i - \mathbf{p}_j\rVert)^2$ | Strong potential repulsion preventing mid-air swarm collisions. |
| **Building Obstacle Collision**| $R_{\text{col}} = -200 \cdot \mathbf{1}_{\text{Collision(Building)}} - \lambda_4 \max(0, d_{\text{clearance}} - d_{\text{obs}})^2$ | Severe termination penalty for structural impacts; soft boundary buffer. |
| **Catenary Wire Hazard** | $R_{\text{hazard}} = -500 \cdot \mathbf{1}_{\text{Collision(Wire)}} - 25 \cdot \max(0, d_{\text{wire\_crit}} - d_{\text{wire}})$ | Fatal penalty for powerline contact; induces strong upward/downward clearance maneuver. |
| **Kinematic Effort** | $R_{\text{energy}} = -\lambda_5 \lVert\mathbf{u}_t\rVert^2$ | Penalizes aggressive, jittery actuator usage to conserve battery in real flight. |
| **Step Penalty** | $R_{\text{step}} = -0.1$ | Constant negative penalty encouraging time-optimal mission trajectories. |

---

## 7. Data, Computational Infrastructure & Software Stack

### 7.1 Remote Sensing & GIS Data Assets

- **Satellite Source:** SpaceNet 2 (AOI 2 — Las Vegas), 0.3 m WorldView-3 optical RGB imagery.
- **Topographic Base:** AWS Open Data Terrarium Digital Elevation Models (10 m–30 m resolution).
- **Metadata Sources:** Ephemeris XML sidecars providing solar zenith/azimuth angles ($\theta_s, \phi_s$) and off-nadir angles.
- **Format Architecture:** Cloud-Optimized GeoTIFFs (COG), GeoJSON feature collections (EPSG:4326 / EPSG:32611 UTM Zone 11N).

### 7.2 Hardware Compute Environment

- **Local Workstation:** NVIDIA GeForce GTX 1660 Super (6 GB VRAM), 6-core Intel Core i5 / AMD Ryzen, 32 GB RAM, 2 TB NVMe SSD.
- **Compute Optimization Strategy:**
  - Mask2Former / SAM 2 inference utilizing mixed precision (`fp16` / `bf16`).
  - Headless batch processing in Blender.
  - Sub-region vectorized tiling: The $4.0\text{ km}^2$ study corridor is divided into $512\text{ m} \times 512\text{ m}$ operational cells to preserve 60 FPS in Unreal Engine 5.

### 7.3 Software Ecosystem & Libraries

```
Layer                   Technology / Framework                          Role in Project
---------------------------------------------------------------------------------------------------------
Foundation Vision       Mask2Former (HuggingFace / PyTorch 2.5)         Universal Transformer instance segmentation
Edge Refinement         SAM 2 (Meta AI Research)                        Zero-shot promptable boundary snapping
Geospatial Math         GDAL, Rasterio, GeoPandas, Shapely              CRS transforms, DP regularization, nDSM
Micro-Hazard Engine     NumPy, SciPy                                    SAVI algebra, catenary curve fitting
3D Pipeline             Blender 4.2 LTS (`bpy` API)                     Automated triangulation, manifold repair
Physics Simulator       Unreal Engine 5.4 (Chaos Physics)               High-fidelity 6-DOF simulation & colliders
MADRL Engine            CleanRL / PettingZoo / PyTorch                  MAPPO swarm actor-critic networks
```

---

## 8. Comprehensive Evaluation Plan

### 8.1 Geospatial Extraction Benchmarks

Evaluated against held-out ground truth vectors on the 146 SpaceNet test tiles:
- **Instance Metrics:** Standard COCO Average Precision ($\text{AP}$, $\text{AP}_{50}$, $\text{AP}_{75}$).
- **Boundary Precision:** Boundary IoU ($\text{BIoU}$) quantifying corner fidelity and edge sharpness:
  $$\text{BIoU} = \frac{|(A_d \cap A) \cap (B_d \cap B)|}{|(A_d \cap A) \cup (B_d \cap B)|}$$
- **Height Accuracy:** Mean Absolute Error ($\text{MAE}$) and Root Mean Square Error ($\text{RMSE}$) between estimated heights and shadow trigonometric reference values:
  $$\text{RMSE}_h = \sqrt{\frac{1}{N} \sum_{i=1}^N (h_i^{\text{pred}} - h_i^{\text{shadow}})^2}$$

### 8.2 Physics Simulation & Collision Integrity

- **Mesh Manifoldness Rate:** Percentage of generated building meshes with zero non-manifold edges.
- **Simulation Framerate:** Continuous monitoring of UE5 frame rendering time ($\le 16.6\text{ ms}$ for 60 FPS) during active 8-UAV swarm flight.
- **Collision Boundary Precision:** Verification that physical Chaos colliders match visual meshes within a tolerance of $< 0.10\text{ m}$.

### 8.3 MADRL Swarm Navigation & Mission Metrics

Swarm performance will be evaluated across 500 test episodes with randomized initial spawns and target locations:
- **Mission Success Rate (MSR):** Percentage of episodes where at least one UAV enters the target radius ($r_{\text{found}} = 3.0\text{ m}$) within the time limit ($T_{\text{max}} = 120\text{ s}$).
- **Collision Frequency:**
  - Inter-agent collision rate: Percentage of episodes terminated by mid-air collision.
  - Obstacle impact rate: Total building/ground collisions per mission.
  - Wire entanglement rate: Total catenary cable contacts.
- **Swarm Energy Expenditure:** Total kinetic control effort $\int_0^T \|\mathbf{u}_t\|^2 dt$.
- **Baseline Comparative Study:** Benchmark MAPPO against:
  1. Centralized 3D A* Search (idealized benchmark with full global map knowledge).
  2. Decentralized RRT* with collision cones (classical geometric motion planning).
  3. Single-Agent Independent PPO (IPPO, treating other swarm members as dynamic environmental noise).

---

## 9. Risk Assessment & Mitigation Matrix

| Risk Identified | Severity | Likelihood | Mitigation Strategy |
| :--- | :---: | :---: | :--- |
| **VRAM Bottlenecks during Mask2Former / SAM 2 Inference** | High | Medium | Execute inference tile-by-tile using gradient-free `torch.inference_mode()` and mixed precision (`fp16`); offload intermediate tensors to system RAM. |
| **Shadows Occluded by Adjacent Tall Structures** | Medium | High | Implement quality-check filtering: only validate shadow lengths for structures where the solar ray azimuth is unblocked by neighboring buildings. |
| **Non-Manifold Geometry Crashing UE5 Physics Engine** | High | Low | Automated Blender pre-flight script runs `mesh.clean_up` and manifold testing, automatically welding vertices $< 2\text{ mm}$ apart before export. |
| **MADRL Exploration Collapse in Complex Urban Canyons** | High | Medium | Implement Curriculum Learning: spawn agents initially near the target in open space, progressively increasing obstacle density and travel distance as policy converges. |
| **Chaos Physics Jitter with Thin Wire Colliders** | Medium | Medium | Model catenary cables as compound collision capsules with expanded conservative collision radiuses ($r = 0.40\text{ m}$) rather than sub-millimeter physics lines. |

---

## 10. Work Plan, Milestone Schedule & Gantt Alignment

### 10.1 Academic Phases & Milestones

The project is structured across four continuous academic phases:

```
Phase 1: Geospatial Extraction Engine (Months 1–2)
  ├── Mask2Former fine-tuning on SpaceNet 2
  ├── SAM 2 boundary refinement & DP orthogonalization
  └── nDSM height estimation & shadow trigonometric cross-validation
Phase 2: Micro-Hazards & Geometry Compilation (Months 3–4)
  ├── SAVI tree canopy segmentation
  ├── Catenary powerline mathematical modeling
  └── Automated Blender asset pipeline & mesh manifold verification
Phase 3: Unreal Engine 5 Environment Setup (Months 5–6)
  ├── DEM terrain import & satellite texture projection
  ├── Chaos Physics convex collider generation
  └── 6-DOF quadrotor flight dynamics & ray-cast LiDAR emulation
Phase 4: MADRL Swarm Policy & Benchmarking (Months 7–8)
  ├── MAPPO policy training (CTDE framework)
  ├── Multi-objective reward tuning & acoustic beacon localization
  └── Quantitative benchmarking against A* and classical planners
Final Phase: Dissertation & Defense (Months 9–10)
  ├── Comprehensive failure mode analysis
  ├── Dissertation manuscript submission
  └── Formal thesis oral defense
```

### 10.2 Division of Responsibilities & Team Work Breakdown

To ensure rigorous execution and balanced academic contribution across the thesis lifecycle, engineering and research responsibilities are structured co-equally between the co-investigators:

| Research Domain / Engineering Module | Primary Lead | Supporting Co-Investigator | Key Responsibilities & Deliverables |
| :--- | :--- | :--- | :--- |
| **Stage 1: Satellite Extraction & Instance Segmentation** | Haider Taqveen | Mashaf Majeed | Fine-tuning Mask2Former on SpaceNet 2; SAM 2 zero-shot edge refinement; Douglas-Peucker orthogonalization pipeline; extraction metric validation ($\text{IoU}$, $\text{BIoU}$, $\text{AP}$). |
| **Stage 2: Topography, nDSM & Micro-Hazard Modeling** | Mashaf Majeed | Haider Taqveen | Stereoscopic DSM ground filtering to compute nDSM; solar shadow trigonometric verification ($h = L_{\text{shadow}} \tan \theta_s$); SAVI vegetation canopy masking ($L=0.5$); catenary powerline mathematical modeling ($y = a \cdot [\cosh(x/a) - 1]$). |
| **Stage 3: 3D Mesh Manifolding & Physics Simulator** | Haider Taqveen | Mashaf Majeed | Blender Python (`bpy`) automated asset generation; watertight manifold repair ($\le 2\text{ mm}$ vertex welding); Unreal Engine 5 Chaos Physics convex hull and capsule collider integration; framerate optimization ($\ge 60\text{ FPS}$). |
| **Stage 4: Multi-Agent DRL Swarm Engine** | Mashaf Majeed | Haider Taqveen | MAPPO multi-agent reinforcement learning architecture (CTDE); 6-DOF quadrotor kinematic constraints; 32-beam LiDAR emulation; multi-objective reward formulation (acoustic rescue beacon, collision & wire entanglement penalties). |
| **Comparative Benchmarking & Thesis Manuscript** | Haider Taqveen & Mashaf Majeed | Dr. Munawar Ali Shah (Supervisor) | Comparative benchmarking against centralized 3D A* and decentralized RRT*; trajectory safety analysis; comprehensive thesis dissertation writeup and oral defense preparation. |

---

## 11. Expected Academic Deliverables & Contributions

### 11.1 Tangible Deliverables

1. **Fully Automated Geospatial Reconstruction Pipeline (`src/data_prep/`, `src/geometry/`):** Python toolchain converting raw optical satellite tiles into cadastre-grade 3D meshes with shadow-validated heights.
2. **Compiled Unreal Engine 5 Digital Twin:** A high-fidelity, georeferenced simulation environment of Las Vegas Sector 7 featuring Chaos Physics colliders, micro-hazards, and terrain topography.
3. **MADRL Swarm Policy Repository (`src/models/marl_swarm/`):** Clean, modular PyTorch implementation of MAPPO governing 6-DOF quadrotors equipped with virtual LiDAR and acoustic localization heads.
4. **Interactive Exploratory Notebooks (`notebooks/`):** Reproducible validation notebooks demonstrating extraction metrics, height error bounds, and swarm trajectory visualizations.
5. **Final BS Thesis Manuscript & Oral Defense Presentation.**

### 11.2 Key Scientific Contributions

- **Bridging GIS and Real-Time Autonomous Swarm Simulation:** Demonstrates that foundation models (Mask2Former + SAM 2) combined with classical photogrammetric shadow trigonometry can generate simulation-ready physics environments without manual 3D modeling.
- **Empirical Demonstration of Micro-Hazard Impact on Swarms:** Proves the necessity of explicit physical modeling for catenary wires and vegetation in urban aerial swarm simulation.
- **Validated MADRL Swarm Policy:** Establishes benchmark convergence rates and trajectory safety metrics for decentralized swarms operating under 6-DOF constraints in photogrammetrically grounded urban digital twins.

---

## 12. Ethical, Dual-Use & Environmental Considerations

- **Civic & Humanitarian Mission Alignment:** The primary operational focus of this research is post-disaster search and rescue, emergency logistics, and civilian infrastructure inspection. The thesis strictly rejects developing targeting algorithms, kinetic tracking, or offensive weaponization systems.
- **Privacy Compliance:** All imagery used originates from publicly accessible SpaceNet commercial datasets released under permissive research licenses. Spatial resolution (0.3m GSD) is sufficient to identify structures and vehicles, but is incapable of resolving human faces or private personal information.
- **Carbon Footprint & Energy Conservation:** By conducting training inside a bounded geospatial region ($4.0\text{ km}^2$) and utilizing lightweight, sample-efficient algorithms (MAPPO), computational requirements are minimized, enabling full reproduction on local consumer hardware without wasteful data-center energy expenditure.

---

## 13. References

1. Cheng, B., Misra, I., Schwing, A. G., Kirillov, A., & Girdhar, R. (2022). Masked-attention Mask Transformer for Universal Image Segmentation. *IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, 1290–1299.
2. Ravi, N., Gabeur, V., Hu, Y. T., Hu, R., Ryali, C., Ma, T., ... & Feichtenhofer, C. (2024). SAM 2: Segment Anything in Images and Videos. *arXiv preprint arXiv:2408.00714*.
3. Yu, C., Velu, A., Vinitsky, E., Gao, J., Wang, Y., Bayen, A., & Wu, Y. (2022). The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games. *Advances in Neural Information Processing Systems (NeurIPS)*, 35, 24611–24624.
4. Ronneberger, O., Fischer, P., & Brox, T. (2015). U-Net: Convolutional Networks for Biomedical Image Segmentation. *International Conference on Medical Image Computing and Computer-Assisted Intervention (MICCAI)*, 234–241.
5. Van Etten, A., Lindenbaum, D., & Bacastow, T. M. (2018). SpaceNet: A Remote Sensing Dataset and Challenge Series. *arXiv preprint arXiv:1807.01401*.
6. Hu, J., & Razdan, A. (2007). 3D Building Reconstruction Based on Photogrammetry and Shadow Analysis. *ISPRS Journal of Photogrammetry and Remote Sensing*, 62(5), 345–358.
7. Hu, X., & Hu, J. (2020). Soil-Adjusted Vegetation Index (SAVI) for Urban Microclimate and Vegetation Density Mapping. *Remote Sensing of Environment*, 240, 111690.
8. Epic Games. (2024). *Unreal Engine 5.4 Documentation: Chaos Physics Simulation and Large World Coordinates*. Epic Games Developer Portal.
9. Douglas, D. H., & Peucker, T. K. (1973). Algorithms for the Reduction of the Number of Points Required to Represent a Digitized Line or its Caricature. *Cartographica: The International Journal for Geographic Information and Geovisualization*, 10(2), 112–122.
10. Beard, R. W., & McLain, T. W. (2012). *Small Unmanned Aircraft: Theory and Practice*. Princeton University Press.

---

## 14. Appendices

### Appendix A: Derivation of Shadow Trigonometry Equation

Consider an optical satellite sensor observing a vertical building wall of height $h$. Let $\theta_s$ denote the solar elevation angle (altitude above the local horizon), such that the angle between the solar ray vector and the vertical surface normal is $\frac{\pi}{2} - \theta_s$.

Assuming the ground datum is locally horizontal:
$$\tan(\theta_s) = \frac{\text{Opposite}}{\text{Adjacent}} = \frac{h}{L_{\text{shadow}}}$$

Rearranging directly yields:
$$h = L_{\text{shadow}} \cdot \tan(\theta_s)$$

When accounting for sensor viewing geometry (sensor zenith $\theta_v$ and relative azimuth $\Delta \phi = \phi_s - \phi_v$), the apparent shadow length $L_{\text{app}}$ in the image plane is corrected via projective perspective geometry:
$$L_{\text{true}} = \frac{L_{\text{app}}}{\cos(\theta_v) \left(1 + \tan(\theta_v) \cot(\theta_s) \cos(\Delta \phi)\right)}$$

### Appendix B: Catenary Sag Mathematical Formulation

A flexible wire suspended under uniform gravity satisfies the differential equation:
$$\frac{d^2 y}{dx^2} = \frac{1}{a} \sqrt{1 + \left(\frac{dy}{dx}\right)^2}, \quad a = \frac{T_0}{\mu g}$$

Letting $u = \frac{dy}{dx}$, separation of variables yields:
$$\int \frac{du}{\sqrt{1 + u^2}} = \int \frac{dx}{a} \implies \operatorname{arsinh}(u) = \frac{x}{a} + C_1$$

Setting the origin at the lowest sag point where $\left.\frac{dy}{dx}\right|_{x=0} = 0$, we have $C_1 = 0$. Integrating once more:
$$y(x) = a \int \sinh\left(\frac{x}{a}\right) dx = a \cosh\left(\frac{x}{a}\right) + C_2$$

Setting $y(0) = 0 \implies C_2 = -a$, giving the standard catenary curve equation:
$$y(x) = a \left[ \cosh\left(\frac{x}{a}\right) - 1 \right]$$

### Appendix C: Glossary of Technical Abbreviations

| Abbreviation | Expanded Technical Terminology |
| :--- | :--- |
| **AOI** | Area of Interest |
| **CTDE** | Centralized Training with Decentralized Execution |
| **Dec-POMDP** | Decentralized Partially Observable Markov Decision Process |
| **DP** | Douglas-Peucker (Polygon Regularization Algorithm) |
| **DSM** | Digital Surface Model |
| **DTM** | Digital Terrain Model |
| **GSD** | Ground Sampling Distance |
| **LiDAR** | Light Detection and Ranging |
| **LWC** | Large World Coordinates (64-bit Floating-Point World Origin) |
| **MADRL** | Multi-Agent Deep Reinforcement Learning |
| **MAPPO** | Multi-Agent Proximal Policy Optimization |
| **nDSM** | Normalized Digital Surface Model ($\text{DSM} - \text{DTM}$) |
| **NDVI** | Normalized Difference Vegetation Index |
| **PPO** | Proximal Policy Optimization |
| **SAM 2** | Segment Anything Model 2 (Meta AI Foundation Model) |
| **SAVI** | Soil-Adjusted Vegetation Index |
| **UE5** | Unreal Engine 5 |
| **URP** | Universal Render Pipeline (Legacy Reference) |
